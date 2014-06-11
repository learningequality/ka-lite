# Copyright (C) 2010, 2011 Sebastian Thiel (byronimo@gmail.com) and contributors
#
# This module is part of async and is released under
# the New BSD License: http://www.opensource.org/licenses/bsd-license.php
"""Implementation of a thread-pool working with channels"""
from thread import (
        WorkerThread, 
        StopProcessing,
        )
from threading import Lock

from util import (
        AsyncQueue,
        DummyLock
    )

from Queue import (
    Queue, 
    Empty
    )

from graph import Graph 
from channel import (
        mkchannel,
        ChannelWriter, 
        Channel,
        SerialChannel,
        CallbackChannelReader
    )

import sys
import weakref
from time import sleep


__all__ = ('PoolReader', 'Pool', 'ThreadPool')


class PoolReader(CallbackChannelReader):
    """A reader designed to read from channels which take part in pools
    It acts like a handle to the underlying task in the pool."""
    __slots__ = ('_task_ref', '_pool_ref')
    
    def __init__(self, channel, task, pool):
        CallbackChannelReader.__init__(self, channel)
        self._task_ref = weakref.ref(task)
        self._pool_ref = weakref.ref(pool)
        
    def __del__(self):
        """Assures that our task will be deleted if we were the last reader"""
        task = self._task_ref()
        if task is None:
            return
        
        pool = self._pool_ref()
        if pool is None:
            return
        
        # if this is the last reader to the wc we just handled, there 
        # is no way anyone will ever read from the task again. If so, 
        # delete the task in question, it will take care of itself and orphans
        # it might leave
        # 1 is ourselves, + 1 for the call + 1, and 3 magical ones which 
        # I can't explain, but appears to be normal in the destructor
        # On the caller side, getrefcount returns 2, as expected
        # When just calling remove_task, 
        # it has no way of knowing that the write channel is about to diminsh.
        # which is why we pass the info as a private kwarg  - not nice, but 
        # okay for now
        if sys.getrefcount(self) < 6:
            pool.remove_task(task, _from_destructor_ = True)
        # END handle refcount based removal of task

    #{ Internal
    def _read(self, count=0, block=True, timeout=None):
        return CallbackChannelReader.read(self, count, block, timeout)
        
        
    def pool_ref(self):
        """:return: reference to the pool we belong to"""
        return self._pool_ref
        
    def task_ref(self):
        """:return: reference to the task producing our items"""
        return self._task_ref
    
    #} END internal

    #{ Interface
    
    def task(self):
        """:return: task we read from
        :raise ValueError: If the instance is not attached to at task"""
        task = self._task_ref()
        if task is None:
            raise ValueError("PoolReader is not associated with at task anymore")
        return task
        
    def pool(self):
        """:return: pool our task belongs to
        :raise ValueError: if the instance does not belong to a pool"""
        pool = self._pool_ref()
        if pool is None:
            raise ValueError("PoolReader is not associated with a pool anymore")
        return pool
        
    
    #} END interface 
    
    def read(self, count=0, block=True, timeout=None):
        """Read an item that was processed by one of our threads
        :note: Triggers task dependency handling needed to provide the necessary input"""
        # NOTE: we always queue the operation that would give us count items
        # as tracking the scheduled items or testing the channels size
        # is in herently unsafe depending on the design of the task network
        # If we put on tasks onto the queue for every request, we are sure
        # to always produce enough items, even if the task.min_count actually
        # provided enough - its better to have some possibly empty task runs 
        # than having and empty queue that blocks.
        
        # if the user tries to use us to read from a done task, we will never 
        # compute as all produced items are already in the channel
        task = self._task_ref()
        if task is None:
            return list()
        # END abort if task was deleted
            
        skip_compute = task.is_done() or task.error()
        
        ########## prepare ##############################
        if not skip_compute:
            self._pool_ref()._prepare_channel_read(task, count)
        # END prepare pool scheduling
        
        
        ####### read data ########
        ##########################
        # read actual items, tasks were setup to put their output into our channel ( as well )
        items = CallbackChannelReader.read(self, count, block, timeout)
        ##########################
        
        
        return items
        
    
    
class Pool(object):
    """A thread pool maintains a set of one or more worker threads, but supports 
    a fully serial mode in which case the amount of threads is zero.
    
    Work is distributed via Channels, which form a dependency graph. The evaluation
    is lazy, as work will only be done once an output is requested.
    
    The thread pools inherent issue is the global interpreter lock that it will hit, 
    which gets worse considering a few c extensions specifically lock their part
    globally as well. The only way this will improve is if custom c extensions
    are written which do some bulk work, but release the GIL once they have acquired
    their resources.
    
    Due to the nature of having multiple objects in git, its easy to distribute 
    that work cleanly among threads.
    
    :note: the current implementation returns channels which are meant to be 
        used only from the main thread, hence you cannot consume their results 
        from multiple threads unless you use a task for it."""
    __slots__ = (   '_tasks',               # a graph of tasks
                    '_num_workers',         # list of workers
                    '_queue',               # master queue for tasks
                    '_taskorder_cache',     # map task id -> ordered dependent tasks
                    '_taskgraph_lock',      # lock for accessing the task graph
                )
    
    # CONFIGURATION
    # The type of worker to create - its expected to provide the Thread interface, 
    # taking the taskqueue as only init argument
    # as well as a method called stop_and_join() to terminate it
    WorkerCls = None
    
    # The type of lock to use to protect critical sections, providing the 
    # threading.Lock interface
    LockCls = None
    
    # the type of the task queue to use - it must provide the Queue interface
    TaskQueueCls = None
    
    
    def __init__(self, size=0):
        self._tasks = Graph()
        self._num_workers = 0
        self._queue = self.TaskQueueCls()
        self._taskgraph_lock = self.LockCls()
        self._taskorder_cache = dict()
        self.set_size(size)
        
    def __del__(self):
        self.set_size(0)
    
    #{ Internal
        
    def _prepare_channel_read(self, task, count):
        """Process the tasks which depend on the given one to be sure the input 
        channels are filled with data once we process the actual task
        
        Tasks have two important states: either they are done, or they are done 
        and have an error, so they are likely not to have finished all their work.
        
        Either way, we will put them onto a list of tasks to delete them, providng 
        information about the failed ones.
        
        Tasks which are not done will be put onto the queue for processing, which 
        is fine as we walked them depth-first."""
        # for the walk, we must make sure the ordering does not change. Even 
        # when accessing the cache, as it is related to graph changes
        self._taskgraph_lock.acquire()
        try:
            try:
                dfirst_tasks = self._taskorder_cache[id(task)]
            except KeyError:
                # have to retrieve the list from the graph
                dfirst_tasks = self._tasks.input_inclusive_dfirst_reversed(task)
                self._taskorder_cache[id(task)] = dfirst_tasks
            # END handle cached order retrieval
        finally:
            self._taskgraph_lock.release()
        # END handle locking
        
        # check the min count on all involved tasks, and be sure that we don't 
        # have any task which produces less than the maximum min-count of all tasks
        # The actual_count is used when chunking tasks up for the queue, whereas 
        # the count is usued to determine whether we still have enough output
        # on the queue, checking qsize ( ->revise )
        # ABTRACT: If T depends on T-1, and the client wants 1 item, T produces
        # at least 10, T-1 goes with 1, then T will block after 1 item, which 
        # is read by the client. On the next read of 1 item, we would find T's 
        # queue empty and put in another 10, which could put another thread into 
        # blocking state. T-1 produces one more item, which is consumed right away
        # by the two threads running T. Although this works in the end, it leaves
        # many threads blocking and waiting for input, which is not desired.
        # Setting the min-count to the max of the mincount of all tasks assures
        # we have enough items for all.
        # Addition: in serial mode, we would enter a deadlock if one task would
        # ever wait for items !
        actual_count = count
        min_counts = (((t.min_count is not None and t.min_count) or count) for t in dfirst_tasks)
        min_count = reduce(lambda m1, m2: max(m1, m2), min_counts)
        if 0 < count < min_count:
            actual_count = min_count
        # END set actual count
        
        # the list includes our tasks - the first one to evaluate first, the 
        # requested one last
        for task in dfirst_tasks: 
            # if task.error() or task.is_done():
                # in theory, the should never be consumed task in the pool, right ?
                # They delete themselves once they are done. But as we run asynchronously, 
                # It can be that someone reads, while a task realizes its done, and 
                # we get here to prepare the read although it already is done.
                # Its not a problem though, the task wiill not do anything.
                # Hence we don't waste our time with checking for it
                # raise AssertionError("Shouldn't have consumed tasks on the pool, they delete themeselves, what happend ?")
            # END skip processing
            
            # but use the actual count to produce the output, we may produce 
            # more than requested
            numchunks = 1
            chunksize = actual_count
            remainder = 0
            
            # we need the count set for this - can't chunk up unlimited items
            # In serial mode we could do this by checking for empty input channels, 
            # but in dispatch mode its impossible ( == not easily possible )
            # Only try it if we have enough demand
            if task.max_chunksize and actual_count > task.max_chunksize:
                numchunks = actual_count / task.max_chunksize
                chunksize = task.max_chunksize
                remainder = actual_count - (numchunks * chunksize)
            # END handle chunking
            
            # the following loops are kind of unrolled - code duplication
            # should make things execute faster. Putting the if statements 
            # into the loop would be less code, but ... slower
            if self._num_workers:
                # respect the chunk size, and split the task up if we want 
                # to process too much. This can be defined per task
                qput = self._queue.put
                if numchunks > 1:
                    for i in xrange(numchunks):
                        qput((task.process, chunksize))
                    # END for each chunk to put
                else:
                    qput((task.process, chunksize))
                # END try efficient looping
                
                if remainder:
                    qput((task.process, remainder))
                # END handle chunksize
            else:
                # no workers, so we have to do the work ourselves
                if numchunks > 1:
                    for i in xrange(numchunks):
                        task.process(chunksize)
                    # END for each chunk to put
                else:
                    task.process(chunksize)
                # END try efficient looping
                
                if remainder:
                    task.process(remainder)
                # END handle chunksize
            # END handle serial mode
        # END for each task to process
        
        
    def _remove_task_if_orphaned(self, task, from_destructor):
        """Check the task, and delete it if it is orphaned"""
        # 1 for writer on task, 1 for the getrefcount call + 1 for each other writer/reader
        # If we are getting here from the destructor of an RPool channel, 
        # its totally valid to virtually decrement the refcount by 1 as 
        # we can expect it to drop once the destructor completes, which is when
        # we finish all recursive calls
        max_ref_count = 3 + from_destructor
        if sys.getrefcount(task.writer().channel) < max_ref_count:
            self.remove_task(task, from_destructor)
    #} END internal
    
    #{ Interface 
    def size(self):
        """:return: amount of workers in the pool
        :note: method is not threadsafe !"""
        return self._num_workers
    
    def set_size(self, size=0):
        """Set the amount of workers to use in this pool. When reducing the size, 
        threads will continue with their work until they are done before effectively
        being removed.
        
        :return: self
        :param size: if 0, the pool will do all work itself in the calling thread, 
            otherwise the work will be distributed among the given amount of threads.
            If the size is 0, newly added tasks will use channels which are NOT 
            threadsafe to optimize item throughput.
        
        :note: currently NOT threadsafe !"""
        assert size > -1, "Size cannot be negative"
        
        # either start new threads, or kill existing ones.
        # If we end up with no threads, we process the remaining chunks on the queue
        # ourselves
        cur_count = self._num_workers
        if cur_count < size:
            # we can safely increase the size, even from serial mode, as we would
            # only be able to do this if the serial ( sync ) mode finished processing.
            # Just adding more workers is not a problem at all.
            add_count = size - cur_count
            for i in range(add_count):
                self.WorkerCls(self._queue).start()
            # END for each new worker to create
            self._num_workers += add_count
        elif cur_count > size:
            # We don't care which thread exactly gets hit by our stop request
            # On their way, they will consume remaining tasks, but new ones 
            # could be added as we speak.
            del_count = cur_count - size
            for i in range(del_count):
                self._queue.put((self.WorkerCls.stop, True))    # arg doesnt matter
            # END for each thread to stop
            self._num_workers -= del_count
        # END handle count
        
        if size == 0:
            # NOTE: we do not preocess any tasks still on the queue, as we ill 
            # naturally do that once we read the next time, only on the tasks
            # that are actually required. The queue will keep the tasks, 
            # and once we are deleted, they will vanish without additional
            # time spend on them. If there shouldn't be any consumers anyway.
            # If we should reenable some workers again, they will continue on the 
            # remaining tasks, probably with nothing to do.
            # We can't clear the task queue if we have removed workers 
            # as they will receive the termination signal through it, and if 
            # we had added workers, we wouldn't be here ;).
            pass 
        # END process queue
        return self
        
    def num_tasks(self):
        """:return: amount of tasks"""
        self._taskgraph_lock.acquire()
        try:
            return len(self._tasks.nodes)
        finally:
            self._taskgraph_lock.release()
        
    def remove_task(self, task, _from_destructor_ = False):
        """
        Delete the task.
        Additionally we will remove orphaned tasks, which can be identified if their 
        output channel is only held by themselves, so no one will ever consume 
        its items.
        
        This method blocks until all tasks to be removed have been processed, if 
        they are currently being processed.
        
        :return: self"""
        self._taskgraph_lock.acquire()
        try:
            # it can be that the task is already deleted, but its chunk was on the 
            # queue until now, so its marked consumed again
            if not task in self._tasks.nodes:
                return self
            # END early abort
            
            # the task we are currently deleting could also be processed by 
            # a thread right now. We don't care about it as its taking care about
            # its write channel itself, and sends everything it can to it.
            # For it it doesn't matter that its not part of our task graph anymore.
        
            # now delete our actual node - be sure its done to prevent further 
            # processing in case there are still client reads on their way.
            task.set_done()
            
            # keep its input nodes as we check whether they were orphaned
            in_tasks = task.in_nodes
            self._tasks.remove_node(task)
            self._taskorder_cache.clear()
        finally:
            self._taskgraph_lock.release()
        # END locked deletion
        
        for t in in_tasks:
            self._remove_task_if_orphaned(t, _from_destructor_)
        # END handle orphans recursively
        
        return self
    
    def add_task(self, task):
        """Add a new task to be processed.
        
        :return: a read channel to retrieve processed items. If that handle is lost, 
            the task will be considered orphaned and will be deleted on the next 
            occasion."""
        # create a write channel for it
        ctype = Channel
        
        # adjust the task with our pool ref, if it has the slot and is empty
        # For now, we don't allow tasks to be used in multiple pools, except
        # for by their channels
        if hasattr(task, 'pool'):
            their_pool = task.pool()
            if their_pool is None:
                task.set_pool(self)
            elif their_pool is not self:
                raise ValueError("Task %r is already registered to another pool" % task.id)
            # END handle pool exclusivity
        # END handle pool aware tasks
        
        self._taskgraph_lock.acquire()
        try:
            self._taskorder_cache.clear()
            self._tasks.add_node(task)
            
            # Use a non-threadsafe queue
            # This brings about 15% more performance, but sacrifices thread-safety
            if self.size() == 0:
                ctype = SerialChannel
            # END improve locks
            
            # setup the tasks channel - respect the task creators choice though
            # if it is set.
            wc = task.writer()
            ch = None
            if wc is None:
                ch = ctype()
                wc = ChannelWriter(ch)
                task.set_writer(wc)
            else:
                ch = wc.channel
            # END create write channel ifunset
            rc = PoolReader(ch, task, self)
        finally:
            self._taskgraph_lock.release()
        # END sync task addition
        
        # If the input channel is one of our read channels, we add the relation
        if hasattr(task, 'reader'):
            ic = task.reader()
            if hasattr(ic, 'pool_ref') and ic.pool_ref()() is self:
                self._taskgraph_lock.acquire()
                try:
                    self._tasks.add_edge(ic._task_ref(), task)
                    
                    # additionally, bypass ourselves when reading from the 
                    # task, if possible
                    if hasattr(ic, '_read'):
                        task.set_read(ic._read)
                    # END handle read bypass
                finally:
                    self._taskgraph_lock.release()
                # END handle edge-adding
            # END add task relation
        # END handle input channels for connections
        
        return rc
            
    #} END interface 
    
    
class ThreadPool(Pool):
    """A pool using threads as worker"""
    WorkerCls = WorkerThread
    LockCls = Lock
        # NOTE: Since threading.Lock is a method not a class, we need to prevent
        # conversion to an unbound method.
    LockCls = staticmethod(Lock)
    TaskQueueCls = AsyncQueue

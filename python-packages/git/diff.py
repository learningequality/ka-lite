# diff.py
# Copyright (C) 2008, 2009 Michael Trier (mtrier@gmail.com) and contributors
#
# This module is part of GitPython and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

import re
from objects.blob import Blob
from objects.util import mode_str_to_int 
from exc import GitCommandError

from gitdb.util import hex_to_bin

	
__all__ = ('Diffable', 'DiffIndex', 'Diff')
	
class Diffable(object):
	"""Common interface for all object that can be diffed against another object of compatible type.
	
	:note: 
		Subclasses require a repo member as it is the case for Object instances, for practical 
		reasons we do not derive from Object."""
	__slots__ = tuple()
	
	# standin indicating you want to diff against the index
	class Index(object):
		pass 
		
	def _process_diff_args(self, args):
		"""
		:return:
			possibly altered version of the given args list.
			Method is called right before git command execution.
			Subclasses can use it to alter the behaviour of the superclass"""
		return args
	
	def diff(self, other=Index, paths=None, create_patch=False, **kwargs):
		"""Creates diffs between two items being trees, trees and index or an 
		index and the working tree.

		:param other:
			Is the item to compare us with. 
			If None, we will be compared to the working tree.
			If Treeish, it will be compared against the respective tree
			If Index ( type ), it will be compared against the index.
			It defaults to Index to assure the method will not by-default fail
			on bare repositories.

		:param paths:
			is a list of paths or a single path to limit the diff to.
			It will only include at least one of the givne path or paths.

		:param create_patch:
			If True, the returned Diff contains a detailed patch that if applied
			makes the self to other. Patches are somwhat costly as blobs have to be read
			and diffed.

		:param kwargs:
			Additional arguments passed to git-diff, such as 
			R=True to swap both sides of the diff.

		:return: git.DiffIndex
			
		:note:
			Rename detection will only work if create_patch is True.
			
			On a bare repository, 'other' needs to be provided as Index or as 
			as Tree/Commit, or a git command error will occour"""
		args = list()
		args.append( "--abbrev=40" )		# we need full shas
		args.append( "--full-index" )		# get full index paths, not only filenames
		
		if create_patch:
			args.append("-p")
			args.append("-M")				# check for renames
		else:
			args.append("--raw")
		
		if paths is not None and not isinstance(paths, (tuple,list)):
			paths = [ paths ]

		if other is not None and other is not self.Index:
			args.insert(0, other)
		if other is self.Index:
			args.insert(0, "--cached")
		
		args.insert(0,self)
		
		# paths is list here or None
		if paths:
			args.append("--")
			args.extend(paths)
		# END paths handling
		
		kwargs['as_process'] = True
		proc = self.repo.git.diff(*self._process_diff_args(args), **kwargs)
		
		diff_method = Diff._index_from_raw_format
		if create_patch:
			diff_method = Diff._index_from_patch_format
		index = diff_method(self.repo, proc.stdout)
		
		status = proc.wait()
		return index


class DiffIndex(list):
	"""Implements an Index for diffs, allowing a list of Diffs to be queried by 
	the diff properties.
	
	The class improves the diff handling convenience"""
	# change type invariant identifying possible ways a blob can have changed
	# A = Added
	# D = Deleted
	# R = Renamed
	# M = modified
	change_type = ("A", "D", "R", "M")
	
	
	def iter_change_type(self, change_type):
		"""
		:return:
			iterator yieling Diff instances that match the given change_type
		
		:param change_type:
			Member of DiffIndex.change_type, namely:
			
			* 'A' for added paths
			* 'D' for deleted paths
			* 'R' for renamed paths
			* 'M' for paths with modified data"""
		if change_type not in self.change_type:
			raise ValueError( "Invalid change type: %s" % change_type )
			
		for diff in self:
			if change_type == "A" and diff.new_file:
				yield diff
			elif change_type == "D" and diff.deleted_file:
				yield diff
			elif change_type == "R" and diff.renamed:
				yield diff
			elif change_type == "M" and diff.a_blob and diff.b_blob and diff.a_blob != diff.b_blob:
				yield diff
		# END for each diff
	

class Diff(object):
	"""A Diff contains diff information between two Trees.
	
	It contains two sides a and b of the diff, members are prefixed with 
	"a" and "b" respectively to inidcate that.
	
	Diffs keep information about the changed blob objects, the file mode, renames, 
	deletions and new files.
	
	There are a few cases where None has to be expected as member variable value:
	
	``New File``::
	
		a_mode is None
		a_blob is None
		
	``Deleted File``::
	
		b_mode is None
		b_blob is None
		
	``Working Tree Blobs``
	
		When comparing to working trees, the working tree blob will have a null hexsha
		as a corresponding object does not yet exist. The mode will be null as well.
		But the path will be available though. 
		If it is listed in a diff the working tree version of the file must 
		be different to the version in the index or tree, and hence has been modified."""
	
	# precompiled regex
	re_header = re.compile(r"""
								#^diff[ ]--git
									[ ]a/(?P<a_path>.+?)[ ]b/(?P<b_path>.+?)\n
								(?:^similarity[ ]index[ ](?P<similarity_index>\d+)%\n
								   ^rename[ ]from[ ](?P<rename_from>\S+)\n
								   ^rename[ ]to[ ](?P<rename_to>\S+)(?:\n|$))?
								(?:^old[ ]mode[ ](?P<old_mode>\d+)\n
								   ^new[ ]mode[ ](?P<new_mode>\d+)(?:\n|$))?
								(?:^new[ ]file[ ]mode[ ](?P<new_file_mode>.+)(?:\n|$))?
								(?:^deleted[ ]file[ ]mode[ ](?P<deleted_file_mode>.+)(?:\n|$))?
								(?:^index[ ](?P<a_blob_id>[0-9A-Fa-f]+)
									\.\.(?P<b_blob_id>[0-9A-Fa-f]+)[ ]?(?P<b_mode>.+)?(?:\n|$))?
							""", re.VERBOSE | re.MULTILINE)
	# can be used for comparisons
	NULL_HEX_SHA = "0"*40
	NULL_BIN_SHA = "\0"*20
	
	__slots__ = ("a_blob", "b_blob", "a_mode", "b_mode", "new_file", "deleted_file", 
				 "rename_from", "rename_to", "diff")

	def __init__(self, repo, a_path, b_path, a_blob_id, b_blob_id, a_mode,
				 b_mode, new_file, deleted_file, rename_from,
				 rename_to, diff):
	
		self.a_mode = a_mode
		self.b_mode = b_mode
		
		if self.a_mode:
			self.a_mode = mode_str_to_int(self.a_mode)
		if self.b_mode:
			self.b_mode = mode_str_to_int(self.b_mode)
		
		if a_blob_id is None:
			self.a_blob = None
		else:
			self.a_blob = Blob(repo, hex_to_bin(a_blob_id), mode=self.a_mode, path=a_path)
		if b_blob_id is None:
			self.b_blob = None
		else:
			self.b_blob = Blob(repo, hex_to_bin(b_blob_id), mode=self.b_mode, path=b_path)
		
		self.new_file = new_file
		self.deleted_file = deleted_file
		
		# be clear and use None instead of empty strings
		self.rename_from = rename_from or None
		self.rename_to = rename_to or None
		
		self.diff = diff


	def __eq__(self, other):
		for name in self.__slots__:
			if getattr(self, name) != getattr(other, name):
				return False
		# END for each name
		return True
		
	def __ne__(self, other):
		return not ( self == other )
		
	def __hash__(self):
		return hash(tuple(getattr(self,n) for n in self.__slots__))

	def __str__(self):
		h = "%s"
		if self.a_blob:
			h %= self.a_blob.path
		elif self.b_blob:		   
			h %= self.b_blob.path
		
		msg = ''
		l = None	# temp line
		ll = 0		# line length
		for b,n in zip((self.a_blob, self.b_blob), ('lhs', 'rhs')):
			if b:
				l = "\n%s: %o | %s" % (n, b.mode, b.hexsha)
			else:
				l = "\n%s: None" % n
			# END if blob is not None
			ll = max(len(l), ll)
			msg += l
		# END for each blob
		
		# add headline
		h += '\n' + '='*ll
		
		if self.deleted_file:
			msg += '\nfile deleted in rhs'
		if self.new_file:
			msg += '\nfile added in rhs'
		if self.rename_from:
			msg += '\nfile renamed from %r' % self.rename_from
		if self.rename_to:
			msg += '\nfile renamed to %r' % self.rename_to
		if self.diff:
			msg += '\n---'
			msg += self.diff
			msg += '\n---'
		# END diff info
		
		return h + msg

	@property
	def renamed(self):
		""":returns: True if the blob of our diff has been renamed"""
		return self.rename_from != self.rename_to

	@classmethod
	def _index_from_patch_format(cls, repo, stream):
		"""Create a new DiffIndex from the given text which must be in patch format
		:param repo: is the repository we are operating on - it is required 
		:param stream: result of 'git diff' as a stream (supporting file protocol)
		:return: git.DiffIndex """
		# for now, we have to bake the stream
		text = stream.read()
		index = DiffIndex()

		diff_header = cls.re_header.match
		for diff in ('\n' + text).split('\ndiff --git')[1:]:
			header = diff_header(diff)

			a_path, b_path, similarity_index, rename_from, rename_to, \
				old_mode, new_mode, new_file_mode, deleted_file_mode, \
				a_blob_id, b_blob_id, b_mode = header.groups()
			new_file, deleted_file = bool(new_file_mode), bool(deleted_file_mode)

			index.append(Diff(repo, a_path, b_path, a_blob_id, b_blob_id,
				old_mode or deleted_file_mode, new_mode or new_file_mode or b_mode,
				new_file, deleted_file, rename_from, rename_to, diff[header.end():]))

		return index
		
	@classmethod
	def _index_from_raw_format(cls, repo, stream):
		"""Create a new DiffIndex from the given stream which must be in raw format.
		:note: 
			This format is inherently incapable of detecting renames, hence we only 
			modify, delete and add files
		:return: git.DiffIndex"""
		# handles 
		# :100644 100644 6870991011cc8d9853a7a8a6f02061512c6a8190 37c5e30c879213e9ae83b21e9d11e55fc20c54b7 M	.gitignore
		index = DiffIndex()
		for line in stream:
			if not line.startswith(":"):
				continue
			# END its not a valid diff line
			old_mode, new_mode, a_blob_id, b_blob_id, change_type, path = line[1:].split(None, 5)
			path = path.strip()
			a_path = path
			b_path = path
			deleted_file = False
			new_file = False
			
			# NOTE: We cannot conclude from the existance of a blob to change type
			# as diffs with the working do not have blobs yet
			if change_type == 'D':
				b_blob_id = None
				deleted_file = True
			elif change_type == 'A':
				a_blob_id = None
				new_file = True
			# END add/remove handling
			
			diff = Diff(repo, a_path, b_path, a_blob_id, b_blob_id, old_mode, new_mode,
						new_file, deleted_file, None, None, '')
			index.append(diff)
		# END for each line
		
		return index


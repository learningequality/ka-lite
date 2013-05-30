from crawler import signals as test_signals

class Plugin(object):
    """
    This is a class to represent a plugin to the Crawler.
    Subclass it and define a start or stop function to be called on requests.
    Define a print_report function if your plugin outputs at the end of the run.
    """
    global_data = {}

    def __init__(self):
        #This should be refactored to call each of the subclasses.
        #Having them use the signal function signature is hacky..

        if hasattr(self, 'pre_request'):
            test_signals.pre_request.connect(self.pre_request)
        if hasattr(self, 'post_request'):
            test_signals.post_request.connect(self.post_request)
        if hasattr(self, 'start_run'):
            test_signals.start_run.connect(self.start_run)
        if hasattr(self, 'finish_run'):
            test_signals.finish_run.connect(self.finish_run)
        if hasattr(self, 'urls_parsed'):
            test_signals.urls_parsed.connect(self.urls_parsed)

        self.data = self.global_data[self.__class__.__name__] = {}

        # This will be updated when a run starts if the user wants output to
        # be saved:
        self.output_dir = None

    """
    #These functions enable instance['test'] to save to instance.data
    def __setitem__(self, key, val):
        self.global_data[self.__class__.__name__][key] = val

    def __getitem__(self, key):
        return self.global_data[self.__class__.__name__][key]
    """

    def set_output_dir(self, output_dir):
        """
        Extension point for subclasses to open files, create directories, etc.
        """

        self.output_dir = output_dir

from sphinx.errors import SphinxError

class ActionError(SphinxError):
    """ Exception raised for unrecognized actions in the input.

    Attributes:
      action: the action for which the error occured.
    """
    def __init__(self, action):
        self.action = action

    def __str__(self):
        return "The specified action '%s' is not recognized." % (self.action)

class OptionError(SphinxError):
    """ Exception raised for unrecognized options for an action in the input.

    Attributes:
      msg: the message to be thrown for the exception.
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

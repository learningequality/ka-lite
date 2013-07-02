from django.contrib.messages.storage.base import BaseStorage
from django.contrib.messages.storage.base import Message

class SessionStorage(BaseStorage):
    """
    Stores messages in the session (that is, django.contrib.sessions).
    """
    session_key = '_messages'

    def __init__(self, request, *args, **kwargs):
        assert hasattr(request, 'session'), "The session-based temporary "\
            "message storage requires session middleware to be installed, "\
            "and come before the message middleware in the "\
            "MIDDLEWARE_CLASSES list."
        super(SessionStorage, self).__init__(request, *args, **kwargs)

    def _get(self, *args, **kwargs):
        """
        Retrieves a list of messages from the request's session.  This storage
        always stores everything it is given, so return True for the
        all_retrieved flag.
        """
        return self.request.session.get(self.session_key), True

    def _store(self, messages, response, *args, **kwargs):
        """
        Stores a list of messages to the request's session.
        """
        if messages:
            self.request.session[self.session_key] = messages
        else:
            self.request.session.pop(self.session_key, None)
        return []

    def add(self, level, message, extra_tags=''):
        """
        Queues a message to be stored.

        The message is only queued if it contained something and its level is
        not less than the recording level (``self.level``).
        """
        for m in self._queued_messages:
        	if m.message == message:
        		return

        if not message:
            return
        # Check that the message level is not less than the recording level.
        level = int(level)
        if level < self.level:
            return
        # Add the message.
        self.added_new = True
        message = Message(level, message, extra_tags=extra_tags)
        self._queued_messages.append(message)
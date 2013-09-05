from django.contrib.messages.storage.session import SessionStorage

class NoDuplicateMessagesSessionStorage(SessionStorage):
    """
    This storage class prevents any messages from being added to the message buffer
    more than once.

    We extend the session store for AJAX-based messaging to work in Django 1.4,
       due to this bug: https://code.djangoproject.com/ticket/19387
    """

    def add(self, level, message, extra_tags=''):
        for m in self._queued_messages:
            if m.level == level and m.message == message and m.extra_tags == extra_tags:
                return
        super(NoDuplicateMessagesSessionStorage, self).add(level, message, extra_tags)
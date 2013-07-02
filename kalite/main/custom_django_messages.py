import django.contrib.messages.api

def _add_message(request, level, message, extra_tags='', fail_silently=False):
    """
    Attempts to add a message to the request using the 'messages' app.
    Edit: Checks for duplicated messages.
    """
    storage = django.contrib.messages.api.get_messages(request)

    for m in storage:
        storage.used = False
        if m.message == message:            
            return request._messages

    if hasattr(request, '_messages'):
        return request._messages.add(level, message, extra_tags)
    if not fail_silently:
        raise MessageFailure('You cannot add messages without installing '
                    'django.contrib.messages.middleware.MessageMiddleware')

def override_add_messages():
    django.contrib.messages.api.add_message = _add_message
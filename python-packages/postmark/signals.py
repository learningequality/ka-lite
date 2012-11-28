from django.dispatch import Signal

post_send = Signal(providing_args=["message", "response"])
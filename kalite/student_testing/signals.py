import django.dispatch

exam_unset = django.dispatch.Signal(providing_args=["test_id"])
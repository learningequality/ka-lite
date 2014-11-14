import django.dispatch

exam_unset = django.dispatch.Signal(providing_args=["test_id"])
unit_switch = django.dispatch.Signal(providing_args=["old_unit", "new_unit", "facility_id"])
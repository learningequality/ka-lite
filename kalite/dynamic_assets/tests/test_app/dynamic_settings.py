from django.db import models


class DynamicSettings(object):
    TEST_URL = True
    TEST_TEXT = "testing 123"
    IS_FAKE = True
    IS_OVERRIDEN = False

    not_a_setting = True

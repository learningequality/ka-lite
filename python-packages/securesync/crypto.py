"""
See crypto_notes.txt in this directory for more info about key formats, etc
"""
import base64
import hashlib
import re
import sys
import rsa as PYRSA

from django.conf import settings

from fle_utils.config.models import Settings
from fle_utils.crypto import *

_own_key = None

def load_keys():
    global _own_key

    # load key strings from the Settings models
    private_key_string = Settings.get("private_key")
    public_key_string = Settings.get("public_key")

    # check whether the keys have been overridden in the settings.py file, and ensure they match any existing keys
    if hasattr(settings, "OWN_DEVICE_PUBLIC_KEY") and hasattr(settings, "OWN_DEVICE_PRIVATE_KEY"):
        assert public_key_string == "" or public_key_string == settings.OWN_DEVICE_PUBLIC_KEY, "OWN_DEVICE_PUBLIC_KEY does not match public_key in Settings"
        assert private_key_string == "" or private_key_string == settings.OWN_DEVICE_PRIVATE_KEY, "OWN_DEVICE_PRIVATE_KEY does not match private_key in Settings"
        public_key_string = settings.OWN_DEVICE_PUBLIC_KEY
        private_key_string = settings.OWN_DEVICE_PRIVATE_KEY

    # instantiate from key strings or generate new key if needed
    if private_key_string and public_key_string:
        _own_key = Key(
            public_key_string=public_key_string,
            private_key_string=private_key_string)
    else:
        reset_keys()

def reset_keys():
    global _own_key
    _own_key = Key()
    Settings.set("private_key", _own_key.get_private_key_string())
    Settings.set("public_key", _own_key.get_public_key_string())

def get_own_key():
    if not _own_key:
        load_keys()
    return _own_key

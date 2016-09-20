import os

# This assertion should not be made here, make it where it's in use.
# from django.conf import settings
# assert hasattr(settings, "ROOT_UUID_NAMESPACE"), "ROOT_UUID_NAMESPACE setting must be defined to use the securesync module."

ID_MAX_LENGTH=32
IP_MAX_LENGTH=50

from kalite.version import VERSION

# JsonResponseMessageError codes
class ERROR_CODES:
    CLIENT_DEVICE_CORRUPTED = "client_device_corrupted"
    CLIENT_DEVICE_NOT_DEVICE = "client_device_not_device"
    CLIENT_DEVICE_INVALID_SIGNATURE = "client_device_invalid_signature"
    CHAIN_OF_TRUST_INVALID = "chain_of_trust_invalid"
    DEVICE_ALREADY_REGISTERED = "device_already_registered"
    PUBLIC_KEY_UNREGISTERED = "public_key_unregistered"


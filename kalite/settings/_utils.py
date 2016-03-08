import base64
import sys
import uuid


def generate_secret_key():
    key = base64.b64encode(str(uuid.uuid4()))
    return key


def cache_secret_key(key, key_file_path):
    try:
        with open(key_file_path, "w") as f:
            f.write(key)
            f.flush()
    except Exception as e:
        sys.stderr.write("Error writing secret key file. Error was: %s\n" % e)

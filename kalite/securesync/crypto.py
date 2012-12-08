import base64, hashlib, rsa
from kalite import settings
from config.models import Settings

keys = {
    "private": None,
    "public": None,
}

def load_keys():
    private_key_string = Settings.get("private_key")
    if private_key_string:
        public_key_string = Settings.get("public_key")
        keys["private"] = rsa.PrivateKey.load_pkcs1(private_key_string)
        keys["public"] = deserialize_public_key(public_key_string)
    else:
        reset_keys()

def reset_keys():
    try:
        (public_key, private_key) = rsa.newkeys(2048, poolsize=4)
    except:
        (public_key, private_key) = rsa.newkeys(2048)
    Settings.set("private_key", private_key.save_pkcs1())
    Settings.set("public_key", serialize_public_key(public_key))
    keys["private"] = private_key
    keys["public"] = public_key

def get_public_key():
    if not keys["public"]:
        load_keys()
    return keys["public"]

def get_private_key():
    if not keys["private"]:
        load_keys()
    return keys["private"]

def sign(message, key=None):
    return rsa.sign(hashed(message, base64encode=False), key or get_private_key(), "SHA-1")

def hashed(message, base64encode=False):
    # encode the message as UTF-8, replacing any invalid characters so they don't blow up the hashing
    sha1sum = hashlib.sha1(message.encode("utf-8", "replace")).digest()
    if base64encode:
        return encode_base64(sha1sum)
    else:
        return sha1sum

def verify(message, signature, key=None):
    try:
        rsa.verify(hashed(message, base64encode=False), signature, key or get_public_key())
    except rsa.pkcs1.VerificationError:
        return False
    return True

def serialize_public_key(key=None):
    if not key:
        key = get_public_key()
    return "".join([line for line in key.save_pkcs1().split("\n") if line and not line.startswith("-----")])
    
def deserialize_public_key(key_str):
    return rsa.PublicKey.load_pkcs1("-----BEGIN RSA PUBLIC KEY-----\n%s\n-----END RSA PUBLIC KEY-----" % key_str)
    
def encode_base64(data):
    return base64.encodestring(data).replace("\n", "")

def decode_base64(data):
    return base64.decodestring(data)
    
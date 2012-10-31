from M2Crypto import RSA
import base64, hashlib
from kalite import settings

private_key_path = settings.PROJECT_PATH + "/private_key.pem"

try:
    private_key = RSA.load_key(private_key_path)
except IOError:
    private_key = RSA.gen_key(2048, 65537, callback=lambda x,y,z: None)
    private_key.save_key(private_key_path, None)

public_key = RSA.new_pub_key(private_key.pub())

def sign(message, key=None):
    if not key:
        key = private_key
    return key.sign(hashed(message, base64encode=False), algo="sha1")

def hashed(message, base64encode=False):
    sha1sum = hashlib.sha1(message).digest()
    if base64encode:
        return encode_base64(sha1sum)
    else:
        return sha1sum

def verify(message, signature, key=None):
    if not key:
        key = public_key
    try:
        return key.verify(hashed(message, base64encode=False), signature, algo="sha1") == 1
    except RSA.RSAError:
        return False

def serialize_public_key(key=public_key):
    return ":".join(encode_base64(x) for x in key.pub())
    
def deserialize_public_key(key_str):
    return RSA.new_pub_key(decode_base64(q) for q in key_str.split(":"))
    
def encode_base64(data):
    return base64.encodestring(data).replace("\n", "")

def decode_base64(data):
    return base64.decodestring(data)
    
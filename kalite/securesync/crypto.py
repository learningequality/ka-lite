from M2Crypto import RSA
import base64, hashlib
from kalite import settings

private_key_path = settings.PROJECT_PATH + "/private_key.pem"

try:
    private_key = RSA.load_key(private_key_path)
except IOError:
    private_key = RSA.gen_key(512, 65537, callback=lambda x,y,z: None)
    private_key.save_key(private_key_path, None)

public_key = RSA.new_pub_key(private_key.pub())

def sign(message, key=None):
    if not key:
        key = private_key
    return key.sign(hashlib.sha1(message).digest(), algo="sha1").replace("\n", "")

def verify(message, signature, key=None):
    if not key:
        key = public_key
    try:
        return key.verify(hashlib.sha1(message).digest(), signature, algo="sha1") == 1
    except RSA.RSAError:
        return False

def serialize_public_key(key):
    return ":".join(base64.encodestring(x).strip() for x in key.pub()).replace("\n", "")
    
def deserialize_public_key(key_str):
    return RSA.new_pub_key(base64.decodestring(q) for q in key_str.split(":"))
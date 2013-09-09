# see crypto_notes.txt in this directory for more info about key formats, etc

import base64, hashlib, sys, re
import rsa as PYRSA

try:
    from M2Crypto import RSA as M2RSA
    from M2Crypto import BIO as M2BIO
    M2CRYPTO_EXISTS = True
except:
    M2CRYPTO_EXISTS = False

PKCS8_HEADER = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A"

class Key(object):
    
    _public_key = None
    _private_key = None
    _using_m2crypto = False
    
    def __init__(self, private_key_string=None, public_key_string=None, key=None, use_m2crypto=M2CRYPTO_EXISTS):
        
        self._using_m2crypto = use_m2crypto
                
        if private_key_string:
            self.set_private_key_string(private_key_string)
        
        if public_key_string:
            self.set_public_key_string(public_key_string)
        
        # if no keys were provided, assume we're generating a new key
        if not private_key_string and not public_key_string:
            self._generate_new_key()

    def _generate_new_key(self):
        if self._using_m2crypto:
            self._private_key = M2RSA.gen_key(2048, 65537, lambda x,y,z: None)
            self._public_key = M2RSA.RSA_pub(self._private_key.rsa)
        else:
            try:
                (self._public_key, self._private_key) = PYRSA.newkeys(2048, poolsize=4)
            except:
                (self._public_key, self._private_key) = PYRSA.newkeys(2048)
    
    def sign(self, message, base64encode=True):
        
        if not self._private_key:
            raise Exception("Key object does not have a private key defined, and thus cannot be used to sign.")
        
        if self._using_m2crypto:
            signature = self._private_key.sign(hashed(message), algo="sha1")
        else:
            signature = PYRSA.sign(message, self._private_key, "SHA-1")
        
        if base64encode:
            return encode_base64(signature)
        else:
            return signature
            
    def verify(self, message, signature):
        # assume we're dealing with a base64 encoded signature, but pass on through if not
        try:
            signature = decode_base64(signature)
        except:
            pass
        
        # try verifying using the public key if available, otherwise the private key
        key = self._public_key or self._private_key or None
        if not key:
            raise Exception("Key object does not have public or private key defined, and thus cannot be used to verify.")
        
        if self._using_m2crypto:
            try:
                key.verify(hashed(message), signature, algo="sha1")
                return True
            except M2RSA.RSAError:
                # some old versions accidentally double-hashed; make sure those old sigs verify too
                try:
                    key.verify(hashed(hashed(message)), signature, algo="sha1")
                    return True
                except M2RSA.RSAError:
                    pass
                return False
        else:
            try:
                PYRSA.verify(message, signature, key)
                return True
            except PYRSA.pkcs1.VerificationError:
                # some old versions accidentally double-hashed; make sure those old sigs verify too
                try:
                    PYRSA.verify(hashed(message), signature, key)
                    return True
                except PYRSA.pkcs1.VerificationError:
                    pass
                return False

    def _hash_large_file(self, filename, chunk_size=None):
        """
        Process a file into a single hash, by taking
        bite-sized chunks.
        Useful for signing the full file.
        """
        hasher = hashlib.sha256()
        chunk_size = chunk_size or hasher.block_size * 1000  #(64,000 on my machine)

        with open(filename, "rb") as fp:
            while True:
                # Chunk file into chunks of 1K.
                #   Write each chunk as a separate signature.
                bytes = fp.read(chunk_size)
                if not bytes:  # stop when we've hit EOF
                    break
                hasher.update(bytes)
        return hasher.hexdigest()

    def sign_large_file(self, filename, chunk_size=None):
        """
        Sign a large file by taking in bite-sized chunks,
        signing each chunk, then appending each signature
        with newlines.
        """
        return self.sign(self._hash_large_file(filename, chunk_size))

    def verify_large_file(self, filename, signature, chunk_size=None):
        """
        Verify a large file by taking in bite-sized chunks,
        signing each chunk, then comparing to a set of signatures,
        either as a list or separated by newlines.
        """
        return self.verify(self._hash_large_file(filename, chunk_size), signature)

    def get_public_key_string(self):
        
        if not self._public_key:
            raise Exception("Key object does not have a public key defined.")
        
        if self._using_m2crypto:
            pem_string = self._public_key.as_pem(None)
        else:
            pem_string = self._public_key.save_pkcs1()
        
        # remove the headers and footer (to save space, but mostly because the text in them varies)
        pem_string = remove_pem_headers(pem_string)
        
        # remove the PKCS#8 header so the key won't cause problems for older versions
        if pem_string.startswith(PKCS8_HEADER):
            pem_string = pem_string[len(PKCS8_HEADER):]
        
        # remove newlines, to ensure consistency when used as an index (e.g. on central server)
        pem_string = pem_string.replace("\n", "")
        
        return pem_string

    def get_private_key_string(self):
        if not self._private_key:
            raise Exception("Key object does not have a private key defined.")
        if self._using_m2crypto:
            return self._private_key.as_pem(None)
        else:
            return self._private_key.save_pkcs1()

    def set_public_key_string(self, public_key_string):
        
        # convert from unicode, as this can throw off the key parsing
        public_key_string = str(public_key_string)
        
        # remove the PEM header/footer
        public_key_string = remove_pem_headers(public_key_string)
                
        if self._using_m2crypto:
            header_string = "PUBLIC KEY"
            # add the PKCS#8 header if it doesn't exist
            if not public_key_string.startswith(PKCS8_HEADER):
                public_key_string = PKCS8_HEADER + public_key_string
            # break up the base64 key string into lines of max length 64, to please m2crypto
            public_key_string = public_key_string.replace("\n", "")
            public_key_string = "\n".join(re.findall(".{1,64}", public_key_string))
        else:
            header_string = "RSA PUBLIC KEY"
            # remove PKCS#8 header if it exists
            if public_key_string.startswith(PKCS8_HEADER):
                public_key_string = public_key_string[len(PKCS8_HEADER):]

        # add the appropriate PEM header/footer
        public_key_string = add_pem_headers(public_key_string, header_string)
        
        if self._using_m2crypto:
            self._public_key = M2RSA.load_pub_key_bio(M2BIO.MemoryBuffer(public_key_string))
        else:
            self._public_key = PYRSA.PublicKey.load_pkcs1(public_key_string)

    def set_private_key_string(self, private_key_string):

        # convert from unicode, as this can throw off the key parsing
        private_key_string = str(private_key_string)

        private_key_string = add_pem_headers(private_key_string, "RSA PRIVATE KEY")
        
        if self._using_m2crypto:
            self._private_key = M2RSA.load_key_string(private_key_string)
            self._public_key = M2RSA.RSA_pub(self._private_key.rsa)
        else:
            self._private_key = PYRSA.PrivateKey.load_pkcs1(private_key_string)
            # TODO(jamalex): load public key here automatically as well?
    
    def __str__(self):
        return self.get_public_key_string()

def remove_pem_headers(pem_string):
    if not pem_string.strip().startswith("-----"):
        return pem_string
    return "\n".join([line for line in pem_string.split("\n") if line and not line.startswith("---")])

def add_pem_headers(pem_string, header_string):
    context = {
        "key": remove_pem_headers(pem_string),
        "header_string": header_string,
    }
    return "-----BEGIN %(header_string)s-----\n%(key)s\n-----END %(header_string)s-----" % context

def hashed(message):
    # try to encode the message as UTF-8, replacing any invalid characters so they don't blow up the hashing
    try:
        message = message.encode("utf-8", "replace")
    except UnicodeDecodeError:
        pass
    return hashlib.sha1(message).digest()
    
def encode_base64(data):
    return base64.encodestring(data).replace("\n", "")

def decode_base64(data):
    return base64.decodestring(data)
    
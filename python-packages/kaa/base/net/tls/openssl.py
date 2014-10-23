# -* -coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# openssl.py - ctypes OpenSSL backend for TLSSocket
# -----------------------------------------------------------------------------
# This module is ugly and low level, but it has the benefit of working
# out-of-the-box on either Python 2 or 3, on non-CPython interpreters, and
# doesn't depend on poorly maintained third party modules.
#
# The implementation is heavily inspired from pyOpenSSL's SSLConnection and
# Twisted's use of it.
# -----------------------------------------------------------------------------
# Copyright 2012 Jason Tackaberry
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version
# 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA
#
# -----------------------------------------------------------------------------
from __future__ import absolute_import

__all__ = [
    'TLSSocket', 'TLSContext', 'Certificate', 'X509Name', 'TLSError',
    'TLSVerificationError', 'TLSProtocolError', 'libssl'
    ]

# python imports
import sys
import threading
import thread
import logging
import os
import binascii
import hmac
import hashlib
from fnmatch import fnmatch # for wildcard certs
from datetime import datetime
from ctypes import *
from ctypes import util
try:
    # Initialize thread support from Python's native OpenSSL implementation --
    # see openssl_init() below for details.
    import _ssl
except ImportError:
    # I'm not sure why this would fail but since we have a fallback, it's not
    # fatal.
    pass

# kaa imports
import kaa
from kaa.strutils import bl, nativestr, py3_str, py3_b
from kaa.dateutils import utc


# get logging object
log = logging.getLogger('kaa.base.net.tls.openssl')

# OpenSSL constants (the ones we use)
SSL_MODE_ENABLE_PARTIAL_WRITE = 0x00000001
SSL_MODE_ACCEPT_MOVING_WRITE_BUFFER = 0x00000002
SSL_MODE_AUTO_RETRY = 0x00000004

SSL_ERROR_NONE = 0
SSL_ERROR_SSL = 1
SSL_ERROR_WANT_READ = 2
SSL_ERROR_WANT_WRITE = 3
SSL_ERROR_WANT_X509_LOOKUP = 4
SSL_ERROR_SYSCALL = 5
SSL_ERROR_ZERO_RETURN = 6
SSL_ERROR_WANT_CONNECT = 7
SSL_ERROR_WANT_ACCEPT = 8

SSL_ST_OK = 0x03

SSL_CTRL_SET_TMP_DH = 3
SSL_CTRL_GET_SESSION_REUSED = 8
SSL_CTRL_OPTIONS = 32
SSL_CTRL_MODE = 33
SSL_CTRL_SET_SESS_CACHE_SIZE = 42
SSL_CTRL_SET_SESS_CACHE_MODE = 44
SSL_CTRL_SET_TLSEXT_TICKET_KEYS = 59
SSL_CTRL_GET_RI_SUPPORT = 76

SSL_SESS_CACHE_OFF = 0x0000
SSL_SESS_CACHE_CLIENT = 0x0001
SSL_SESS_CACHE_SERVER = 0x0002
SSL_SESS_CACHE_BOTH = SSL_SESS_CACHE_CLIENT | SSL_SESS_CACHE_SERVER

SSL_OP_ALL = 0x00000FFF
SSL_OP_NO_SSLv2 = 0x01000000
SSL_VERIFY_NONE = 0x00

BIO_C_SET_BUF_MEM_EOF_RETURN = 130
BIO_NOCLOSE = 0x00
BIO_FLAGS_READ = 0x01
BIO_FLAGS_WRITE = 0x02
BIO_FLAGS_IO_SPECIAL = 0x04
BIO_FLAGS_SHOULD_RETRY = 0x08

X509_FILETYPE_PEM = 1
X509_FILETYPE_ASN1 =  2
X509_FILETYPE_DEFAULT = 3
X509_R_CERT_ALREADY_IN_HASH_TABLE = 101
X509_V_OK = 0
V_ASN1_GENERALIZEDTIME = 24
NID_subject_alt_name = 85

class C_DH(Structure):
    _fields_ = [
        ('pad', c_int),
        ('version', c_int),
        ('p', c_void_p),
        ('g', c_void_p),
    ]

class C_GENERAL_NAME(Structure):
    _fields_ = [
        ('type', c_int),
        ('data', c_void_p)
    ]

class C_X509_VAL(Structure):
    _fields_ = [
        ('notBefore', c_void_p),
        ('notAfter', c_void_p),
    ]

class C_X509_CINF(Structure):
    _fields_ = [
        ('version', c_void_p),
        ('serialNumber', c_void_p),
        ('signature', c_void_p),
        ('issuer', c_void_p),
        ('validity', POINTER(C_X509_VAL)),
        ('subject', c_void_p),
        ('key', c_void_p),
        ('issuerUID', c_void_p),
        ('subjectUID', c_void_p),
        ('extensions', c_void_p),
    ]

class C_X509(Structure):
    _fields_ = [
        ('cert_info', POINTER(C_X509_CINF))
    ]

VERIFY_CALLBACK = CFUNCTYPE(c_int, c_int, c_void_p, use_errno=True, use_last_error=True)
PASSWD_CALLBACK = CFUNCTYPE(c_int, c_void_p, c_int, c_int, c_void_p, use_errno=True, use_last_error=True)
LOCKING_CALLBACK = CFUNCTYPE(None, c_int, c_int, c_char_p, c_int, use_errno=True, use_last_error=True)
ID_CALLBACK = CFUNCTYPE(c_ulong, use_errno=True, use_last_error=True)


class TLSError(Exception):
    """
    Base class for all TLS/SSL exceptions.

    Exception args is a message string.
    """
    pass

class TLSProtocolError(TLSError):
    """
    Raised when a protocol-related problem occurs, such as the remote end does
    not speak TLS, or when no shared cipher could be established.
    """
    pass

class TLSVerificationError(TLSError):
    """
    Raised when the remote end's certificate did not verify correctly.
    """
    pass


class BIOError(TLSError):
    """
    Raised when there are any OpenSSL errors in the BIO_* functions.
    """
    pass

class WantReadError(Exception):
    pass

class WantWriteError(Exception):
    pass

class ZeroReturnError(Exception):
    pass


class LibSSL(object):
    """
    Wrapper class to do on-demand loading of openssl.
    """
    def __init__(self):
        self._cdll = None


    def __getattr__(self, name):
        if not self._cdll:
            self.initialize()
        return getattr(self._cdll, name)


    def initialize(self, lib='ssl'):
        """
        Initialize openssl from the given library, which is either a library
        name or a CDLL object.
        """
        trylibs = []
        if isinstance(lib, str):
            lib = util.find_library(lib)
        if lib:
            if isinstance(lib, str):
                trylibs.append(CDLL(lib, use_errno=True))
            elif isinstance(lib, CDLL):
                trylibs.append(lib)
            else:
                raise TypeError('lib must be string or CDLL object')

        # Also try the PyDLL in case ssl is linked in.
        trylibs.append(pythonapi)

        err = None
        for lib in trylibs:
            try:
                self._init_definitions(lib)
            except Exception, e:
                err = err or e
            else:
                self._cdll = lib
                return
        else:
            raise err or ImportError('no openssl candidate libraries found')


    def _init_definitions(self, libssl):
        """
        Initialize in the given CDLL the restype/argtypes for all OpenSSL
        functions used in this module.  (Not all functions in the library, just
        the ones we're interested in.)
        """
        # void OPENSSL_add_all_algorithms_conf(void);
        libssl.OPENSSL_add_all_algorithms_conf.restype = None
        libssl.OPENSSL_add_all_algorithms_conf.argtypes = []
        # void ERR_load_ERR_strings(void);
        libssl.ERR_load_ERR_strings.restype = None
        libssl.ERR_load_ERR_strings.argtypes = []
        # void SSL_load_error_strings(void );
        libssl.SSL_load_error_strings.restype = None
        libssl.SSL_load_error_strings.argtypes = []
        # int SSL_library_init(void );
        libssl.SSL_library_init.restype = c_int
        libssl.SSL_library_init.argtypes = []

        # const char *ERR_reason_error_string(unsigned long e);
        libssl.ERR_reason_error_string.restype = c_char_p
        libssl.ERR_reason_error_string.argtypes = [c_ulong]
        # unsigned long ERR_peek_error(void);
        libssl.ERR_peek_error.restype = c_ulong
        libssl.ERR_peek_error.argtypes = []
        # unsigned long ERR_get_error(void);
        libssl.ERR_get_error.restype = c_ulong
        libssl.ERR_get_error.argtypes = []

        # SSL_METHOD *SSLv23_method(void);
        libssl.SSLv23_method.restype = c_void_p
        libssl.SSLv23_method.argtypes = []
        # SSL_METHOD *SSLv23_client_method(void);
        libssl.SSLv23_client_method.restype = c_void_p
        libssl.SSLv23_client_method.argtypes = []
        # SSL_CT *SSL_CTX_new(SSL_METHOD *meth);
        libssl.SSL_CTX_new.restype = c_void_p
        libssl.SSL_CTX_new.argtypes = [c_void_p]
        # long SSL_CTX_ctrl(SSL_CTX *ctx,int cmd, long larg, void *parg);
        libssl.SSL_CTX_ctrl.restype = c_long
        libssl.SSL_CTX_ctrl.argtypes = [c_void_p, c_long, c_long, c_void_p]
        # int SSL_CTX_set_cipher_list(SSL_CTX *,const char *str);
        libssl.SSL_CTX_set_cipher_list.restype = c_int
        libssl.SSL_CTX_set_cipher_list.argtypes = [c_void_p, c_char_p]
        # const char *SSL_get_cipher_list(const SSL *ssl, int priority);
        libssl.SSL_get_cipher_list.restype = c_char_p
        libssl.SSL_get_cipher_list.argtypes = [c_void_p, c_int]
        # int SSL_CTX_load_verify_locations(SSL_CTX *ctx, const char *CAfile, const char *CApath);
        libssl.SSL_CTX_load_verify_locations.restype = c_int
        libssl.SSL_CTX_load_verify_locations.argtypes = [c_void_p, c_char_p, c_char_p]
        # int SSL_CTX_use_certificate_chain_file(SSL_CTX *ctx, const char *file);
        libssl.SSL_CTX_use_certificate_chain_file.restype = c_int
        libssl.SSL_CTX_use_certificate_chain_file.argtypes = [c_void_p, c_char_p]
        # int SSL_CTX_use_PrivateKey_file(SSL_CTX *ctx, const char *file, int type);
        libssl.SSL_CTX_use_PrivateKey_file.restype = c_int
        libssl.SSL_CTX_use_PrivateKey_file.argtypes = [c_void_p, c_char_p, c_int]
        # void SSL_CTX_set_verify(SSL_CTX *ctx,int mode, int (*callback)(int, X509_STORE_CTX *));
        libssl.SSL_CTX_set_verify.restype = None
        libssl.SSL_CTX_set_verify.argtypes = [c_void_p, c_int, c_void_p]
        # void SSL_CTX_set_default_passwd_cb(SSL_CTX *ctx, pem_password_cb *cb);
        libssl.SSL_CTX_set_default_passwd_cb.restype = None
        libssl.SSL_CTX_set_default_passwd_cb.argtypes = [c_void_p, c_void_p]
        # void SSL_CTX_free(SSL_CTX *);
        libssl.SSL_CTX_free.restype = None
        libssl.SSL_CTX_free.argtypes = [c_void_p]

        # SSL *SSL_new(SSL_CTX *ctx);
        libssl.SSL_new.restype = c_void_p
        libssl.SSL_new.argtypes = [c_void_p]
        # int SSL_read(SSL *ssl,void *buf,int num);
        libssl.SSL_read.restype = c_int
        libssl.SSL_read.argtypes = [c_void_p, c_void_p, c_int]
        # int SSL_write(SSL *ssl,const void *buf,int num);
        libssl.SSL_write.restype = c_int
        libssl.SSL_write.argtypes = [c_void_p, c_void_p, c_int]
        # int SSL_shutdown(SSL *s);
        libssl.SSL_shutdown.restype = c_int
        libssl.SSL_shutdown.argtypes = [c_void_p]
        # int SSL_do_handshake(SSL *s);
        libssl.SSL_do_handshake.restype = c_int
        libssl.SSL_do_handshake.argtypes = [c_void_p]
        # int SSL_state(const SSL *ssl);
        libssl.SSL_state.restype = c_int
        libssl.SSL_state.argtypes = [c_void_p]
        # void SSL_set_connect_state(SSL *s);
        libssl.SSL_set_connect_state.restype = None
        libssl.SSL_set_connect_state.argtypes = [c_void_p]
        # void SSL_set_accept_state(SSL *s);
        libssl.SSL_set_accept_state.restype = None
        libssl.SSL_set_accept_state.argtypes = [c_void_p]
        # long SSL_ctrl(SSL *ssl,int cmd, long larg, void *parg);
        libssl.SSL_ctrl.restype = c_long
        libssl.SSL_ctrl.argtypes = [c_void_p, c_int, c_long, c_void_p]
        # void SSL_set_bio(SSL *s, BIO *rbio,BIO *wbio);
        libssl.SSL_set_bio.restype = None
        libssl.SSL_set_bio.argtypes = [c_void_p, c_void_p, c_void_p]
        # int SSL_shutdown(SSL *s);
        libssl.SSL_shutdown.restype = c_int
        libssl.SSL_shutdown.argtypes = [c_void_p]
        # long SSL_get_verify_result(const SSL *ssl);
        libssl.SSL_get_verify_result.restype = c_long
        libssl.SSL_get_verify_result.argtypes = [c_void_p]
        # void SSL_set_verify(SSL *s, int mode, int (*verify_callback)(int, X509_STORE_CTX *));
        libssl.SSL_set_verify.restype = None
        libssl.SSL_set_verify.argtypes = [c_void_p, c_int, c_void_p]
        # void SSL_free(SSL *ssl);
        libssl.SSL_free.restype = None
        libssl.SSL_free.argtypes = [c_void_p]
        # int SSL_get_error(const SSL *s,int ret_code);
        libssl.SSL_get_error.restype = c_int
        libssl.SSL_get_error.argtypes = [c_void_p, c_int]
        # SSL_SESSION *SSL_get1_session(SSL *ssl);
        libssl.SSL_get1_session.restype = c_void_p
        libssl.SSL_get1_session.argtypes = [c_void_p]
        # int SSL_set_session(SSL *to, SSL_SESSION *session);
        libssl.SSL_set_session.restype = c_int
        libssl.SSL_set_session.argtypes = [c_void_p, c_void_p]
        # void SSL_SESSION_free(SSL_SESSION *ses);
        libssl.SSL_SESSION_free.restype = None
        libssl.SSL_SESSION_free.argtypes = [c_void_p]

        # BIO *BIO_new(BIO_METHOD *type);
        libssl.BIO_new.restype = c_void_p
        libssl.BIO_new.argtypes = [c_void_p]
        # BIO *BIO_new_file(const char *filename, const char *mode);
        libssl.BIO_new_file.restype = c_void_p
        libssl.BIO_new_file.argtypes = [c_char_p, c_char_p]
        # BIO_METHOD *BIO_f_ssl(void);
        libssl.BIO_f_ssl.restype = c_void_p
        libssl.BIO_f_ssl.argtypes = []
        # BIO_METHOD *BIO_s_mem(void);
        libssl.BIO_s_mem.restype = c_void_p
        libssl.BIO_s_mem.argtypes = []
        # long BIO_ctrl(BIO *bp,int cmd,long larg,void *parg);
        libssl.BIO_ctrl.restype = c_long
        libssl.BIO_ctrl.argtypes = [c_void_p, c_int, c_long, c_void_p]
        # long BIO_int_ctrl(BIO *bp,int cmd,long larg,int iarg);
        libssl.BIO_int_ctrl.restype = c_long
        libssl.BIO_int_ctrl.argtypes = [c_void_p, c_int, c_long, c_int]
        # void BIO_free_all(BIO *a);
        libssl.BIO_free_all.restype = None
        libssl.BIO_free_all.argtypes = [c_void_p]
        # size_t BIO_ctrl_get_write_guarantee(BIO *b);
        libssl.BIO_ctrl_get_write_guarantee.restype = c_size_t
        libssl.BIO_ctrl_get_write_guarantee.argtypes = [c_void_p]
        # int BIO_write(BIO *b, const void *data, int len);
        libssl.BIO_write.restype = c_int
        libssl.BIO_write.argtypes = [c_void_p, c_void_p, c_int]
        # int BIO_read(BIO *b, void *data, int len);
        libssl.BIO_read.restype = c_int
        libssl.BIO_read.argtypes = [c_void_p, c_void_p, c_int]
        # int BIO_test_flags(const BIO *b, int flags);
        libssl.BIO_test_flags.restype = c_int
        libssl.BIO_test_flags.argtypes = [c_void_p, c_int]
        # size_t BIO_ctrl_pending(BIO *b);
        libssl.BIO_ctrl_pending.restype = c_size_t
        libssl.BIO_ctrl_pending.argtypes = [c_void_p]
        # BIO_METHOD *BIO_s_file(void );
        libssl.BIO_s_file.restype = c_void_p
        libssl.BIO_s_file.argtypes = []

        # void CRYPTO_set_id_callback(unsigned long (*func)(void));
        libssl.CRYPTO_set_id_callback.restype = None
        libssl.CRYPTO_set_id_callback.argtypes = [c_void_p]
        # void CRYPTO_set_locking_callback(void (*func)(int mode,int type, const char *file,int line));
        libssl.CRYPTO_set_locking_callback.restype = None
        libssl.CRYPTO_set_locking_callback.argtypes = [c_void_p]
        # void (*CRYPTO_get_locking_callback(void))(int mode,int type,const char *file, int line);
        libssl.CRYPTO_get_locking_callback.restype = c_void_p
        libssl.CRYPTO_get_locking_callback.argtypes = []
        # int CRYPTO_num_locks(void);
        libssl.CRYPTO_num_locks.restype = c_int
        libssl.CRYPTO_num_locks.argtypes = []
        # void CRYPTO_free(void *);
        libssl.CRYPTO_free.restype = None
        libssl.CRYPTO_free.argtypes = [c_void_p]

        # const char *X509_get_default_cert_dir(void);
        libssl.X509_get_default_cert_dir.restype = c_char_p
        libssl.X509_get_default_cert_dir.argtypes = []
        # const char *X509_get_default_cert_file(void);
        libssl.X509_get_default_cert_file.restype = c_char_p
        libssl.X509_get_default_cert_file.argtypes = []
        # X509 *X509_STORE_CTX_get_current_cert(X509_STORE_CTX *ctx);
        libssl.X509_STORE_CTX_get_current_cert.restype = c_void_p
        libssl.X509_STORE_CTX_get_current_cert.argtypes = [c_void_p]
        # int X509_STORE_CTX_get_error(X509_STORE_CTX *ctx);
        libssl.X509_STORE_CTX_get_error.restype = c_int
        libssl.X509_STORE_CTX_get_error.argtypes = [c_void_p]
        # int X509_STORE_CTX_get_error_depth(X509_STORE_CTX *ctx);
        libssl.X509_STORE_CTX_get_error_depth.restype = c_int
        libssl.X509_STORE_CTX_get_error_depth.argtypes = [c_void_p]
        # const char *X509_verify_cert_error_string(long n);
        libssl.X509_verify_cert_error_string.restype = c_char_p
        libssl.X509_verify_cert_error_string.argtypes = [c_long]
        # void X509_STORE_CTX_set_error(X509_STORE_CTX *ctx,int s);
        libssl.X509_STORE_CTX_set_error.restype = None
        libssl.X509_STORE_CTX_set_error.argtypes = [c_void_p, c_int]
        # X509 *X509_dup(X509 *x509);
        libssl.X509_dup.restype = c_void_p
        libssl.X509_dup.argtypes = [c_void_p]
        # void X509_free(X509 *a);
        libssl.X509_free.restype = None
        libssl.X509_free.argtypes = [c_void_p]
        # X509_NAME *X509_get_subject_name(X509 *a);
        libssl.X509_get_subject_name.restype = c_void_p
        libssl.X509_get_subject_name.argtypes = [c_void_p]
        # X509_NAME *X509_get_issuer_name(X509 *a);
        libssl.X509_get_issuer_name.restype = c_void_p
        libssl.X509_get_issuer_name.argtypes = [c_void_p]
        # ASN1_INTEGER *X509_get_serialNumber(X509 *x);
        libssl.X509_get_serialNumber.restype = c_void_p
        libssl.X509_get_serialNumber.argtypes = [c_void_p]
        # void  *X509_get_ext_d2i(X509 *x, int nid, int *crit, int *idx);
        libssl.X509_get_ext_d2i.restype = c_void_p
        libssl.X509_get_ext_d2i.argtypes = [c_void_p, c_int, POINTER(c_int), POINTER(c_int)]
        # STACK_OF(CONF_VALUE) *i2v_GENERAL_NAMES(X509V3_EXT_METHOD *method, GENERAL_NAMES *gen, STACK_OF(CONF_VALUE) *extlist);
        libssl.i2v_GENERAL_NAMES.restype = c_void_p
        libssl.i2v_GENERAL_NAMES.argtypes = [c_void_p, c_void_p, c_void_p]

        # char *X509_NAME_oneline(X509_NAME *a,char *buf,int size);
        libssl.X509_NAME_oneline.restype = c_char_p
        libssl.X509_NAME_oneline.argtypes = [c_void_p, c_char_p, c_int]
        # int X509_NAME_cmp(const X509_NAME *a, const X509_NAME *b);
        libssl.X509_NAME_cmp.restype = c_int
        libssl.X509_NAME_cmp.argtypes = [c_void_p, c_void_p]
        # int X509_NAME_entry_count(X509_NAME *name);
        libssl.X509_NAME_entry_count.restype = c_int
        libssl.X509_NAME_entry_count.argtypes = [c_void_p]
        # X509_NAME_ENTRY *X509_NAME_get_entry(X509_NAME *name, int loc);
        libssl.X509_NAME_get_entry.restype = c_void_p
        libssl.X509_NAME_get_entry.argtypes = [c_void_p, c_int]
        # ASN1_OBJECT *X509_NAME_ENTRY_get_object(X509_NAME_ENTRY *ne);
        libssl.X509_NAME_ENTRY_get_object.restype = c_void_p
        libssl.X509_NAME_ENTRY_get_object.argtypes = [c_void_p]
        # ASN1_STRING *X509_NAME_ENTRY_get_data(X509_NAME_ENTRY *ne);
        libssl.X509_NAME_ENTRY_get_data.restype = c_void_p
        libssl.X509_NAME_ENTRY_get_data.argtypes = [c_void_p]
        # unsigned long X509_subject_name_hash(X509 *x);
        libssl.X509_subject_name_hash.restype = c_long
        libssl.X509_subject_name_hash.argtypes = [c_void_p]
        # int X509_digest(const X509 *data,const EVP_MD *type, unsigned char *md, unsigned int *len);
        libssl.X509_digest.restype = c_int
        libssl.X509_digest.argtypes = [c_void_p, c_void_p, c_char_p, POINTER(c_int)]
        # int X509v3_get_ext_count(const STACK_OF(X509_EXTENSION) *x);
        libssl.X509v3_get_ext_count.restype = c_int
        libssl.X509v3_get_ext_count.argtypes = [c_void_p]
        # int X509_get_ext_count(const STACK_OF(X509_EXTENSION) *x);
        libssl.X509_get_ext_count.restype = c_int
        libssl.X509_get_ext_count.argtypes = [c_void_p]
        # X509_EXTENSION *X509_get_ext(X509 *x, int loc);
        libssl.X509_get_ext.restype = c_void_p
        libssl.X509_get_ext.argtypes = [c_void_p, c_int]

        # ASN1_OBJECT *X509_EXTENSION_get_object(X509_EXTENSION *ex);
        libssl.X509_EXTENSION_get_object.restype = c_void_p
        libssl.X509_EXTENSION_get_object.argtypes = [c_void_p]
        # ASN1_OCTET_STRING *X509_EXTENSION_get_data(X509_EXTENSION *ne);
        libssl.X509_EXTENSION_get_data.restype = c_void_p
        libssl.X509_EXTENSION_get_data.argtypes = [c_void_p]
        # int X509_EXTENSION_get_critical(X509_EXTENSION *ex);
        libssl.X509_EXTENSION_get_critical.restype = c_int
        libssl.X509_EXTENSION_get_critical.argtypes = [c_void_p]

        # int sk_num(const STACK *);
        libssl.sk_num.restype = c_int
        libssl.sk_num.argtypes = [c_void_p]
        # char *sk_value(const STACK *, int);
        libssl.sk_value.restype = c_void_p
        libssl.sk_value.argtypes = [c_void_p, c_int]

        # int ASN1_STRING_length(ASN1_STRING *x);
        libssl.ASN1_STRING_length.restype = c_int
        libssl.ASN1_STRING_length.argtypes = [c_void_p]
        # unsigned char *ASN1_STRING_data(ASN1_STRING *x);
        libssl.ASN1_STRING_data.restype = c_char_p
        libssl.ASN1_STRING_data.argtypes = [c_void_p]
        # int ASN1_STRING_type(ASN1_STRING *x);
        libssl.ASN1_STRING_type.restype = c_int
        libssl.ASN1_STRING_type.argtypes = [c_void_p]
        # int ASN1_STRING_to_UTF8(unsigned char **out, ASN1_STRING *in);
        libssl.ASN1_STRING_to_UTF8.restype = c_int
        libssl.ASN1_STRING_to_UTF8.argtypes = [POINTER(c_char_p), c_void_p]
        # long ASN1_INTEGER_get(ASN1_INTEGER *a);
        libssl.ASN1_INTEGER_get.restype = c_long
        libssl.ASN1_INTEGER_get.argtypes = [c_void_p]
        # BIGNUM *ASN1_INTEGER_to_BN(ASN1_INTEGER *ai,BIGNUM *bn);
        libssl.ASN1_INTEGER_to_BN.restype = c_void_p
        libssl.ASN1_INTEGER_to_BN.argtypes = [c_void_p, c_void_p]
        # ASN1_GENERALIZEDTIME *ASN1_TIME_to_generalizedtime(ASN1_TIME *t, ASN1_GENERALIZEDTIME **out);
        libssl.ASN1_TIME_to_generalizedtime.restype = c_void_p
        libssl.ASN1_TIME_to_generalizedtime.argtypes = [c_void_p, c_void_p]
        # ??? No prototype for ASN1_GENERALIZEDTIME_free
        libssl.ASN1_GENERALIZEDTIME_free.restype = None
        libssl.ASN1_GENERALIZEDTIME_free.argtypes = [c_void_p]

        # void *PEM_ASN1_read_bio(d2i_of_void *d2i, const char *name, BIO *bp, void **x, pem_password_cb *cb, void *u);
        libssl.PEM_ASN1_read_bio.restype = c_void_p
        libssl.PEM_ASN1_read_bio.argtypes = [c_void_p, c_char_p, c_void_p, POINTER(c_void_p), c_void_p, c_void_p]

        # int OBJ_obj2nid(const ASN1_OBJECT *o);
        libssl.OBJ_obj2nid.restype = c_int
        libssl.OBJ_obj2nid.argtypes = [c_void_p]
        # const char *OBJ_nid2sn(int n);
        libssl.OBJ_nid2sn.restype = c_char_p
        libssl.OBJ_nid2sn.argtypes = [c_int]

        # const EVP_MD *EVP_get_digestbyname(const char *name);
        libssl.EVP_get_digestbyname.restype = c_void_p
        libssl.EVP_get_digestbyname.argtypes = [c_char_p]

        # DH *d2i_DHparams(DH **a,const unsigned char **pp, long length);
        libssl.d2i_DHparams.restype = c_void_p
        libssl.d2i_DHparams.argtypes = [POINTER(c_void_p), POINTER(c_void_p), c_long]
        # DH *DH_new(void);
        libssl.DH_new.restype = POINTER(C_DH)
        libssl.DH_new.argtypes = []
        # int DH_size(const DH *dh);
        libssl.DH_size.restype = c_int
        libssl.DH_size.argtypes = [POINTER(C_DH)]
        # void DH_free(DH *dh);
        libssl.DH_free.restype = None
        libssl.DH_free.argtypes = [c_void_p]
        # BIGNUM *BN_bin2bn(const unsigned char *s,int len,BIGNUM *ret);
        libssl.BN_bin2bn.restype = c_void_p
        libssl.BN_bin2bn.argtypes = [c_void_p, c_int, c_void_p]
        # char *BN_bn2hex(const BIGNUM *a);
        libssl.BN_bn2hex.restype = c_void_p   # Can't use c_char_p because we must free()
        libssl.BN_bn2hex.argtypes = [c_void_p]
        # void BN_free(BIGNUM *a);
        libssl.BN_free.restype = None
        libssl.BN_free.argtypes = [c_void_p]


libssl = LibSSL()


def _check(result, cls=TLSError):
    """
    Check if there are any OpenSSL errors pending, and if so, coalesce and
    raise them.  Otherwise, pass through result.
    """
    errors = []
    while libssl.ERR_peek_error():
        errors.append(py3_str(libssl.ERR_reason_error_string(libssl.ERR_get_error())))
    if errors:
        errstr = '; '.join(errors)
        if cls:
            raise cls(errstr)
        else:
            log.error('OpenSSL error during __del__: %s', errstr)
    return result



class Certificate(object):
    """
    An X.509 certificate.

    You will not instantiate these objects directly, but they will be returned
    from various :class:`TLSSocket` methods and properties.

    .. note::
       Certificate objects are presently read-only.
    """
    def __init__(self, x509, copy=False):
        # We free the X509 object in __del__ so we must own a reference to this
        # object.  So if necessary, pass copy=True
        if copy:
            x509 = libssl.X509_dup(x509)
            if x509 is None:
                raise ValueError('X509_dup failed: X509 certificate is invalid')
        self._x509 = cast(x509, POINTER(C_X509))
        self._parse_extensions()


    def __del__(self):
        libssl.X509_free(self._x509)


    def _parse_extensions(self):
        # Maps GeneralName type ids to dict key names
        types = ('othername', 'email', 'dns', 'x400', 'dirname', 'ediparty', 'uri', 'ipadd', 'rid')

        self._extensions = {}

        num_extensions = _check(libssl.X509_get_ext_count(self._x509))
        for i in range(num_extensions):
            ext = libssl.X509_get_ext(self._x509, i)
            name = libssl.X509_EXTENSION_get_object(ext)
            shortname = nativestr(libssl.OBJ_nid2sn(libssl.OBJ_obj2nid(name)))
            critical = libssl.X509_EXTENSION_get_critical(ext)
            extdict = self._extensions.setdefault(shortname, {'critical': critical})

            if shortname in ('subjectAltName',):
                names = _check(libssl.X509_get_ext_d2i(self._x509, NID_subject_alt_name, None, None))
                if not names:
                    continue
                for i in range(libssl.sk_num(names)):
                    name = cast(libssl.sk_value(names, i), POINTER(C_GENERAL_NAME))
                    if not name or name.contents.type < 0 or name.contents.type >= len(types):
                        continue
                    # Only support email, dns, and uri types right now (since
                    # all we can parse are ASN1 strings).
                    if name.contents.type not in (1, 2, 6):
                        continue
                    utf8 = c_char_p()
                    utf8_len = libssl.ASN1_STRING_to_UTF8(byref(utf8), name.contents.data)
                    value = py3_str(string_at(utf8, utf8_len), encoding='utf8')
                    libssl.CRYPTO_free(utf8)
                    extdict.setdefault(types[name.contents.type], []).append(value)
            else:
                # Indicate extension not supported yet
                self._extensions[shortname] = None


    @property
    def extensions(self):
        """
        A dictionary of X509 v3 extensions present in the certificate.

        The keys are the extension name (e.g. ``subjectAltName``), and each value
        is a dict mapping data type names (e.g. ``dns``) to a list of data values.

        .. note::
           Currently the only supported extension is ``subjectAltName``.  Other
           extensions will be present in the extensions dict, but their values
           will be None.
        """
        return self._extensions


    @property
    def subject(self):
        """
        An :class:`X509Name` for the entity the certificate belongs to.
        """
        name = _check(libssl.X509_get_subject_name(self._x509))
        return X509Name(name, self) if name else None


    @property
    def issuer(self):
        """
        An :class:`X509Name` for the entity that signed and issued the
        certificate.
        """
        name = _check(X509_get_issuer_name(self._x509))
        return X509Name(name, self) if name else None


    @property
    def version(self):
        """
        The version of the certificate (usually 2).
        """
        asn1_i = self._x509.contents.cert_info.contents.version
        return libssl.ASN1_INTEGER_get(asn1_i)


    @property
    def serial_number(self):
        """
        The serial number assigned to the certificate by the issuer (which must
        be unique per CA).
        """
        asn1_i = libssl.X509_get_serialNumber(self._x509)
        bignum = libssl.ASN1_INTEGER_to_BN(asn1_i, None)
        hex = libssl.BN_bn2hex(bignum)
        try:
            return int(cast(hex, c_char_p).value, 16)
        finally:
            libssl.BN_free(bignum)
            libssl.CRYPTO_free(hex)


    def _get_datetime_from_asn1time(self, time):
        # This logic borrowed from pyOpenSSL
        if libssl.ASN1_STRING_length(time) == 0:
            return
        elif libssl.ASN1_STRING_type(time) == V_ASN1_GENERALIZEDTIME:
            timestamp = libssl.ASN1_STRING_data(time)
        else:
            gt = libssl.ASN1_TIME_to_generalizedtime(time, None)
            if not gt:
                return
            timestamp = libssl.ASN1_STRING_data(gt)
            libssl.ASN1_GENERALIZEDTIME_free(gt)

        return datetime.strptime(timestamp, '%Y%m%d%H%M%SZ').replace(tzinfo=utc)


    @property
    def not_before(self):
        """
        A datetime object representing the date the certificate becomes valid.

        The datetime object is timezone-aware in UTC.
        """
        time = self._x509.contents.cert_info.contents.validity.contents.notBefore
        return self._get_datetime_from_asn1time(time)


    @property
    def not_after(self):
        """
        A datetime object representing the expiry date of the certificate.

        The datetime object is timezone-aware in UTC.
        """
        time = self._x509.contents.cert_info.contents.validity.contents.notAfter
        return self._get_datetime_from_asn1time(time)


    @property
    def expired(self):
        """
        True if the current time is outside the certificate's validity period.

        For convenience, if a certificate is not yet valid (because the current
        time is before :attr:`not_before`), this property will be True.
        """
        now = datetime.now(utc)
        return now >= self.not_before and self.not_after < now


    def digest(self, name='sha1'):
        """
        Generate a binary digest for the certificate.

        :param name: the name of the digest algorithm to use (e.g. ``md5``, ``sha1``,
                     ``sha256``, ``sha512``)
        :type name: str
        :returns: a byte string containing the binary digest
        """
        digest = libssl.EVP_get_digestbyname(name)
        if not digest:
            raise ValueError('no such digest "%s"' % name)
        value = create_string_buffer(64)  # EVP_MAX_MD_SIZE
        sz = c_int()
        _check(libssl.X509_digest(self._x509, digest, value, byref(sz)))
        return value.raw[:sz.value]


    def hexdigest(self, name='sha1'):
        """
        Generate a hex string digest for the certificate.

        :param name: see :meth:`digest`
        :type name: str
        :returns: a hex string of the digest
        """
        return py3_str(binascii.hexlify(self.digest(name)))


    def match_subject_name(self, name, wildcards=True):
        """
        Match the given name with either the subject's commonName or one of
        the subjectAltNames.

        :param name: the hostname to match
        :param wildcards: allow wildcards in the subject names
        :returns: the name that matched the supplied name, or None if no matches
                  were found.
        """
        alt_names = self._extensions.get('subjectAltName', {}).get('dns', [])
        all_cnames = ([self.subject.get('CN')] or []) + alt_names
        for cn in all_cnames:
            if (wildcards and fnmatch(name.lower(), cn.lower())) or name.lower() == cn.lower():
                return cn


class X509Name(dict):
    """
    Represents an X509 name element as a dictionary.

    Typical keys are:
        * ``C``: country
        * ``ST``: state
        * ``L``: city
        * ``O``: organization
        * ``OU``: organizational unit
        * ``CN``: common name (hostname)

    ``str(x509name)`` will return a single line representing all elements of the
    X509Name in an OpenSSL-specific format.

    .. note::
       X509Name objects are presently read-only.
    """
    # TODO: allow lookups by nid
    def __init__(self, x509name, cert):
        # For now, this is only used by X509 objects which we hold a reference
        # to which prevents their destruction.  So no need to dup() x509name.
        self._x509name = x509name
        self._cert = cert

        count = libssl.X509_NAME_entry_count(self._x509name)
        components = []
        for i in range(count):
            entry = libssl.X509_NAME_get_entry(self._x509name, i)
            # Extract name of entry
            name = libssl.X509_NAME_ENTRY_get_object(entry)
            shortname = nativestr(libssl.OBJ_nid2sn(libssl.OBJ_obj2nid(name)))
            # Extract UTF-8 encoded string from entry
            data = libssl.X509_NAME_ENTRY_get_data(entry)
            utf8 = c_char_p()
            utf8_len = libssl.ASN1_STRING_to_UTF8(byref(utf8), data)
            value = py3_str(string_at(utf8, utf8_len), encoding='utf8')
            libssl.CRYPTO_free(utf8)
            # Add to components.
            components.append((shortname, value))
        super(X509Name, self).__init__(components)


    def __str__(self):
        oneline = create_string_buffer(512)
        _check(libssl.X509_NAME_oneline(self._x509name, oneline, 512))
        return nativestr(oneline.value)

    def __repr__(self):
        return '<X509Name object "%s" at 0x%x>' % (str(self), id(self))


    def _cmp(self, other):
        return libssl.X509_NAME_cmp(self._x509name, other._x509name)

    def __eq__(self, other):
        return self._cmp(other) == 0

    def __lt__(self, other):
        return self._cmp(other) < 0

    def __le__(self, other):
        return self._cmp(other) <= 0

    def __gt__(self, other):
        return self._cmp(other) > 0

    def __ge__(self, other):
        return self._cmp(other) >= 0

    def __setitem__(self, attr, value):
        raise NotImplementedError('X509Name objects are currently read-only')


class TLSContext(object):
    """
    Encapsulates one or more :class:`TLSSocket` objects with common
    configuration (like certificates) and shared data (like sessions).

    By default, TLSSockets will each create their own TLSContext.  Sharing the
    same context allows things like SSL session resumption between multiple
    sockets.
    """

    # TODO: support SSL_CTX_set_tlsext_ticket_key_cb for key rotation

    _openssl_initialized = False
    # Mutex to prevent parallel initialization of OpenSSL.
    _openssl_init_lock = threading.Lock()
    _openssl_thread_locks = []
    _threading_locking_callback_c = None
    _threading_id_callback_c = None

    def __init__(self, protocol=None):
        # For _passwd_cb()
        self._key_passwd = None
        self._ticket_key = None
        self._local_cert = None
        self._verify_location = None
        self._dh_size = None

        TLSContext._openssl_init()

        method = libssl.SSLv23_method()
        self._ctx = libssl.SSL_CTX_new(method)

        # Keep a reference for __del__
        self._libssl = libssl

        # Initialize server-side session cache.
        _check(libssl.SSL_CTX_ctrl(self._ctx, SSL_CTRL_SET_SESS_CACHE_SIZE, 10240, None))
        _check(libssl.SSL_CTX_ctrl(self._ctx, SSL_CTRL_SET_SESS_CACHE_MODE, SSL_SESS_CACHE_BOTH, None))
        # We disable SSLv2.  It's vulnerable, deprecated, and I've never seen
        # anything that didn't work with SSLv3.  TODO: provide an interface to
        # set this.
        _check(libssl.SSL_CTX_ctrl(self._ctx, SSL_CTRL_OPTIONS, SSL_OP_ALL | SSL_OP_NO_SSLv2, None))
        mode = SSL_MODE_ENABLE_PARTIAL_WRITE | SSL_MODE_ACCEPT_MOVING_WRITE_BUFFER | SSL_MODE_AUTO_RETRY
        _check(libssl.SSL_CTX_ctrl(self._ctx, SSL_CTRL_MODE, mode, None))
        _check(libssl.SSL_CTX_set_verify(self._ctx, SSL_VERIFY_NONE, None))

        # Seems like a sensible default.
        self.set_ciphers('HIGH:MEDIUM:!ADH')

        # We need to keep a reference to the ctypes callback to keep it alive, but
        # use a WeakCallable to avoid the refcycle.
        self._passwd_callback_c = PASSWD_CALLBACK(kaa.WeakCallable(self._passwd_callback))
        _check(libssl.SSL_CTX_set_default_passwd_cb(self._ctx, self._passwd_callback_c))


    def __del__(self):
        if hasattr(self, '_libssl'):
            self._libssl.SSL_CTX_free(self._ctx)


    @classmethod
    def _openssl_init(cls):
        with cls._openssl_init_lock:
            if cls._openssl_initialized:
                return

            libssl.SSL_library_init()
            libssl.SSL_load_error_strings()
            libssl.ERR_load_ERR_strings()
            libssl.OPENSSL_add_all_algorithms_conf()

            # OpenSSL isn't thread-safe by default.  It maintains a number of
            # global shared data structures and rather than doing synchronization
            # internally, it leaves it up to the API caller to install a thread
            # locking callback.
            #
            # We can install Python functions as callbacks using ctypes.  This isn't
            # exactly ideal however because each time the locking callback is invoked
            # by OpenSSL, ctypes must reacquire the GIL before it can call back into
            # Python.  The GIL should be released quickly enough, but it still acts
            # as a funnel point for all thread switching with OpenSSL.
            #
            # Fortunately, the native Python SSL support uses OpenSSL, and as of
            # Python 2.6, it registers a proper locking callback with OpenSSL.
            # We imported _ssl above to give it the opportunity to install that
            # callback.  If an existing callback is installed, we do nothing.
            # Otherwise, we install the sub-optimal ctypes-based handler.
            if libssl.CRYPTO_get_locking_callback() == 0:
                # No locking callback is currently set, which must mean Python 2.5,
                # or some other extension has (strangely) removed the callback.
                # Initialize experimental ctypes threading support for OpenSSL by
                # registering thread id and thread lock callbacks.  A low-level
                # thread lock is created for each thread type OpenSSL needs (as
                # reported by CRYPTO_num_locks()) and a callback function
                # locks/unlocks as needed.
                log.warning('Using experimental ctypes-based OpenSSL thread support')
                n_locks = libssl.CRYPTO_num_locks()
                for i in range(n_locks):
                    cls._openssl_thread_locks.append(thread.allocate_lock())

                cls._threading_id_callback_c = ID_CALLBACK(cls._threading_id_callback)
                libssl.CRYPTO_set_id_callback(cls._threading_id_callback_c)
                cls._threading_locking_callback_c = LOCKING_CALLBACK(cls._threading_locking_callback)
                libssl.CRYPTO_set_locking_callback(cls._threading_locking_callback_c)
            cls._openssl_initialized = True


    @classmethod
    def _openssl_cleanup(cls):
        if cls._openssl_thread_locks:
            del cls._openssl_thread_locks[:]
        if libssl.CRYPTO_get_locking_callback() == cast(cls._threading_locking_callback_c, c_void_p).value:
            # At least the locking callback currently active is the one we set.
            # Assume the thread id callback is also ours (they should be
            # installed together) and remove them both.
            libssl.CRYPTO_set_id_callback(None)
            libssl.CRYPTO_set_locking_callback(None)
        cls._openssl_initialized = False


    @classmethod
    def _threading_id_callback(cls):
        return thread.get_ident()


    @classmethod
    def _threading_locking_callback(cls, mode, type, file, line):
        if mode & 0x01:  # CRYPTO_LOCK
            cls._openssl_thread_locks[type].acquire()
        else:
            cls._openssl_thread_locks[type].release()


    def _get_dh2048(self):
        dh2048_p = (0xe6,0xd0,0x50,0xed,0x83,0xeb,0xa2,0xea,0xa5,0x39,0xef,0x1d,0x00,0x53,0x53,0x13,
                    0x7f,0x5d,0xd5,0x55,0xf0,0x1d,0xfe,0xc0,0xe7,0xa8,0xf4,0x3a,0x96,0x62,0xcb,0xb6,
                    0x92,0x14,0x55,0x52,0x7d,0x47,0xd9,0xfb,0x12,0x28,0xe1,0xd6,0x2c,0xbd,0x1a,0x84,
                    0x7e,0x6b,0xd6,0x2c,0x28,0x75,0xdc,0xc2,0x2d,0xab,0xf5,0xf7,0xee,0x9f,0x12,0x8e,
                    0x9c,0xca,0xe1,0x9e,0x41,0xcd,0x60,0x8b,0xd5,0x2f,0x09,0xa6,0x8b,0x43,0x27,0xd9,
                    0xc7,0x43,0x8d,0x1f,0x5b,0x8b,0x08,0xaa,0xfc,0x19,0xa9,0x10,0x8e,0x35,0xf0,0x1d,
                    0x0e,0xbd,0xc1,0x7f,0xaa,0x80,0x31,0x38,0xcc,0xba,0xb3,0x7d,0x0c,0x18,0x6d,0x92,
                    0x56,0x71,0x54,0x2f,0x65,0xa6,0xea,0x33,0xcf,0x67,0xcf,0x1e,0x69,0x5c,0x2a,0x87,
                    0x69,0x26,0xdc,0xcb,0x48,0xa5,0x16,0xf3,0xa3,0x00,0xe6,0x29,0x82,0xf9,0xf0,0x21,
                    0x6c,0xfb,0xbf,0x2e,0xb0,0x81,0x8a,0x9a,0x22,0xd9,0x5d,0x9d,0x5e,0x28,0xee,0x8d,
                    0x66,0x60,0x14,0x86,0x54,0x39,0xf0,0xf2,0x41,0x3e,0x30,0xf9,0x27,0xc7,0xd3,0x3c,
                    0x79,0xcc,0xa0,0xcc,0x1f,0xa7,0x94,0x04,0xb1,0xd4,0x57,0xcd,0x1e,0xea,0x38,0xb8,
                    0x13,0x08,0x12,0xc1,0x85,0x54,0xc0,0x4c,0xa0,0x38,0x3c,0x7f,0x1b,0xce,0xf4,0xed,
                    0x49,0x1a,0xf7,0xd7,0xa6,0x6f,0x9f,0x2f,0x5b,0x91,0xf4,0x79,0x63,0x1a,0xc0,0x06,
                    0x66,0x99,0xee,0xab,0xf7,0x40,0x8a,0xc9,0x64,0x0f,0xae,0x26,0x59,0x5a,0x88,0xf6,
                    0x4d,0x29,0xf9,0xe8,0x3c,0xaa,0x9e,0x02,0x79,0x94,0x67,0xaa,0x60,0x26,0x3d,0x9b)
        return (c_byte*len(dh2048_p))(*dh2048_p), (c_byte*1)(0x02)


    def load_dh_params(self, file=None):
        """
        Load parameters for Ephemeral Diffie-Hellman.

        :param file: filename containing DH parameters in PEM format; if None,
                     hardcoded defaults are used
        :type file: str

        DH parameters are required to be loaded in order for EDH ciphers to be
        available.

        The size of the loaded DH parameters can be gotten from the
        :attr:`dh_size` property.
        """
        if file:
            try:
                btmp = _check(libssl.BIO_new_file(kwargs['dh'], 'r'), BIOError)
                try:
                    # PEM_read_bio_DHparams() is a macro that does this:
                    dh = _check(libssl.PEM_ASN1_read_bio(libssl.d2i_DHparams, 'DH PARAMETERS', btmp, None, None, None))
                    _check(libssl.SSL_CTX_ctrl(self._ctx, SSL_CTRL_SET_TMP_DH, 0, dh))
                    self._dh_size = libssl.DH_size(dh)
                    _check(libssl.DH_free(dh))
                finally:
                    _check(libssl.BIO_free_all(btmp), BIOError)
            except TLSError, e:
                raise TLSError('Could not load DH parameter file: %s' % e.args[0])

        else:
            dh2048_p, dh2048_g = self._get_dh2048()
            dh = _check(libssl.DH_new())
            dh.contents.p = _check(libssl.BN_bin2bn(dh2048_p, len(dh2048_p), None))
            dh.contents.g = _check(libssl.BN_bin2bn(dh2048_g, len(dh2048_g), None))
            _check(libssl.SSL_CTX_ctrl(self._ctx, SSL_CTRL_SET_TMP_DH, 0, dh))
            self._dh_size = libssl.DH_size(dh)
            _check(libssl.DH_free(dh))


    def _passwd_callback(self, buf, maxlen, verify, arg):
        passwd = py3_b(self._key_passwd)
        if callable(passwd):
            passwd = passwd()
        if not passwd:
            return 0
        memmove(buf, passwd, len(passwd))
        memmove(buf + len(passwd), '\x00', 1)
        return len(passwd)


    def load_cert_chain(self, cert, key=None, password=None):
        """
        Load a certificate chain and keys into the context.

        :param cert: filename for side certificate in PEM format
        :type cert: str
        :param key: filename for the private key for the given *cert* in PEM
                    format; if None and cert is not None, then it assumes the
                    key is contained in the cert file.
        :type key: str
        :param password: password to unlock the private key; if None and
                         cert is not None, then it assumes the key is not
                         protected by a password.  If arg is a callable,
                         it is passed no arguments and must return a string.

        For clients, a loaded certificate will be presented to the server
        when :meth:`TLSSocket.starttls_client` is called.  For servers, it is
        mandatory that a certificate is loaded.

        In either case, the certificate chain can be loaded by explicitly
        calling this method, or passing the ``cert``, ``key``, and ``password``
        kwargs in :meth:`TLSSocket.starttls_client` and
        :meth:`TLSSocket.starttls_server`.
        """
        self._key_passwd = password
        try:
            _check(libssl.SSL_CTX_use_certificate_chain_file(self._ctx, cert))
            if key is not None:
                _check(libssl.SSL_CTX_use_PrivateKey_file(self._ctx, key, X509_FILETYPE_PEM))
        except TLSError, e:
            raise TLSError('Invalid certificate and/or key: %s' % e.args[0])

        # There doesn't seem to be a way to get a X509 of the local certificate
        # we just loaded.  So we need to load it again using
        # PEM_read_bio_X509().  If we got this far, we shouldn't have problems
        # loading the certificate, because SSL_CTX_use_certificate_chain_file
        # will already have loaded it.
        btmp = _check(libssl.BIO_new_file(cert, 'r'), BIOError)
        try:
            # PEM_read_bio_X509() is a macro that does this:
            x509 = _check(libssl.PEM_ASN1_read_bio(libssl.d2i_X509, 'CERTIFICATE', btmp, None, self._passwd_callback_c, None))
            self._local_cert = Certificate(x509, copy=False)
        finally:
            _check(libssl.BIO_free_all(btmp), BIOError)


    def load_verify_locations(self, location=None):
        """
        Set the location of trusted certificates for certificate verification.

        :param location: path to a file containing concatenated certificates in
                         PEM format, or directory containing individual certificates
                         as files; if None, a location is auto-discovered based on
                         OpenSSL system configuration.
        :type location: str
        """
        dir = file = None
        if location:
            if os.path.isdir(location):
                dir = location
            elif os.path.exists(location):
                file = location
        else:
            dir = libssl.X509_get_default_cert_dir()
            if not os.path.isdir(dir):
                dir = None
            file = libssl.X509_get_default_cert_file()
            if not os.path.isfile(file):
                file = None

        if not dir and not file:
            raise TLSError('could not automatically determine CA certificates location')

        self._verify_location = dir or file
        if dir:
            libssl.SSL_CTX_load_verify_locations(self._ctx, None, dir)
        if file:
            libssl.SSL_CTX_load_verify_locations(self._ctx, file, None)

        if libssl.ERR_peek_error():
            err = libssl.ERR_get_error()
            if err != X509_R_CERT_ALREADY_IN_HASH_TABLE:
                raise TLSError(py3_stR(libssl.ERR_reason_error_string(err)))


    def set_ciphers(self, ciphers):
        """
        Set the available ciphers for sockets created with this context.

        :param ciphers: a string in the `OpenSSL cipher list format
                        <http://www.openssl.org/docs/apps/ciphers.html#CIPHER_LIST_FORMAT>`_.
        :type ciphers: str
        :raises: TLSError if no ciphers could be selected

        Once a :class:`TLSSocket` is connected, the :attr:`~TLSSocket.cipher`
        property can be checked to see which cipher was selected.
        """
        _check(libssl.SSL_CTX_set_cipher_list(self._ctx, ciphers))


    @property
    def ticket_key(self):
        """
        A 48 byte string used to encrypt session tickets.

        Setting this value enables the session ticket extension, and clients
        will receive session tickets during handshake.  Clients that present
        tickets encrypted using this key can resume SSL sessions without the
        need for server-side session cache.

        Clients don't need to do anything special to use the tickets except
        to set :attr:`~TLSSocket.reuse_sessions`.

        .. note::
           The actual key used to encrypt the tickets is derived from an
           HMAC of the local certificate using the given key.  This means it
           is necessary to first call :meth:`load_cert_chain`.
        """
        return self._ticket_key


    @ticket_key.setter
    def ticket_key(self, key):
        # Follow Apache's approach to generate the actual ticket key: use
        # an HMAC of the server certificate with the user-supplied secret.
        if not isinstance(key, bytes):
            raise TypeError('ticket key must be a byte string')
        elif len(key) < 48:
            raise ValueError('ticket key must be at least 48 bytes long')
        elif not self._local_cert:
            raise ValueError('must call load_cert_chain() first')
        self._ticket_key = key
        digest = self._local_cert.digest('sha384')
        private = hmac.new(key, digest, hashlib.sha384).digest()
        _check(libssl.SSL_CTX_ctrl(self._ctx, SSL_CTRL_SET_TLSEXT_TICKET_KEYS, 48, private))


    @property
    def dh_size(self):
        """
        The size of the currently loaded DH parameters in bits.
        """
        if self._dh_size is not None:
            return self._dh_size * 8

    @property
    def verify_location(self):
        """
        The location set (or discovered) by :meth:`load_verify_locations`

        If None, :meth:`load_verify_locations` was either never called or no
        location was auto-discovered.
        """
        return self._verify_location

    @property
    def local_cert(self):
        """
        A :class:`Certificate` object of the local certificate loaded by
        :meth:`load_cert_chain`.

        If None, :meth:`load_cert_chain` was never called (or had failed).
        """
        return self._local_cert


class TLSSession(object):
    """
    Represents the session state of a previously established TLS connection.
    """
    def __init__(self, session, peer_cert_chain, verified):
        self._libssl = libssl
        self._session = session
        self._peer_cert_chain = peer_cert_chain
        self._verified = verified


    def __del__(self):
        self._libssl.SSL_SESSION_free(self._session)


    @property
    def peer_cert_chain(self):
        """
        The saved :attr:`~TLSSocket.peer_cert_chain` from the established session.
        """
        return self._peer_cert_chain


    @property
    def verified(self):
        """
        Indicates whether the peer's certificate chain was properly verified.
        """
        return self._verified



class _SSLMemoryBIO(object):
    """
    Internal class representing an in-memory BIO pair, translating between
    application level (plaintext) data and network level (ciphertext) data.

    recv() and send() deal with the app layer via the OpenSSL SSL object,
    while bio_read() and bio_write() deal with the network layer via BIO
    objects.
    """
    def __init__(self, ctx):
        self._libssl = libssl
        self._ctx = ctx

        # Initialize these to None in case any allocation fails, __del__ and
        # the exception handler below will know what to free.
        self.ssl = self.into_ssl = self.from_ssl = None
        self.ssl = _check(libssl.SSL_new(ctx._ctx))
        try:
            self.into_ssl = _check(libssl.BIO_new(libssl.BIO_s_mem()))
            self.from_ssl = _check(libssl.BIO_new(libssl.BIO_s_mem()))
            _check(libssl.SSL_set_bio(self.ssl, self.into_ssl, self.from_ssl), BIOError)
        except:
            if self.into_ssl:
                self._libssl.BIO_free(self.into_ssl)
            if self.from_ssl:
                self._libssl.BIO_free(self.from_ssl)
            raise


    def __del__(self):
        if self.ssl:
            self._libssl.SSL_free(self.ssl)
            # These are already freed by SSL_free() because of SSL_set_bio()
            self.into_ssl = self.from_ssl = None


    def bio_read(self, maxsize=32768):
        """
        Return encrypted data destined toward the network.
        """
        chunk = create_string_buffer(maxsize)
        r = libssl.BIO_read(self.from_ssl, chunk, maxsize)
        self._handle_possible_bio_errors(self.from_ssl, r)
        # If the read failed, we will have raised by now.
        return chunk.raw[:r]


    def recv(self, maxsize=32768):
        """
        Return unencrypted application-level data.
        """
        chunk = create_string_buffer(maxsize)
        r = libssl.SSL_read(self.ssl, chunk, maxsize)
        self._handle_possible_ssl_errors(r)
        # If the read failed, we will have raised by now.
        return chunk.raw[:r]


    def bio_write(self, data):
        """
        Write encrypted data that came in from the network, and return the
        number of bytes successfully written.
        """
        r = libssl.BIO_write(self.into_ssl, data, len(data))
        self._handle_possible_bio_errors(self.into_ssl, r)
        # If the write failed, we will have raised by now.
        return r


    def send(self, data):
        """
        Write unencrypted application-level data, and return the number
        of bytes written.
        """
        r = libssl.SSL_write(self.ssl, data, len(data))
        self._handle_possible_ssl_errors(r)
        # If the write failed, we will have raised by now.
        return r

    def bio_shutdown(self):
        r = libssl.BIO_ctrl(self.into_ssl, BIO_C_SET_BUF_MEM_EOF_RETURN, 0, None)
        self._handle_possible_bio_errors(self.into_ssl, r)
        return r


    def shutdown(self):
        return  _check(libssl.SSL_shutdown(self.ssl)) > 0


    def do_handshake(self):
        r = libssl.SSL_do_handshake(self.ssl)
        self._handle_possible_ssl_errors(r)


    def is_handshake_done(self):
        return libssl.SSL_state(self.ssl) == SSL_ST_OK


    def _handle_possible_bio_errors(self, bio, r):
        if r > 0:
            # No error
            return r
        elif libssl.BIO_test_flags(bio, BIO_FLAGS_SHOULD_RETRY):
            if libssl.BIO_test_flags(bio, BIO_FLAGS_READ):
                raise WantReadError
            elif libssl.BIO_test_flags(bio, BIO_FLAGS_WRITE):
                raise WantWriteError
            elif libssl.BIO_test_flags(bio, BIO_FLAGS_IO_SPECIAL):
                # It's not obvious if this should ever happen on BIOs,
                # but raise just in case.
                raise BIOError('BIO_FLAGS_IO_SPECIAL')
            else:
                raise BIOError('unknown BIO failure')
        else:
            # OpenSSL doesn't want us to retry, but some error occurred.  Fall
            # back to standard SSL errors.
            return self._handle_possible_ssl_errors(r)


    def _handle_possible_ssl_errors(self, r):
        err = libssl.SSL_get_error(self.ssl, r)
        if err == SSL_ERROR_NONE:
            return r
        elif err == SSL_ERROR_WANT_READ:
            raise WantReadError
        elif err == SSL_ERROR_WANT_WRITE:
            raise WantWriteError
        elif err == SSL_ERROR_ZERO_RETURN:
            # SSL connection has been gracefully closed
            raise ZeroReturnError
        elif err == SSL_ERROR_SYSCALL:
            errno = get_errno()
            if errno != 0:
                raise IOError(errno, os.strerror(errno))
        else:
            # Eat all errors in the error stack and raise them.
            errors = []
            while libssl.ERR_peek_error():
                errors.append(py3_str(libssl.ERR_reason_error_string(libssl.ERR_get_error())))
            raise TLSError('; '.join(errors))



class TLSSocket(kaa.Socket):
    """
    TLSSocket extends :class:`~kaa.Socket` by adding SSL/TLS support.

    Until :meth:`~TLSSocket.starttls_client` or
    :meth:`~TLSSocket.starttls_server` is called, a TLSSocket operates like a
    standard :class:`~kaa.Socket`.  After TLS handshaking is initiated, data
    passed to/from the socket is transparently encrypted.

    TLSSockets that :meth:`~kaa.Socket.listen` will emit
    :attr:`~kaa.Socket.signals.new-client` with a TLSSocket object as the
    client.  This TLSSocket will share the same :class:`TLSContext` as the
    listening TLSSocket.
    """
    __kaasignals__ = {
        'tls':
            '''
            Emitted when a TLS handshake has been successfully completed.

            .. describe:: def callback(...)
            '''
    }


    def __init__(self, ctx=None, reuse_sessions=False):
        super(TLSSocket, self).__init__()
        self._ctx = None
        self._libssl = libssl
        # We need to keep a reference to the ctypes callback to keep it alive, but
        # use a WeakCallable to avoid the refcycle.
        self._user_verify_cb = None
        self._reuse_sessions = reuse_sessions
        self._session = None
        self._verify_callback_c = VERIFY_CALLBACK(kaa.WeakCallable(self._verify_callback))
        self._lock = threading.Lock()
        self._reset()
        if ctx:
            # Use the property setter to validate the argument.
            self.ctx = ctx


    def _make_new(self):
        """
        Make new instance of TLSSocket with the same TLSContext.

        Overwridden from super class for Socket._accept().
        """
        return self.__class__(self.ctx)


    def _reset(self):
        with self._lock:
            # Certificate chain for connected peer
            self._peer_cert_chain = None
            # Application level (plaintext) buffered data
            self._app_send_buffer = []
            # Remove reference to _SSLMemoryBIO instance so BIO/SSL objects get freed
            self._membio = None
            # True if a _SSLMemoryBIO.send() raised WantReadError and a read is pending
            self._write_blocked_on_read = False
            # True while performing initial handshake, False once it completes.
            self._handshaking = False
            # True once starttls_*() has been called.  When _tls_started == True and
            # _handshaking == False , negotiation has finished.
            self._tls_started = False
            # None when peer certificate verification hasn't been performed, True if
            # the peer's cert verified properly or if verify=False was passed to
            # starttls(), or False if the verification failed.
            self._verified = None
            # True if starttls_client() was called, False otherwise.
            self._is_client = False
            # kwargs passed to starttls_(client|server) for use by _check()
            self._starttls_kwargs = None
            # TLSSession object for the current session (if set)
            if not self._reuse_sessions:
                self._session = None
            # InProgress finished when starttls completes or fails.
            self._tls_ip = kaa.InProgress()


    def _shutdown_tls(self):
        self._membio.shutdown()
        self._flush_send_bio()


    def close(self, immediate=False, expected=True):
        if not immediate and self._tls_started:
            # Send (or rather queue for write) an SSL shutdown message to the
            # client to gracefully terminate the session.
            with self._lock:
                if self._membio:
                    self._shutdown_tls()
        return super(TLSSocket, self).close(immediate, expected)


    def _close(self):
        super(TLSSocket, self)._close()
        self._reset()


    def _is_read_connected(self):
        """
        Returns True if we're interested in read events.
        """
        # While doing initial handshake from ClientHello, we are interested
        # in read events internally, even if we have no listeners.
        return self._write_blocked_on_read or self._handshaking or super(TLSSocket, self)._is_read_connected()


    def _flush_send_bio(self):
        """
        Reads all pending network-level (encrypted) data from the memory BIO
        and queue them for write to the socket.
        """
        try:
            data = self._membio.bio_read()
        except WantReadError:
            pass
        except AttributeError:
            # self._membio is None, meaning the connection was closed.
            pass
        else:
            return super(TLSSocket, self).write(data)


    def _flush_recv_bio(self):
        """
        Pull all pending application-level (plaintext) data from the memory BIO
        and returns them.
        """
        appdata = []
        while True:
            try:
                appdata.append(self._membio.recv())
            except WantReadError:
                break
            except ZeroReturnError:
                self.close()
                break
            except TLSError, e:
                if not self._tls_ip.finished:
                    return self._handle_verify_failure(*sys.exc_info())

        # Reading might have generated some sort of protocol response (like a
        # ClientHello) that now requires transmission.
        self._flush_send_bio()
        return bl('').join(appdata)


    def _send_appdata(self, data):
        """
        Writes application-level (plaintext) data to the memory BIO and queues
        for write any encrypted data read from the other end of the membio.
        """
        total = 0
        encrypted = []
        while data:
            try:
                sent = self._membio.send(data)
            except WantReadError:
                self._write_blocked_on_read = True
                self._update_read_monitor()
                break
            else:
                if self._handshaking:
                    self._handshaking = False
                try:
                    chunk = self._membio.bio_read()
                except WantReadError:
                    pass
                else:
                    encrypted.append(chunk)
                data = data[sent:]
                total += sent
        if not encrypted:
            return total, None
        else:
            return total, super(TLSSocket, self).write(bl('').join(encrypted))


    # Useful for debug.
    #def _write(self, data):
    #    log.debug2('open: write len=%d data=%r...' % (len(data), data[:20]))
    #    return super(TLSSocket, self)._write(data)


    def write(self, data):
        """
        Write data to the socket, encrypting if necessary.

        :param data: the plaintext data to be sent to the peer
        :type data: str
        :returns: an :class:`~kaa.InProgress` as described in :meth:`kaa.IOChannel.write`

        Until :meth:`starttls_client` or :meth:`starttls_server` is called, the
        data passed is sent plaintext, just as it is with a standard
        :class:`~kaa.Socket`.  After either is called, TLS handshaking must be
        completed and verification passed (if enabled) before writing is allowed,
        after which the supplied data is encrypted before being sent to the peer.
        """
        # A write can require us to read from the socket, even when there are
        # no callbacks attached to 'read' or 'readline', such as in the case
        # when a handshake is still pending.  If this is the case,
        # _send_appdata() called below will cause _rmon to get registered while
        # the TLS layer needs data from the peer.
        if not self._tls_started:
            return super(TLSSocket, self).write(data)
        elif self._verified is None and self._starttls_kwargs['verify'] is not False:
            if not self._handshaking:
                # Handshake is done, verification needed but not performed.  It means
                # the peer didn't present a certificate, but we expected one.
                raise TLSError('peer did not present a certificate when one was expected')
            else:
                # Still handshaking, we can't write() yet!
                raise TLSError('TLS handshake has started but certificate not yet verified')
        elif self._verified is False:
            raise TLSError('peer certificate failed to verify')

        # XXX: this makes the interface asymmetric, but more convenient.  Is
        # that what we want?  If so, do it everywhere.
        data = py3_b(data)
        r, ip = self._send_appdata(data)
        if r < len(data):
            # Partial write, requeue what we couldn't write.
            self._app_send_buffer.insert(0, data[r:])
        return ip if ip else kaa.InProgress().finish(r)


    def _read(self, chunk):
        data = super(TLSSocket, self)._read(chunk)
        if not self._tls_started or not data:
            if self._tls_started and not self._tls_ip.finished:
                e = TLSProtocolError('Peer terminated connection before TLS handshake completed')
                self._tls_ip.throw(TLSProtocolError, e, None)
            return data

        if self._membio.bio_write(data) < len(data):
            # FIXME: can this even happen?  Twisted doesn't handle this case.
            raise NotImplementedError("BUG: we don't yet handle partial BIO writes. Please report this.")

        if self._write_blocked_on_read:
            # A previous write got a WantReadError.  Now that we've read, try to
            # write out any queued app-level data.
            self._write_blocked_on_read = False
            while self._app_send_buffer:
                chunk = self._app_send_buffer.pop(0)
                r, ip = self._send_appdata(chunk)
                if r < len(chunk):
                    # Partial write, requeue what we couldn't write.
                    self._app_send_buffer.insert(0, chunk[r:])
                    break

        plaintext = self._flush_recv_bio()
        if self._handshaking and self._membio.is_handshake_done():
            self._handshaking = False
            if self.session_reused and self._session:
                # We were able to reuse our session, so pull in the cert chain
                # and verified values stored in the session.
                self._peer_cert_chain = self._session._peer_cert_chain
                self._verified = self._session._verified
            elif self._reuse_sessions:
                # We're asked to re-use sessions, so store this session for
                # future re-use.
                self._session = self.session
            if not self._tls_ip.finished:
                self._tls_ip.finish(True)
            self._update_read_monitor()


        if plaintext and not self._is_read_connected() and not self._is_readline_connected():
            # There is decrypted (user) data from the socket, but no one external is wants
            # it yet.  So this data was decrypted as a consequence of our handshaking.
            # We can stuff this data into the read queue (from IOChannel superclass), so
            # subsequent user reads will consume it.
            if len(plaintext) + self.read_queue_used > self.queue_size + self.chunk_size:
                # This shouldn't happen in normal circumstances.  It's more of a sanity
                # check.
                raise TLSError('Read queue overflow')

            self._read_queue.write(plaintext)
            plaintext = None
            # We probably no longer need to read from the socket, given that we
            # have user data.
            self._update_read_monitor()


        if not plaintext:
            # We read data from the socket, but after passing through the BIO pair
            # there was no decrypted data.  So what we read was protocol traffic.
            # We signal to the underlying IOHandler that we want to continue
            # later by raising this.
            raise IOError(11, 'Resource temporarily unavailable')

        return plaintext


    def _handle_verify_failure(self, tp, exc, tb):
        self._tls_ip.throw(tp, exc, tb)
        self.close(immediate=True, expected=True)


    def _verify_callback(self, preverify_ok, x509_ctx):
        """
        Called back from OpenSSL.  Here we wrap up the lower level values
        and pass them along to the higher level verification callbacks
        (verify_cb or self.verify).
        """
        x509 = _check(libssl.X509_STORE_CTX_get_current_cert(x509_ctx))
        cert = Certificate(x509, copy=True)
        self._peer_cert_chain.insert(0, cert)

        if self._starttls_kwargs['verify'] is False:
            # Verification is explicitly disabled by the user
            libssl.X509_STORE_CTX_set_error(x509_ctx, X509_V_OK)
            return 1

        err = libssl.X509_STORE_CTX_get_error(x509_ctx) or None
        depth = libssl.X509_STORE_CTX_get_error_depth(x509_ctx)
        errmsg = libssl.X509_verify_cert_error_string(err) if err else None
        verify_func = self._user_verify_cb or self.verify
        try:
            verify_func(cert, depth, err, errmsg)
            # verify_func must raise to reject the certificate, so if we're here
            # it was accepted.
            libssl.X509_STORE_CTX_set_error(x509_ctx, X509_V_OK)
        except Exception:
            self._verified = False
            # Invoke _handle_verify_failure() in a OneShotTimer to avoid doing
            # too much work from this ctypes callback.
            kaa.OneShotTimer(self._handle_verify_failure, *sys.exc_info()).start(0)
            return 0

        if depth == 0 and self._verified is None:
            # We made it all the way to the peer cert without failing, so
            # we're considered verified now.
            self._verified = True
            # Again, use a timer to avoid invoking signal callbacks within the
            # ctypes callback.
            kaa.OneShotTimer(self.signals['tls'].emit).start(0)
        return 1


    @property
    def ctx(self):
        """
        The :class:`TLSContext` object associated with this TLSSocket.

        By default, a new context is created for each TLSSocket.  You can set
        this property or pass a :class:`TLSContext` object when creating the
        TLSSocket to share contexts between connections.

        .. note::
           For active connections that have completed handshaking, setting this
           property will have no effect until the next time :meth:`starttls_client`
           or :meth:`starttls_server` is called.
        """
        if self._ctx is None:
            self._ctx = TLSContext()
        return self._ctx


    @ctx.setter
    def ctx(self, value):
        if not isinstance(value, TLSContext):
            raise TypeError('value must be a TLSContext object')
        self._ctx = value


    @property
    def peer_cert_chain(self):
        """
        A list of :class:`Certificate` objects representing the certificate chain for
        the connected peer.

        The list is ordered such that the first element is the peer's certificate,
        and the last element is the top-level certificate authority.
        """
        return self._peer_cert_chain


    @property
    def verified(self):
        """
        The status of the peer's certificate chain verification.

        Possible values:
            * **None**: verification was not yet performed (e.g. TLS handshake
              has not yet occurred)
            * **False**: verification was performed and failed
            * **True**: peer certificate chain passed verfication.
        """
        return self._verified


    @property
    def verify_cb(self):
        """
        User-installable callback for peer certificate verification.

        .. describe:: def callback(cert, depth, err, errmsg)

           See :meth:`~TLSSocket.verify` for argument details.

        If a callback is set, it will be invoked for each certificate in the peer's
        chain *instead* of the :meth:`verify` method.
        """
        return self._user_verify_cb


    @verify_cb.setter
    def verify_cb(self, value):
        if not callable(value):
            raise TypeError('value must be callable')
        self._user_verify_cb = value


    @property
    def handshaked(self):
        """
        True when the SSL handshake has completed.
        """
        return self._tls_started and not self._handshaking


    @property
    def cipher(self):
        """
        The cipher negotiated with the peer.

        If no TLS handshake has been performed, this value is None.
        """
        if self._membio:
            return libssl.SSL_get_cipher_list(self._membio.ssl, 0)


    @property
    def session(self):
        """
        A :class:`TLSSession` object representing the session state for the
        current connection.

        This value can be set with an existing :class:`TLSSession` and later calls
        to :meth:`starttls_client` will attempt to reuse the session.
        """
        if self._session:
            # Object previously set, use that one.
            return self._session
        elif self._membio:
            s = libssl.SSL_get1_session(self._membio.ssl)
            if s:
                return TLSSession(s, self._peer_cert_chain, self._verified)


    @session.setter
    def session(self, s):
        if not isinstance(s, TLSSession):
            raise TypeError('session must be a TLSSession')
        self._session = s
        # XXX: should we raise if already connected?


    @property
    def session_reused(self):
        """
        True if the SSL session was able to be reused for this connection.
        """
        if not self._membio:
            return False
        return bool(libssl.SSL_ctrl(self._membio.ssl, SSL_CTRL_GET_SESSION_REUSED, 0, None))


    @property
    def reuse_sessions(self):
        """
        True if session state will be preserved between connections.

        SSL session resumption performs an abbreviated handshake if the server
        side recognizes the session id, or if the client presents a valid
        session ticket the server can decrypt.  This is allows substantially
        more efficient reconnections.

        This value is False by default.  If True, for clients, the session
        state will be perserved between subsequent :meth:`connect` and
        :meth:`starttls_client` calls.

        .. note::
           Currently, servers will always maintain a session cache and allow
           clients to attempt session resumption.

        It is possible to explicitly reuse sessions by saving and restoring
        the :attr:`session` property between connections (which also works
        across different TLSSocket instances, and across TLSContexts).
        """
        return self._reuse_sessions


    @reuse_sessions.setter
    def reuse_sessions(self, value):
        self._reuse_sessions = value


    @property
    def secure_renegotiation_support(self):
        """
        Indicates if the peer supports RFC5746 Secure Renegotiation.
        """
        return bool(libssl.SSL_ctrl(self._membio.ssl, SSL_CTRL_GET_RI_SUPPORT, 0, None))


    def verify(self, cert, depth, err, errmsg):
        """
        Verify one certificate in the peer's certificate chain.

        :param cert: the certificate in the chain currently being verified
        :type cert: :class:`Certificate`
        :param depth: the depth within the peer's certificate chain for the
                      certificate; the values are inverted such that 0 is the
                      peer's certificate, and increasing values walk up the
                      issuer chain.
        :type depth: int
        :param err: an error code indicating any pre-validation failures detected
                    by OpenSSL, or None if no errors were found.
        :type err: int or None
        :param errmsg: a human-readable string of *err*, or None if no errors
                       were found.
        :type errmsg: str or None
        :returns: anything if the certificate should be accepted, otherwise
                  it will raise an exception to reject it
        :raises: :class:`TLSVerificationError`

        If ``verify=True`` was passed to either :meth:`starttls_client` or
        :meth:`starttls_server`, this method is invoked for each certificate in
        the peer's chain to give it an opportunity to accept or reject it by
        raising :class:`TLSVerificationError`.

        Raising an exception will cause the exception to be thrown to the
        :class:`~kaa.InProgress` of a pending :meth:`starttls_client` or
        :meth:`starttls_server`.  The :attr:`verified` property will be False,
        and the socket will be immediately closed.

        The default behaviour requires the certificate is issued by a
        recognized CA (see :meth:`TLSContext.load_verify_locations`), the
        current time is within the certificate's validity period, and
        :meth:`Certificate.match_subject_name` succeeds given the hostname
        given to :meth:`~kaa.Socket.connect` (or ``cn`` kwarg passed to
        :meth:`starttls_client`)

        .. note::

           Subclasses may override this method to implement custom verification
           behaviour, but it may be more convenient to set the
           :attr:`verify_cb` property with a callback.
        """
        if err:
            raise TLSVerificationError(err, errmsg)
        if not err and depth == 0:
            # No errors so far and we made it all the way to the peer's cert.
            # Verify subject name now.
            host = self._starttls_kwargs['cn'] or self._reqhost
            if not cert.match_subject_name(host):
                raise TLSVerificationError(1000, 'Hostname "%s" does not match certificate' % host)


    def _starttls(self, **kwargs):
        self._starttls_kwargs = kwargs
        self._is_client = kwargs['client']
        self._handshaking = True
        self._peer_cert_chain = []
        self._update_read_monitor()

        # Accessing the ctx property causes a new context to be created if
        # necessary.
        ctx = self.ctx
        if not ctx.dh_size:
            if kwargs.get('dh'):
                ctx.load_dh_params(kwargs['dh'])
            elif not kwargs['client']:
                # openssl s_server will use hardcoded temp DH parameters if none are
                # specified, so we do the same in the spirit of Just Working.
                log.warning('Using default temp DH parameters')
                ctx.load_dh_params()

        if not ctx.local_cert:
            if kwargs['cert']:
                ctx.load_cert_chain(kwargs['cert'], kwargs.get('key'), kwargs.get('password'))
            elif not kwargs['client'] and not ctx.local_cert:
                # For clients cert is optional, but servers need it.
                raise ValueError('Certificate required by starttls_server() but none was set')

        if not ctx.verify_location and kwargs['verify']:
            # No verify location on this context.  Try auto-discovering.
            ctx.load_verify_locations()
            if not ctx.verify_location:
                # Still no location.  Verification is required but with no CA
                # certs it is impossible.
                raise TLSError('CA bundle not found but verification requested')

        if 'ticket_key' in kwargs and ctx.ticket_key != kwargs['ticket_key']:
            ctx.ticket_key = kwargs['ticket_key']

        self._membio = _SSLMemoryBIO(ctx)
        if kwargs['client']:
            libssl.SSL_set_connect_state(self._membio.ssl)
        else:
            libssl.SSL_set_accept_state(self._membio.ssl)
        libssl.SSL_set_verify(self._membio.ssl, SSL_VERIFY_NONE, self._verify_callback_c)
        if self._session:
            libssl.SSL_set_session(self._membio.ssl, self._session._session)

        self._tls_started = True
        if kwargs['client']:
            try:
                self._membio.do_handshake()
            except WantReadError:
                self._flush_send_bio()

        return self._tls_ip


    def starttls_client(self, cert=None, key=None, password=None, verify=True, cn=None, fingerprint=None):
        """
        Send a ClientHello to initiate SSL session negotiation.

        :param cert, key, password: corresponds to :meth:`TLSContext.load_cert_chain`
        :param verify: if True, the server must present a certificate and
                       must verify successfully until further communication is
                       allowed; if False, no server certificate verification
                       is done.
        :type verify: bool
        :param cn: the default verification function will verify that the server
                   presents a certificate with a commonName or subjectAltName
                   matching this value; if None, the hostname passed to connect()
                   is used instead.
        :type cn: str
        :param fingerprint: require the server's certificate to match the given
                            SHA1 hex digest
        :type fingerprint: str
        :returns: :class:`~kaa.InProgress` that finishes when TLS handshaking
                  succeeds or fails.  If the handshake fails, an exception is
                  thrown to the InProgress

        Before this method (or :meth:`~TLSSocket.starttls_server`) is invoked,
        a TLSSocket behaves like a standard :class:`~kaa.Socket`.
        """
        return self._starttls(client=True, cert=cert, key=key, password=password, verify=verify,
                              cn=cn, fingerprint=fingerprint)


    def starttls_server(self, cert=None, key=None, password=None, verify=False, dh=None, ticket_key=None):
        """
        Wait for a ClientHello before continuing communication.

        :param cert, key, password: corresponds to :meth:`TLSContext.load_cert_chain`
        :param verify: if True, the client must present a certificate and
                       must verify successfully until further communication is
                       allowed; if False, no client certificate verification
                       is done.
        :type verify: bool
        :param dh: filename for Diffie-Hellman parameters in PEM format, needed
                   for EDH ciphers.  If None, temporary DH params will be used.
        :type dh: str
        :param ticket_key: corresponds to :attr:`TLSContext.ticket_key`
        :type ticket_key: str
        :returns: :class:`~kaa.InProgress` that finishes when TLS handshaking
                  succeeds or fails.  If the handshake fails, an exception is
                  thrown to the InProgress

        Before this method (or :meth:`~TLSSocket.starttls_client`) is invoked,
        a TLSSocket behaves like a standard :class:`~kaa.Socket`.
        """
        return self._starttls(client=False, cert=cert, key=key, password=password,
                              verify=verify, dh=dh, ticket_key=ticket_key)


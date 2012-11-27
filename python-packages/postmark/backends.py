from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ImproperlyConfigured
from django.core import serializers
from django.conf import settings
import httplib2

try:
    import json                     
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        raise Exception('Cannot use django-postmark without Python 2.6 or greater, or Python 2.4 or 2.5 and the "simplejson" library')
        
from postmark.signals import post_send

# Settings
POSTMARK_API_KEY = getattr(settings, "POSTMARK_API_KEY", None)
POSTMARK_SSL = getattr(settings, "POSTMARK_SSL", False)
POSTMARK_TEST_MODE = getattr(settings, "POSTMARK_TEST_MODE", False)

POSTMARK_API_URL = ("https" if POSTMARK_SSL else "http") + "://api.postmarkapp.com/email"

class PostmarkMailSendException(Exception):
    """
    Base Postmark send exception
    """
    def __init__(self, value, inner_exception=None):
        self.parameter = value
        self.inner_exception = inner_exception
    def __str__(self):
        return repr(self.parameter)

class PostmarkMailUnauthorizedException(PostmarkMailSendException):
    """
    401: Unathorized sending due to bad API key
    """
    pass

class PostmarkMailUnprocessableEntityException(PostmarkMailSendException):
    """
    422: Unprocessable Entity - usually an exception with either the sender
    not having a matching Sender Signature in Postmark.  Read the message
    details for further information
    """
    pass
    
class PostmarkMailServerErrorException(PostmarkMailSendException):
    """
    500: Internal error - this is on the Postmark server side.  Errors are
    logged and recorded at Postmark.
    """
    pass

class PostmarkMessage(dict):
    """
    Creates a Dictionary representation of a Django EmailMessage that is suitable
    for submitting to Postmark's API. An Example Dicitionary would be:
    
        {
            "From" : "sender@example.com",
            "To" : "receiver@example.com",
            "Cc" : "copied@example.com",
            "Bcc": "blank-copied@example.com",
            "Subject" : "Test",
            "Tag" : "Invitation",
            "HtmlBody" : "<b>Hello</b>",
            "TextBody" : "Hello",
            "ReplyTo" : "reply@example.com",
            "Headers" : [{ "Name" : "CUSTOM-HEADER", "Value" : "value" }],
            "Attachments": [
                {
                    "Name": "readme.txt",
                    "Content": "dGVzdCBjb250ZW50",
                    "ContentType": "text/plain"
                },
                {
                    "Name": "report.pdf",
                    "Content": "dGVzdCBjb250ZW50",
                    "ContentType": "application/octet-stream"
                }
            ]
        }
    """
    
    def __init__(self, message, fail_silently=False):
        """
        Takes a Django EmailMessage and parses it into a usable object for
        sending to Postmark.
        """
        try:
            message_dict = {}
            
            message_dict["From"] = message.from_email
            message_dict["Subject"] = unicode(message.subject)
            message_dict["TextBody"] = unicode(message.body)
            
            message_dict["To"] = ",".join(message.to)
            
            if len(message.cc):
                message_dict["Cc"] = ",".join(message.cc)
            if len(message.bcc):
                message_dict["Bcc"] = ",".join(message.bcc)
            
            if isinstance(message, EmailMultiAlternatives):
                for alt in message.alternatives:
                    if alt[1] == "text/html":
                        message_dict["HtmlBody"] = unicode(alt[0])
            
            if message.extra_headers and isinstance(message.extra_headers, dict):
                if message.extra_headers.has_key("Reply-To"):
                    message_dict["ReplyTo"] = message.extra_headers.pop("Reply-To")
                    
                if message.extra_headers.has_key("X-Postmark-Tag"):
                    message_dict["Tag"] = message.extra_headers.pop("X-Postmark-Tag")
                    
                if len(message.extra_headers):
                    message_dict["Headers"] = [{"Name": x[0], "Value": x[1]} for x in message.extra_headers.items()]
            
            if message.attachments and isinstance(message.attachments, list):
                if len(message.attachments):
                    message_dict["Attachments"] = message.attachments
            
        except:
            if fail_silently:
                message_dict = {}
            else:
                raise
        
        super(PostmarkMessage, self).__init__(message_dict)

class PostmarkBackend(BaseEmailBackend):
    
    BATCH_SIZE = 500
    
    def __init__(self, api_key=None, api_url=None, api_batch_url=None, **kwargs):
        """
        Initialize the backend.
        """
        super(PostmarkBackend, self).__init__(**kwargs)
        
        self.api_key = api_key or POSTMARK_API_KEY
        self.api_url = api_url or POSTMARK_API_URL
        
        if self.api_key is None:
            raise ImproperlyConfigured("POSTMARK_API_KEY must be set in Django settings file or passed to backend constructor.")
    
    def send_messages(self, email_messages):
        """
        Sends one or more EmailMessage objects and returns the number of email
        messages sent.
        """
        if not email_messages:
            return
        
        num_sent = 0
        for message in email_messages:
            sent = self._send(PostmarkMessage(message, self.fail_silently))
            if sent:
                num_sent += 1
        return num_sent
    
    def _send(self, message):
        http = httplib2.Http()
        
        if POSTMARK_TEST_MODE:
            print 'JSON message is:\n%s' % json.dumps(message)
            return
        
        try:
            resp, content = http.request(self.api_url,
                body=json.dumps(message),
                method="POST",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-Postmark-Server-Token": self.api_key,
                })
        except httplib2.HttpLib2Error:
            if not self.fail_silently:
                return False
            raise
        
        if resp["status"] == "200":
            post_send.send(sender=self, message=message, response=json.loads(content))
            return True
        elif resp["status"] == "401":
            if not self.fail_silently:
                raise PostmarkMailUnauthorizedException("Your Postmark API Key is Invalid.")
        elif resp["status"] == "422":
            if not self.fail_silently:
                content_dict = json.loads(content)
                raise PostmarkMailUnprocessableEntityException(content_dict["Message"])
        elif resp["status"] == "500":
            if not self.fail_silently:
                PostmarkMailServerErrorException()
        
        return False
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from django.db import models
from itertools import izip_longest
from datetime import datetime
from pytz import timezone
import pytz
import iso8601

from postmark.signals import post_send

POSTMARK_DATETIME_STRING = "%Y-%m-%dT%H:%M:%S.%f"

TO_CHOICES = (
    ("to", _("Recipient")),
    ("cc", _("Carbon Copy")),
    ("bcc", _("Blind Carbon Copy")),
)

BOUNCE_TYPES = (
    ("HardBounce", _("Hard Bounce")),
    ("Transient", _("Transient")),
    ("Unsubscribe", _("Unsubscribe")),
    ("Subscribe", _("Subscribe")),
    ("AutoResponder", _("Auto Responder")),
    ("AddressChange", _("Address Change")),
    ("DnsError", _("DNS Error")),
    ("SpamNotification", _("Spam Notification")),
    ("OpenRelayTest", _("Open Relay Test")),
    ("Unknown", _("Unknown")),
    ("SoftBounce", _("Soft Bounce")),
    ("VirusNotification", _("Virus Notification")),
    ("ChallengeVerification", _("Challenge Verification")),
    ("BadEmailAddress", _("Bad Email Address")),
    ("SpamComplaint", _("Spam Complaint")),
    ("ManuallyDeactivated", _("Manually Deactivated")),
    ("Unconfirmed", _("Unconfirmed")),
    ("Blocked", _("Blocked")),
)

class EmailMessage(models.Model):
    message_id = models.CharField(_("Message ID"), max_length=40)
    submitted_at = models.DateTimeField(_("Submitted At"))
    status = models.CharField(_("Status"), max_length=150)
    
    to = models.CharField(_("To"), max_length=150)
    to_type = models.CharField(_("Type"), max_length=3, choices=TO_CHOICES)
    
    sender = models.CharField(_("Sender"), max_length=150)
    reply_to = models.CharField(_("Reply To"), max_length=150)
    subject = models.CharField(_("Subject"), max_length=150)
    tag = models.CharField(_("Tag"), max_length=150)
    text_body = models.TextField(_("Text Body"))
    html_body = models.TextField(_("HTML Body"))
    
    headers = models.TextField(_("Headers"))
    attachments = models.TextField(_("Attachments"))
    
    def __unicode__(self):
        return u"%s" % (self.message_id,)
    
    class Meta:
        verbose_name = _("email message")
        verbose_name_plural = _("email messages")
        
        get_latest_by = "submitted_at"
        ordering = ["-submitted_at"]

class EmailBounce(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    message = models.ForeignKey(EmailMessage, related_name="bounces", verbose_name=_("Message"))
    
    inactive = models.BooleanField(_("Inactive"))
    can_activate = models.BooleanField(_("Can Activate"))
    
    type = models.CharField(_("Type"), max_length=100, choices=BOUNCE_TYPES)
    description = models.TextField(_("Description"))
    details = models.TextField(_("Details"))
    
    bounced_at = models.DateTimeField(_("Bounced At"))
    
    def __unicode__(self):
        return u"Bounce: %s" % (self.message.to,)
    
    class Meta:
        verbose_name = _("email bounce")
        verbose_name_plural = _("email bounces")
        
        order_with_respect_to = "message"
        get_latest_by = "bounced_at"
        ordering = ["-bounced_at"]

@receiver(post_send)
def sent_message(sender, **kwargs):
    msg = kwargs["message"]
    resp = kwargs["response"]
    
    for recipient in (
        list(izip_longest(msg["To"].split(","), [], fillvalue='to')) +
        list(izip_longest(msg.get("Cc", "").split(","), [], fillvalue='cc')) +
        list(izip_longest(msg.get("Bcc", "").split(","), [], fillvalue='bcc'))):
        
        if not recipient[0]:
            continue

        emsg = EmailMessage(
            message_id=resp["MessageID"],
            submitted_at=iso8601.parse_date(resp["SubmittedAt"]).replace(tzinfo=None),
            status=resp["Message"],
            to=recipient[0],
            to_type=recipient[1],
            sender=msg["From"],
            reply_to=msg.get("ReplyTo", ""),
            subject=msg["Subject"],
            tag=msg.get("Tag", ""),
            text_body=msg["TextBody"],
            html_body=msg.get("HtmlBody", ""),
            headers=msg.get("Headers", ""),
            attachments=msg.get("Attachments", "")
        )
        emsg.save()

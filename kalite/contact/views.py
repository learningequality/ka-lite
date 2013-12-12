from annoying.decorators import render_to

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.http import HttpResponse,HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

import settings
from central.models import Organization
from contact.forms  import ContactForm, DeploymentForm, SupportForm, InfoForm, ContributeForm
from contact.models import *
from utils.django_utils import get_request_ip
from utils.mailchimp import mailchimp_subscribe


@render_to("contact/contact_thankyou.html")
def contact_thankyou(request):
    # Currently, just a static html page; no data needed.
    return {
    }


def contact_subscribe(request, email=None):

    email = email or getattr(request,request.method).get('email')
    if not email:
        raise Exception(_("Email not specified"))
        
    # Don't want to muck with mailchimp during testing (though I did validate this)
    if settings.DEBUG:
        return HttpResponse(_("We'll subscribe you via mailchimp when we're in RELEASE mode, %s, we swear!") % email)
    else:
        return HttpResponse(mailchimp_subscribe(email, settings.CENTRAL_SUBSCRIBE_URL))


@render_to("contact/contact_wizard.html")
def contact_wizard(request, type=""):
    """Contact form consists of a contact main portion, and three possible contact types (deployment, support, info).
    Here, we handle all the forms and save them into their parts."""

    # handle a submitted contact form
    if request.method == "POST":
        # Note that each form has a "prefix", which makes forms with entries
        #   of the same name avoid colliding with each other
        #
        # Note that these prefixes have to match those below in the "GET" section.
        contact_form = ContactForm(prefix="contact_form", data=request.POST)
        deployment_form = DeploymentForm(prefix="deployment_form", data=request.POST)
        support_form = SupportForm(prefix="support_form", data=request.POST)
        contribute_form = ContributeForm(prefix="contribute_form", data=request.POST)
        info_form = InfoForm(prefix="info_form", data=request.POST)

        if contact_form.is_valid():
            # Point to authenticated user
            if request.user.is_authenticated():
                contact_form.instance.user = request.user
            # Map over the field at the bottom of the form to the hidden form element.
            #   I couldn't find a better way to get this set up in the form, without
            #   making a giant HTML mess, other than this way.
            contact_form.instance.cc_email = bool(request.POST.get("hack_cc_email", False))

            # Deployment
            if contact_form.cleaned_data["type"] == CONTACT_TYPE_DEPLOYMENT:
                if deployment_form.is_valid():
                    return handle_contact(request, contact_form, deployment_form, settings.CENTRAL_DEPLOYMENT_EMAIL, "deployment")

            # Support
            elif contact_form.cleaned_data["type"] == CONTACT_TYPE_SUPPORT:
                if support_form.is_valid():
                    return handle_contact(request, contact_form, support_form, settings.CENTRAL_SUPPORT_EMAIL, "support")

            # Info
            elif contact_form.cleaned_data["type"] == CONTACT_TYPE_INFO:
                if info_form.is_valid():
                    return handle_contact(request, contact_form, info_form, settings.CENTRAL_INFO_EMAIL, "info")

            # Contribute
            elif contact_form.cleaned_data["type"] == CONTACT_TYPE_CONTRIBUTE:
                if contribute_form.is_valid():
                    # Send development inquiries to the development list
                    if contribute_form.cleaned_data["type"] == CONTRIBUTE_TYPE_DEVELOPMENT:
                        return handle_contact(request, contact_form, contribute_form, settings.CENTRAL_DEV_EMAIL, "contribute")
                    # Everything else must go to the info list
                    else:
                       return handle_contact(request, contact_form, contribute_form, settings.CENTRAL_INFO_EMAIL, "contribute")

            else:
                raise Exception(_("Unknown contact type: %s") % (contact_form.cleaned_data["type"]))

    # A GET request.  Create empty forms, fill in user details if available
    #   Auto-select the type, if relevant
    else:
        deployment_form = DeploymentForm(prefix="deployment_form")
        support_form = SupportForm(prefix="support_form")
        info_form = InfoForm(prefix="info_form")
        contribute_form = ContributeForm(prefix="contribute_form")

        if not request.user.is_authenticated():
            contact_form = ContactForm(
                prefix="contact_form",
                instance=Contact(
                    type=type,
                    ip=get_request_ip(request),
                ))
        
        else:
            # Use the user's information, if available
            if request.user.owned_organizations.count() > 0:
                org = request.user.owned_organizations.all()[0]
            elif request.user.organization_set.count() > 0:
                org = request.user.organization_set.all()[0]
            else:
                org = Organization()

            contact_form = ContactForm(
                prefix="contact_form",
                instance=Contact(
                    type=type,
                    user=request.user,
                    name="%s %s" % (request.user.first_name, request.user.last_name),
                    email=request.user.email,
                    org_name=org.name,
                    ip=get_request_ip(request),
                ))

    return {
        "central_contact_email": settings.CENTRAL_CONTACT_EMAIL,
        "wiki_url": settings.CENTRAL_WIKI_URL,
        'deployment_form' : deployment_form,
        'support_form' : support_form,
        'contribute_form' : contribute_form,
        'info_form' : info_form,
        'contact_form' : contact_form,
    }


def handle_contact(request, contact_form, details_form, list_email, email_template_prefix):
        # Save data to database
        contact_form.save()
        details_form.instance.contact = contact_form.instance
        details_form.save()

        # Send email
        context = {
            'contact':    contact_form.instance,
            'details': details_form.instance,
            'central_server_host': settings.CENTRAL_SERVER_HOST,
        }
        subject = '[KA Lite] %s'%render_to_string('contact/%s_subject.txt' % email_template_prefix, context)
        body = render_to_string('contact/%s_body.txt' % email_template_prefix, context)

        if contact_form.instance.cc_email:
            cc_email = [contact_form.instance.email]
        else:
            cc_email = []

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.CENTRAL_FROM_EMAIL,
            to=[list_email],
            cc=cc_email,
            headers = {'Reply-To': contact_form.instance.email}  # when we reply, sent to the 'sender'
        )
        email.send()
        
        return HttpResponseRedirect(reverse("contact_thankyou"))


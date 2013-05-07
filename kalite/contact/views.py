from annoying.decorators import render_to
from forms  import ContactForm, DeploymentForm, SupportForm, InfoForm
from models import Contact, Deployment, Support, Info
from central.models import Organization
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.http import HttpResponse,HttpResponseRedirect
from django.core.urlresolvers import reverse
from utils.mailchimp import mailchimp_subscribe

import settings

@render_to("contact/contact_thankyou.html")
def contact_thankyou(request):
    return {
    }


def contact_subscribe(request):
    
    email = getattr(request,request.method)['email']
    if not email:
        raise Exception("Email not specified")
    return HttpResponse(mailchimp_subscribe(email))
    
    
@render_to("contact/contact_wizard.html")
def contact_wizard(request, type=""):
    """Contact form consists of a contact main portion, and three possible contact types (deployment, support, info).
    Here, we handle all the forms and save them into their parts."""
    
    # handle a submitted contact form
    if request.method == "POST":
        contact_form = ContactForm(prefix="cf", data=request.POST)
        deployment_form = DeploymentForm(prefix="df", data=request.POST)
        support_form = SupportForm(prefix="sf", data=request.POST)
        info_form = InfoForm(prefix="if", data=request.POST)

        if contact_form.is_valid():
            # Point to authenticated user
            if request.user.is_authenticated():
                contact_form.instance.user = request.user
            # Map over the field at the bottom of the form to the hidden form element (laziness!)
            contact_form.instance.cc_email = request.POST["hack_cc_email"]
                
            # Deployment
            if contact_form.cleaned_data["type"]  ==Contact.CONTACT_TYPE_DEPLOYMENT:
                if deployment_form.is_valid():
                    return handle_contact(request, contact_form, deployment_form, settings.CENTRAL_DEPLOYMENT_EMAIL, "deployment")

            # Support
            elif contact_form.cleaned_data["type"]==Contact.CONTACT_TYPE_SUPPORT:
                if support_form.is_valid():
                    return handle_contact(request, contact_form, support_form, settings.CENTRAL_SUPPORT_EMAIL, "support")
                    
            # Info
            elif contact_form.cleaned_data["type"]==Contact.CONTACT_TYPE_INFO:
                if info_form.is_valid():
                    return handle_contact(request, contact_form, info_form, settings.CENTRAL_INFO_EMAIL, "info")

            else:
                raise Exception("Unknown contact type: %s"%(contact_form.cleaned_data["type"]))
    
    # A GET request.  Create empty forms, fill in user details if available
    #   Auto-select the type, if relevant
    else:
        deployment_form = DeploymentForm(prefix="df")
        support_form = SupportForm(prefix="sf")
        info_form = InfoForm(prefix="if")
        
        # Use the user's information, if available
        if request.user.is_authenticated():
            if request.user.owned_organizations.count()>0:
                org = request.user.owned_organizations.get()
            elif request.user.organization_set.count()>0:
                org = request.user.organization_set.get()
            else:
                org = Organization()
            
            contact_form = ContactForm(prefix="cf", instance=Contact(type=type, user=request.user, name="%s %s"%(request.user.first_name, request.user.last_name), email=request.user.email, org_name=org.name, org_url=org.url))
        else:
            contact_form = ContactForm(prefix="cf", instance=Contact(type=type))

    return {
        "central_contact_email": settings.CENTRAL_CONTACT_EMAIL,
        "wiki_url": settings.CENTRAL_WIKI_URL,
        'deployment_form' : deployment_form,
        'support_form' : support_form,
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
        subject = '[KA Lite] %s'%render_to_string('contact/%s_subject.txt'%email_template_prefix, context)
        body = render_to_string('contact/%s_body.txt'%email_template_prefix, context)

        if contact_form.instance.cc_email:
            cc_email = [contact_form.instance.email]
        else:
            cc_email = []
            
        email = EmailMessage(subject=subject, body=body, from_email=settings.CENTRAL_FROM_EMAIL,
                    to=[list_email], cc=cc_email, headers = {'Reply-To': contact_form.instance.email})
        email.send()
        return HttpResponseRedirect(reverse("contact_thankyou"))


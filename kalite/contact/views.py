from annoying.decorators import render_to
from forms  import ContactForm, DeploymentForm, SupportForm, InfoForm
from models import Contact, Deployment, Support, Info
from django.core.mail import send_mail

import settings

@render_to("contact/contact_thankyou.html")
def contact_thankyou(request):
    return {
    }

@render_to("contact/contact_wizard.html")
def contact_wizard(request):
    """Contact form consists of a contact main portion, and three possible contact types (deployment, support, info).
    Here, we handle all the forms and save them into their parts."""
    
    # handle a submitted contact form
    if request.method == "POST":
        contact_form = ContactForm(data=request.POST)
        deployment_form = DeploymentForm(data=request.POST)
        support_form = SupportForm(data=request.POST)
        info_form = InfoForm(data=request.POST)
        
        if contact_form.is_valid():
            # Deployment
            if contact_form.cleaned_data["type"]  ==Contact.CONTACT_TYPE_DEPLOYMENT:
                if deployment_form.is_valid():
                    handle_deployment(request)

            # Support
            elif contact_form.cleaned_data["type"]==Contact.CONTACT_TYPE_SUPPORT:
                if support_form.is_valid():
                    raise Exception('Support not yet implemented')
                    
            # Info
            elif contact_form.cleaned_data["type"]==Contact.CONTACT_TYPE_INFO:
                if info_form.is_valid():
                    raise Exception('Support not yet implemented')
                    
            else:
                raise Exception("Unknown contact type: %s"%(contact_form.cleaned_data["type"]))
    
    # A GET request.  Create empty forms, fill in user details if available
    else:
        deployment_form = DeploymentForm()
        support_form = SupportForm()
        info_form = InfoForm()
        if request.user.is_authenticated():
            contact_form = ContactForm(user=request.user, name=request.user.name)
        else:
            contact_form = ContactForm()

    return {
        "central_contact_email": settings.CENTRAL_CONTACT_EMAIL,
        "wiki_url": settings.CENTRAL_WIKI_URL,
        'deployment_form' : deployment_form,
        'support_form' : support_form,
        'info_form' : info_form,
        'contact_form' : contact_form,
    }
    
    
def handle_deployment(request):
        # Save data to database
        contact_form.save()
        deployment_form.instance.contact = contact_form.instance
        deployment_form.save()
        
        # Send email
        to_email = "ben@learningequality.org"
        context = {
            'contact_form':    contact_form,
            'deployment_form': deployment_form,
            'central_server_host': settings.CENTRAL_SERVER_HOST,
        }
        subject = render_to_string('contact/deployment_subject.txt', context)
        body = render_to_string('contact/deployment_body.txt', context)

        email = EmailMessage(subject, body, settings.CENTRAL_SERVER_HOST,
                    [contact_form.instance.email], [],
                    headers = {'Reply-To': contact_form.instance.email})
        email.send()
        return HttpResponseRedirect(reverse("contact_thankyou"))

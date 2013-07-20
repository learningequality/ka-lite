"""
Views which allow users to create and activate accounts.

"""

import copy

from django.contrib import messages
from django.contrib.auth import logout as auth_logout, views as auth_views, REDIRECT_FIELD_NAME
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

import settings
from central.forms import OrganizationForm
from central.models import Organization
from contact.views import contact_subscribe
from registration.backends import get_backend
from securesync.models import Zone
from utils.decorators import central_server_only
from utils.mailchimp import mailchimp_subscribe


@central_server_only
def complete(request, *args, **kwargs):
    messages.success(request, "Congratulations! Your account is now active. To get started, "
        + "login to the central server below, to administer organizations and zones.")
    return redirect("auth_login")


@central_server_only
def activate(request, backend,
             template_name='registration/activate.html',
             success_url=None, extra_context=None, **kwargs):
    """
    Activate a user's account.

    The actual activation of the account will be delegated to the
    backend specified by the ``backend`` keyword argument (see below);
    the backend's ``activate()`` method will be called, passing any
    keyword arguments captured from the URL, and will be assumed to
    return a ``User`` if activation was successful, or a value which
    evaluates to ``False`` in boolean context if not.

    Upon successful activation, the backend's
    ``post_activation_redirect()`` method will be called, passing the
    ``HttpRequest`` and the activated ``User`` to determine the URL to
    redirect the user to. To override this, pass the argument
    ``success_url`` (see below).

    On unsuccessful activation, will render the template
    ``registration/activate.html`` to display an error message; to
    override thise, pass the argument ``template_name`` (see below).

    **Arguments**

    ``backend``
        The dotted Python import path to the backend class to
        use. Required.

    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context. Optional.

    ``success_url``
        The name of a URL pattern to redirect to on successful
        acivation. This is optional; if not specified, this will be
        obtained by calling the backend's
        ``post_activation_redirect()`` method.

    ``template_name``
        A custom template to use. This is optional; if not specified,
        this will default to ``registration/activate.html``.

    ``\*\*kwargs``
        Any keyword arguments captured from the URL, such as an
        activation key, which will be passed to the backend's
        ``activate()`` method.

    **Context:**

    The context will be populated from the keyword arguments captured
    in the URL, and any extra variables supplied in the
    ``extra_context`` argument (see above).

    **Template:**

    registration/activate.html or ``template_name`` keyword argument.

    """
    backend = get_backend(backend)
    account = backend.activate(request, **kwargs)

    if account:
        if success_url is None:
            to, args, kwargs = backend.post_activation_redirect(request, account)
            return redirect(to, *args, **kwargs)
        else:
            return redirect(success_url)

    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    return render_to_response(template_name,
                              kwargs,
                              context_instance=context)

@central_server_only
@transaction.commit_on_success
def register(request, backend, success_url=None, form_class=None,
             disallowed_url='registration_disallowed',
             template_name='registration/registration_form.html',
             extra_context=None):
    """
    Allow a new user to register an account.

    The actual registration of the account will be delegated to the
    backend specified by the ``backend`` keyword argument (see below);
    it will be used as follows:

    1. The backend's ``registration_allowed()`` method will be called,
       passing the ``HttpRequest``, to determine whether registration
       of an account is to be allowed; if not, a redirect is issued to
       the view corresponding to the named URL pattern
       ``registration_disallowed``. To override this, see the list of
       optional arguments for this view (below).

    2. The form to use for account registration will be obtained by
       calling the backend's ``get_form_class()`` method, passing the
       ``HttpRequest``. To override this, see the list of optional
       arguments for this view (below).

    3. If valid, the form's ``cleaned_data`` will be passed (as
       keyword arguments, and along with the ``HttpRequest``) to the
       backend's ``register()`` method, which should return the new
       ``User`` object.

    4. Upon successful registration, the backend's
       ``post_registration_redirect()`` method will be called, passing
       the ``HttpRequest`` and the new ``User``, to determine the URL
       to redirect the user to. To override this, see the list of
       optional arguments for this view (below).

    **Required arguments**

    None.

    **Optional arguments**

    ``backend``
        The dotted Python import path to the backend class to use.

    ``disallowed_url``
        URL to redirect to if registration is not permitted for the
        current ``HttpRequest``. Must be a value which can legally be
        passed to ``django.shortcuts.redirect``. If not supplied, this
        will be whatever URL corresponds to the named URL pattern
        ``registration_disallowed``.

    ``form_class``
        The form class to use for registration. If not supplied, this
        will be retrieved from the registration backend.

    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``success_url``
        URL to redirect to after successful registration. Must be a
        value which can legally be passed to
        ``django.shortcuts.redirect``. If not supplied, this will be
        retrieved from the registration backend.

    ``template_name``
        A custom template to use. If not supplied, this will default
        to ``registration/registration_form.html``.

    **Context:**

    ``form``
        The registration form.

    Any extra variables supplied in the ``extra_context`` argument
    (see above).

    **Template:**

    registration/registration_form.html or ``template_name`` keyword
    argument.

    """
    backend = get_backend(backend)
    if not backend.registration_allowed(request):
        return redirect(disallowed_url)
    if form_class is None:
        form_class = backend.get_form_class(request)

    do_subscribe = request.REQUEST.get("email_subscribe") == "on"

    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        org_form = OrganizationForm(data=request.POST, instance=Organization())

        # Could register
        if form.is_valid() and org_form.is_valid():
            assert form.cleaned_data.get("username") == form.cleaned_data.get("email"), "Should be set equal in the call to clean()"

            try:
                # Create the user
                new_user = backend.register(request, **form.cleaned_data)

                # Add an org.  Must create org before adding user.
                org_form.instance.owner = new_user
                org_form.save()
                org = org_form.instance
                org.users.add(new_user)

                # Now add a zone, and link to the org
                zone = Zone(name=org_form.instance.name + " Default Zone")
                zone.save()
                org.zones.add(zone)

                # Finally, try and subscribe the user to the mailing list
                # (silently; don't return anything to the user)
                if do_subscribe:
                    contact_subscribe(request, form.cleaned_data['email'])  # no "return"
                org.save()

                if success_url is None:
                    to, args, kwargs = backend.post_registration_redirect(request, new_user)
                    return redirect(to, *args, **kwargs)
                else:
                    return redirect(success_url)

            except IntegrityError as e:
                if e.message=='column username is not unique':
                    form._errors['__all__'] = _("An account with this email address has already been created.  Please login at the link above.")
                else:
                    raise e

    # GET, not POST
    else:
        form = form_class()
        org_form = OrganizationForm()

    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    return render_to_response(
        template_name,
        {
            'form': form,
            "org_form" : org_form,
            "subscribe": do_subscribe,
        },
        context_instance=context,
    )


@central_server_only
def login_view(request, *args, **kwargs):
    """
    Force lowercase of the username.

    Since we don't want things to change to the user (if something fails),
    we should try the new way first, then fall back to the old way
    """
    if request.method=="POST":
        users = User.objects.filter(username__iexact=request.POST["username"])
        nusers = users.count()
    
        # Coerce
        if nusers == 1 and users[0].username != request.POST["username"]:
            request.POST = copy.deepcopy(request.POST)
            request.POST['username'] = request.POST['username'].lower()
    
    extra_context = {
        "redirect": {
            "name": REDIRECT_FIELD_NAME,
            "url": request.REQUEST.get("next", reverse('org_management')),
        }
    }
    kwargs["extra_context"] = extra_context

    return auth_views.login(request, *args, **kwargs)


@central_server_only
def logout_view(request):
    auth_logout(request)
    return redirect("homepage")

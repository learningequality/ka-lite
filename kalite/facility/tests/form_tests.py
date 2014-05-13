"""
"""
import string

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.test import TestCase

from ..forms import FacilityUserForm
from ..models import Facility, FacilityUser, FacilityGroup
from kalite.testing import KALiteTestCase
from securesync.models import Zone, Device, DeviceMetadata


class FacilityTestCase(KALiteTestCase):

    def setUp(self):
        super(FacilityTestCase, self).setUp()
        self.facility = Facility.objects.create(name='testfac')
        self.group = FacilityGroup.objects.create(name='testgroup', facility=self.facility)
        self.admin = User.objects.create(username='testadmin',password=make_password('insecure'))
        self.data = {
            'username': u'testuser',
            'first_name': u'fn',
            'facility': self.facility.id,
            'group': self.group.id,
            'is_teacher': False,
            'default_language': 'en',
            'password_first': 'k' * settings.PASSWORD_CONSTRAINTS['min_length'],
            'password_recheck': 'k' * settings.PASSWORD_CONSTRAINTS['min_length'],
        }


class UserRegistrationTestCase(FacilityTestCase):

    def test_facility_user_form_works(self):
        """Valid password should work"""
        response = self.client.post(reverse('add_facility_student'), self.data)
        self.assertNotIn("errorlist", response.content, "Must be no form errors")
        self.assertEqual(response.status_code, 302, "Status code must be 302")

        FacilityUser.objects.get(username=self.data['username']) # should not raise error

    def test_admin_and_user_no_common_username(self):
        """Post as username"""
        self.data['username'] = self.admin.username
        response = self.client.post(reverse('add_facility_student'), self.data)
        self.assertEqual(response.status_code, 200, "Status code must be 200")
        self.assertFormError(response, 'form', 'username', 'The specified username is unavailable. Please choose a new username and try again.')

    def test_password_length_valid(self):
        response = self.client.post(reverse('add_facility_student'), self.data)
        self.assertNotIn("errorlist", response.content, "Must be no form errors")
        self.assertEqual(response.status_code, 302, "Status code must be 302")

        FacilityUser.objects.get(username=self.data['username']) # should not raise error

    def test_password_length_enforced(self):
        # always make passwd shorter than passwd min length setting
        self.data['password_first'] = self.data['password_recheck'] =  self.data['password_first'][:settings.PASSWORD_CONSTRAINTS['min_length']-1]

        response = self.client.post(reverse('add_facility_student'), self.data)
        self.assertEqual(response.status_code, 200, "Status code must be 200")
        self.assertFormError(response, 'form', 'password_first', "Password should be at least %d characters." % settings.PASSWORD_CONSTRAINTS['min_length'])

    def test_only_ascii_letters_allowed(self):
        self.data['password_first'] = self.data['password_recheck'] = string.whitespace.join([self.data['password_first']] * 2)

        response = self.client.post(reverse('add_facility_student'), self.data)
        self.assertNotIn("errorlist", response.content, "Must be no form errors")
        self.assertEqual(response.status_code, 302, "Status code must be 302")

        FacilityUser.objects.get(username=self.data['username']) # should not raise error


class DuplicateFacilityNameTestCase(FacilityTestCase):

    def test_duplicate_facility_name(self):
        with self.assertRaisesMessage(ValidationError, "'name'") as ve:
            fac = Facility(name=self.facility.name)
            fac.full_clean()

    def test_nonduplicate_facility_name(self):
        fac = Facility(name=self.facility.name + "-different")
        fac.full_clean()
        fac.save()


class DuplicateFacilityGroupTestCase(FacilityTestCase):

    def test_duplicate_group_name(self):
        with self.assertRaisesMessage(ValidationError, "'name'") as ve:
            gr = FacilityGroup(name=self.group.name, facility=self.facility)
            gr.full_clean()

    def test_duplicate_group_name_in_different_facility(self):
        """Group need only be unique within a facility, not across them."""
        different_fac = Facility(name=self.facility.name + "-different")
        different_fac.save()
        gr = FacilityGroup(name=self.group.name, facility=different_fac)
        gr.full_clean()
        gr.save()

    def test_nonduplicate_group_name(self):
        gr = FacilityGroup(name=self.group.name + "-different", facility=self.facility)
        gr.full_clean()
        gr.save()


class DuplicateFacilityUserTestCase(FacilityTestCase):

    def setUp(self):
        super(DuplicateFacilityUserTestCase, self).setUp()

    def test_form_works_student(self):
        """Make a student"""
        self.data['is_teacher'] = False
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertTrue(user_form.is_valid(), "Form must be valid; instead: errors (%s)" % user_form.errors)
        user_form.instance.set_password(user_form.cleaned_data["password_first"])
        user_form.save()

    def test_form_works_teacher(self):
        """Make a teacher"""
        self.data['is_teacher'] = True
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertTrue(user_form.is_valid(), "Form must be valid; instead: errors (%s)" % user_form.errors)
        user_form.instance.set_password(user_form.cleaned_data["password_first"])
        user_form.save()

    def test_form_duplicate_name_student_teacher(self):
        """Basic test that duplicate name causes error on first submission, not on second (with warned=True)"""

        # Works for the student
        self.data['is_teacher'] = False
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertTrue(user_form.is_valid(), "Form must be valid; instead: errors (%s)" % user_form.errors)
        user_form.instance.set_password(user_form.cleaned_data["password_first"])
        user_form.save()

        # Fails for the teacher
        self.data['is_teacher'] = True
        self.data['username'] += '-different'
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertFalse(user_form.is_valid(), "Form must NOT be valid.")
        self.assertIn('1 user(s)', user_form.errors['__all__'][0], "Error message must contain # of users")

        # Succeeds if warned=True
        self.data['warned'] = True
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertTrue(user_form.is_valid(), "Form must be valid; instead: errors (%s)" % user_form.errors)
        user_form.instance.set_password(user_form.cleaned_data["password_first"])
        user_form.save()

    def test_form_duplicate_name_different_facility(self):
        """Check that duplicate names on different facilities fails to validate."""

        # Works for the student
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertTrue(user_form.is_valid(), "Form must be valid; instead: errors (%s)" % user_form.errors)
        user_form.instance.set_password(user_form.cleaned_data["password_first"])
        user_form.save()

        # Works for a student with the same username and same name, different zone.
        new_fac = Facility(name="test")
        new_fac.save()
        self.data['facility'] = new_fac
        self.data['username'] += '-different'
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertFalse(user_form.is_valid(), "Form must NOT be valid.")
        self.assertIn('1 user(s)', user_form.errors['__all__'][0], "Error message must contain # of users")

    def test_form_duplicate_username_different_facility(self):
        """Check that duplicate usernames on different facilities fails to validate."""

        # Works for the student
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertTrue(user_form.is_valid(), "Form must be valid; instead: errors (%s)" % user_form.errors)
        user_form.instance.set_password(user_form.cleaned_data["password_first"])
        user_form.save()

        # Works for a student with the same username and same name, different zone.
        new_fac = Facility(name="test")
        new_fac.save()
        self.data['facility'] = new_fac
        self.data['first_name'] += '-different'
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertFalse(user_form.is_valid(), "Form must NOT be valid.")
        self.assertIn('A user with this username already exists.', user_form.errors['username'][0], "Error message must contain # of users")

    def test_form_duplicate_name_count(self):
        """Should have the proper duplicate user name count."""

        self.test_form_duplicate_name_student_teacher()  # set up 2 users

        # Fails for the teacher
        self.data['warned'] = False
        self.data['username'] += '-different'
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertFalse(user_form.is_valid(), "Form must NOT be valid.")
        self.assertIn('2 user(s)', user_form.errors['__all__'][0], "Error message must contain # of users")

    def test_form_duplicate_name_list(self):
        """User list with the same name should only appear IF form has admin_access==True"""

        # Works for one user
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertTrue(user_form.is_valid(), "Form must be valid; instead: errors (%s)" % user_form.errors)
        user_form.instance.set_password(user_form.cleaned_data["password_first"])
        user_form.save()

        # Fails for a second; no userlist if not admin
        old_username = self.data['username']
        self.data['username'] += '-different'
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertFalse(user_form.is_valid(), "Form must NOT be valid.")

        # Fails for a second; userlist if admin
        user_form = FacilityUserForm(facility=self.facility, admin_access=True, data=self.data)
        self.assertFalse(user_form.is_valid(), "Form must NOT be valid.")

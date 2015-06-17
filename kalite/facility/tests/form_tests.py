"""
"""
import string

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import unittest

from ..forms import FacilityUserForm, FacilityForm, FacilityGroupForm
from ..models import Facility, FacilityUser, FacilityGroup
from kalite.testing.base import KALiteTestCase, KALiteBrowserTestCase
from kalite.testing.mixins.browser_mixins import BrowserActionMixins
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins


class FacilityTestCase(KALiteTestCase):

    def setUp(self):
        super(FacilityTestCase, self).setUp()
        self.facility = Facility.objects.create(name='testfac')
        self.group = FacilityGroup.objects.create(name='testgroup', facility=self.facility)
        self.admin = User.objects.create(username='testadmin', password=make_password('insecure'))
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
        response = self.client.post(reverse('facility_user_signup'), self.data)
        self.assertNotIn("errorlist", response.content, "Must be no form errors")
        self.assertEqual(response.status_code, 302, "Status code must be 302")

        FacilityUser.objects.get(username=self.data['username'])  # should not raise error

    def test_admin_and_user_no_common_username(self):
        """Post as username"""
        self.data['username'] = self.admin.username
        response = self.client.post(reverse('facility_user_signup'), self.data, follow=True)
        self.assertEqual(response.status_code, 200, "Status code must be 200")
        self.assertFormError(response, 'form', 'username',
                            'A user with this username already exists. Please choose a new username and try again.')

    def test_password_length_valid(self):
        response = self.client.post(reverse('facility_user_signup'), self.data)
        self.assertNotIn("errorlist", response.content, "Must be no form errors")
        self.assertEqual(response.status_code, 302, "Status code must be 302")

        FacilityUser.objects.get(username=self.data['username'])  # should not raise error

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "Always fails occasionally")
    def test_password_length_enforced(self):
        # always make passwd shorter than passwd min length setting
        min_length = settings.PASSWORD_CONSTRAINTS['min_length']
        d = self.data['password_first'][:min_length - 1]
        self.data['password_first'] = self.data['password_recheck'] = d

        response = self.client.post(reverse('facility_user_signup'), self.data, follow=True)
        self.assertEqual(response.status_code, 200, "Status code must be 200")
        self.assertFormError(response, 'form', 'password_first',
                             "Password should be at least %d characters." % min_length)

    def test_only_ascii_letters_allowed(self):
        l = [self.data['password_first']] * 2
        self.data['password_first'] = self.data['password_recheck'] = string.whitespace.join(l)

        response = self.client.post(reverse('facility_user_signup'), self.data)
        self.assertNotIn("errorlist", response.content, "Must be no form errors")
        self.assertEqual(response.status_code, 302, "Status code must be 302")

        FacilityUser.objects.get(username=self.data['username'])  # should not raise error


class DuplicateFacilityNameTestCase(FacilityTestCase):

    def test_duplicate_facility_name(self):
        facility_form = FacilityForm(data={"name": self.facility.name})
        self.assertFalse(facility_form.is_valid(), "Form must not be valid, but was!")

    def test_nonduplicate_facility_name(self):
        facility_form = FacilityForm(data={"name": self.facility.name + "-different"})
        self.assertTrue(facility_form.is_valid(), "Form must be valid; instead: errors (%s)" % facility_form.errors)


class DuplicateFacilityGroupTestCase(FacilityTestCase):

    def test_duplicate_group_name(self):
        group_form = FacilityGroupForm(facility=self.facility, data={"facility": self.facility.id, "name": self.group.name})
        self.assertFalse(group_form.is_valid(), "Form must not be valid, but was!")

    def test_duplicate_group_name_in_different_facility(self):
        """Group need only be unique within a facility, not across them."""
        different_fac = Facility(name=self.facility.name + "-different")
        different_fac.save()
        group_form = FacilityGroupForm(facility=different_fac, data={"facility": self.facility.id, "name": self.group.name})
        self.assertTrue(group_form.is_valid(), "Form must be valid; instead: errors (%s)" % group_form.errors)

    def test_nonduplicate_group_name(self):
        group_form = FacilityGroupForm(facility=self.facility,
                                       data={"facility": self.facility.id, "name": self.group.name + "-different"})
        self.assertTrue(group_form.is_valid(), "Form must be valid; instead: errors (%s)" % group_form.errors)


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
        """Check that duplicate usernames on different facilities properly validates."""

        # Create a student.
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertTrue(user_form.is_valid(), "Form must be valid; instead: errors (%s)" % user_form.errors)
        user_form.instance.set_password(user_form.cleaned_data["password_first"])
        user_form.save()

        # Create a new facility
        new_fac = Facility(name="test")
        new_fac.save()

        # Create a user with same username, but on the new facility
        self.data['facility'] = new_fac.id
        self.data['first_name'] += "-different"
        self.data['group'] = None
        user_form = FacilityUserForm(facility=new_fac, data=self.data)
        self.assertTrue(user_form.is_valid(),
            "Form must be valid; instead: errors (%s)" % user_form.errors)

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
        self.data['username'] += '-different'
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertFalse(user_form.is_valid(), "Form must NOT be valid.")

        # Fails for a second; userlist if admin
        user_form = FacilityUserForm(facility=self.facility, data=self.data)
        self.assertFalse(user_form.is_valid(), "Form must NOT be valid.")


class FormBrowserTests(FacilityMixins, BrowserActionMixins, KALiteBrowserTestCase, CreateAdminMixin):

    def setUp(self):
        self.facility = self.create_facility()
        super(FormBrowserTests, self).setUp()

    def test_no_groups_no_select(self):
        signup_url = "%s%s%s" % (self.reverse('facility_user_signup'), "?&facility=", self.facility.id)
        self.browse_to(signup_url)
        group_label = self.browser.find_element_by_xpath("//label[@for='id_group']")
        self.assertFalse(group_label.is_displayed())
        group_select = self.browser.find_element_by_id('id_group')
        self.assertFalse(group_select.is_displayed())

    def test_signup_cannot_select_group(self):
        self.group = self.create_group(facility=self.facility)
        signup_url = "%s%s%s" % (self.reverse('facility_user_signup'), "?&facility=", self.facility.id)
        self.browse_to(signup_url)
        group_label = self.browser.find_element_by_xpath("//label[@for='id_group']")
        self.assertTrue(group_label.is_displayed())
        group_select = self.browser.find_element_by_id('id_group')
        self.assertFalse(group_select.is_displayed())

    def test_logged_in_student_cannot_select_group(self):
        self.group = self.create_group(facility=self.facility)
        self.student = self.create_student(facility=self.facility, group=self.group)
        self.browser_login_student(username=self.student.username, password='password', facility_name=self.facility.name)
        self.browse_to(self.reverse('edit_facility_user', kwargs={'facility_user_id': self.student.id}))
        group_label = self.browser.find_element_by_xpath("//label[@for='id_group']")
        self.assertTrue(group_label.is_displayed())
        group_select = self.browser.find_element_by_id('id_group')
        self.assertFalse(group_select.is_displayed())

    def test_teacher_can_select_group(self):
        self.group = self.create_group(facility=self.facility)
        self.student = self.create_student(facility=self.facility, group=self.group)
        self.teacher = self.create_teacher(facility=self.facility)
        self.browser_login_teacher(username=self.teacher.username, password='password', facility_name=self.facility.name)
        self.browse_to(self.reverse('edit_facility_user', kwargs={'facility_user_id': self.student.id}))
        group_label = self.browser.find_element_by_xpath("//label[@for='id_group']")
        self.assertTrue(group_label.is_displayed())
        group_select = self.browser.find_element_by_id('id_group')
        self.assertTrue(group_select.is_displayed())


class FormGroupTest(FacilityMixins, BrowserActionMixins, KALiteBrowserTestCase, CreateAdminMixin):

    def setUp(self):
        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)
        self.facility = self.create_facility()
        super(FormGroupTest, self).setUp()

    def test_ungroup_student_dropdown(self):
        self.group = self.create_group(facility=self.facility)
        self.student = self.create_student(facility=self.facility, group=self.group)
        self.browser_login_admin(**self.admin_data)
        self.browse_to(self.reverse("facility_management", kwargs={"zone_id": None, "facility_id": self.facility.id}))
        select = self.browser_wait_for_element(css_selector="select.movegrouplist option[value='']").text
        txt = 'Ungrouped'
        self.assertEqual(txt, select)


class HomePageTest(BrowserActionMixins, CreateAdminMixin, KALiteBrowserTestCase):

    def setUp(self):
        super(HomePageTest, self).setUp()
        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)

    def test_homepage_search(self):
        self.browse_to(self.reverse("homepage"));
        searchButton = self.browser_wait_for_element(css_selector="#search-button[disabled='disabled']")
        self.assertNotEqual(None, searchButton);
        self.browser.find_element_by_id("search").send_keys('search')
        searchButton = self.browser_wait_for_element(css_selector="#search-button[disabled='disabled']")
        self.assertEqual(None, searchButton);
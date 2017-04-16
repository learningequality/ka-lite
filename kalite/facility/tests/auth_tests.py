from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins.browser_mixins import BrowserActionMixins
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins


class FacilityUserPermissionsTests(CreateAdminMixin,
                                   FacilityMixins,
                                   BrowserActionMixins,
                                   KALiteBrowserTestCase):
    """Test different users creating/editing or trying to create/edit other types of users"""

    def setUp(self):
        super(FacilityUserPermissionsTests, self).setUp()

        self.default_password = 'password'

        self.admin_data = {'username': 'admin', 'password': 'admin'}
        self.admin = self.create_admin(**self.admin_data)

        self.facility = self.create_facility()

        self.teacher_data = {'username': 'teacher1', 'password': self.default_password}
        self.teacher = self.create_teacher(**self.teacher_data)
        self.teacher_to_edit = self.create_teacher(username='Edit Me', password=self.default_password)

        self.student_data = {'username': 'student1', 'password': self.default_password}
        self.student_to_edit = self.create_student(**self.student_data)
        self.student_form_data = {
            'id_username': 'user',
            'id_password_first': self.default_password,
            'id_password_recheck': self.default_password,
        }
        self.teacher_form_data = self.student_form_data.copy()
        self.teacher_form_data['id_username'] = 'teacher'

        # Urls
        self.add_student_url = self.reverse('add_facility_student')
        self.add_teacher_url = self.reverse('add_facility_teacher')
        self.edit_student_url = self.reverse('edit_facility_user', kwargs={'facility_user_id': self.student_to_edit.id})
        self.edit_teacher_url = self.reverse('edit_facility_user', kwargs={'facility_user_id': self.teacher_to_edit.id})

    def submit_and_wait(self, url, message_type, message_contains):
        self.browser.find_elements_by_class_name("submit")[0].click()
        self.wait_for_page_change(url)
        self.browser_check_django_message(message_type=message_type, contains=message_contains)

    def add_student(self):
        self.browse_to(self.add_student_url)
        self.fill_form(self.student_form_data)
        self.assertFalse(self.browser.find_element_by_id("id_is_teacher").get_attribute('value') == 'True', "While creating student, 'is_teacher' checkbox selected.")
        self.submit_and_wait(self.add_student_url, "success", "You successfully created")

    def edit_student(self, message_contains="Changes saved for"):
        self.browse_to(self.edit_student_url)
        edit_data = self.student_form_data.copy()
        edit_data['id_username'] = 'changed_student'
        self.fill_form(edit_data)
        self.submit_and_wait(self.reverse('facility_management', kwargs={'zone_id': 'None', 'facility_id': self.facility.id}), "success", message_contains)

    def add_teacher(self):
        self.browse_to(self.add_teacher_url)
        self.fill_form(self.teacher_form_data)
        self.assertTrue(self.browser.find_element_by_id("id_is_teacher").get_attribute('value') == 'True', "While creating teacher, 'is_teacher' checkbox not selected.")
        self.submit_and_wait(self.add_student_url, "success", "You successfully created")

    def edit_teacher(self, message_contains="Changes saved for"):
        self.browse_to(self.edit_teacher_url)
        edit_data = self.teacher_form_data.copy()
        edit_data['id_username'] = 'changed_teacher'
        self.fill_form(edit_data)
        self.submit_and_wait(self.reverse('facility_management', kwargs={'zone_id': 'None', 'facility_id': self.facility.id}), "success", message_contains)

    def test_admin_permissions(self):
        self.browser_login_admin(**self.admin_data)
        self.add_student()
        self.add_teacher()
        self.edit_student()
        self.edit_teacher()

    def test_teacher_permissions(self):
        self.browser_login_teacher(username=self.teacher.username, password=self.default_password)
        self.add_student()
        self.add_teacher()
        self.edit_student()
        self.edit_teacher()

    def test_student_edit_self(self):
        self.browser_login_student(username=self.student_to_edit.username, password=self.default_password)
        self.edit_student(message_contains="You successfully updated your user settings")

    def test_teacher_edit_self(self):
        self.browser_login_teacher(username=self.teacher_to_edit.username, password=self.default_password)
        self.edit_teacher(message_contains="You successfully updated your user settings")

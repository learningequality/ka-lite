"""
These use a web-browser, along selenium, to simulate user actions.
"""
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions, ui
from selenium.webdriver.firefox.webdriver import WebDriver

from django.core.urlresolvers import reverse
from testing.browser import BrowserTestCase
from testing.decorators import distributed_server_test
from i18n import get_installed_language_packs


@distributed_server_test
class LanguagePackTest(KALiteDistributedBrowserTestCase):

    def is_language_installed(lang_code):
    flag = False	# flag to check language de is installed or not
    installed_languages= get_installed_language_packs()
    for lang in installed_languages:
        if lang['code'] == lang_code
            flag = True
            break
    return flag

    def test_add_language_pack(self):
    ''' Test to check whether a language pack is added successfully or not'''	

    #Login as admin
    self.browser_login_admin()

    #Add the language pack	
    if is_language_installed("de"):
        print "Error already Installed "
    else:
        add_language_url= self.reverse("start_languagepack_download", kwargs={"lang": "de"})
        self.browse_to(add_language_url)

    if not is_language_installed("de"):
        print "Error Language Still Not Installed" 


    def test_delete_language_pack(self):
    ''' Test to check whether a language pack is deleted successfully or not'''

    #Login as admin
    self.browser_login_admin()

    #Delete the language pack
    if not is_language_installed("de"):
        print "Language Not Installed "
    else:
        delete_language_url = self.reverse("delete_language_pack", kwargs={"lang": "de"})
        self.browse_to(delete_language_url)

    if is_language_installed("de"):
        print "Language Still Not Deleted"

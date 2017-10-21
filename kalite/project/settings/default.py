import os

DEFAULT_USER_SETTINGS_FILE = os.path.join(os.environ["KALITE_HOME"], 'settings.py')
# Check if default user file exists and load settings from there
if os.path.isfile(DEFAULT_USER_SETTINGS_FILE):
    execfile(DEFAULT_USER_SETTINGS_FILE)

# If not, write a new custom user settings file and continue loading with
# defaults.
else:
    with open(DEFAULT_USER_SETTINGS_FILE, "w") as my_settings:
        my_settings.write(
            "# This is the default location where the kalite command finds its settings\n"
            "# You can change the below lines to use different default settings or\n"
            "# you can run kalite <command> --settings=other_module\n"
            "\n"
            "from kalite.project.settings.base import *\n"
            "\n"
            "# from kalite.project.settings.dev import *\n"
            "# from kalite.project.settings.raspberry_pi import *\n"
            "\n"
            "# Put your custom settings here\n"
            "# MY_SETTING = 123\n"
            "\n"
            "KALITE_WELCOME_MESSAGE = \"\"\"""\n"
            "<h2>KA Lite for <custom_name_here></h2>""\n"
            "<p>You are running an instance of KA Lite shipped with a RACHEL Pi. You can get online support for the device itself or KA Lite depending on the nature of your problem:</p>\n"
            "<ul>\n"
            "  <li><a href='http://community.learningequality.org/' target='_blank'>KA Lite community</a></li>\n"
            "  <li><a href='http://community.rachelfriends.org/' target='_blank'>RACHEL community</a></li>\n"
            "</ul>\n"
            "\"\"\"""\n"

        )
    from .base import *

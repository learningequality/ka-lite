import sys
import os

from django.core.management.base import BaseCommand, CommandError


def django_module(app_name):
    """
    Parse the django_app templates and its handlebars templates
    """
    # Todo (arceduardvincent) parse and indivial templates or handlebars without using the django_app name
    if app_name == "coachreports":
        os.popen("i18nize-templates %s/hbtemplates/coach_nav/*.handlebars" % (app_name))
        os.popen("i18nize-templates %s/hbtemplates/student_progress/*.handlebars" % (app_name))

        os.popen("i18nize-templates %s/templates/coachreports/*.html" % (app_name))
        os.popen("i18nize-templates %s/templates/coachreports/partials/*.html" % (app_name))

    if app_name == "control_panel":
        os.popen("i18nize-templates %s/hbtemplates/data_export/*.handlebars" % (app_name))

        os.popen("i18nize-templates %s/templates/control_panel/*.html" % (app_name))
        os.popen("i18nize-templates %s/templates/control_panel/snippets/*.html" % (app_name))
        os.popen("i18nize-templates %s/templates/control_panel/partials/*.html" % (app_name))

    elif app_name == "distributed":
        os.popen("i18nize-templates %s/hbtemplates/audio/*.handlebars" % (app_name))
        os.popen("i18nize-templates %s/hbtemplates/content/*.handlebars" % (app_name))
        os.popen("i18nize-templates %s/hbtemplates/exercise/*.handlebars" % (app_name))
        os.popen("i18nize-templates %s/hbtemplates/map/*.handlebars" % (app_name))
        os.popen("i18nize-templates %s/hbtemplates/pdf/*.handlebars" % (app_name))
        os.popen("i18nize-templates %s/hbtemplates/topics/*.handlebars" % (app_name))
        os.popen("i18nize-templates %s/hbtemplates/video/*.handlebars" % (app_name))

        os.popen("i18nize-templates %s/templates/admin/*.html" % (app_name))
        os.popen("i18nize-templates %s/templates/distributed/loadtesting/*.html" % (app_name))
        os.popen("i18nize-templates %s/templates/distributed/partials/*.html" % (app_name))
        os.popen("i18nize-templates %s/templates/distributed/*.html" % (app_name))

    elif app_name == "facility":
        os.popen("i18nize-templates %s/templates/admin/facility/facility/*.html" % (app_name))
        os.popen("i18nize-templates %s/templates/facility/*.html" % (app_name))

    elif app_name == "playlist":
        os.popen("i18nize-templates %s/hbtemplates/playlist/*.handlebars" % (app_name))
        os.popen("i18nize-templates %s/templates/playlist/*.html" % (app_name))

    elif app_name == "store":
        os.popen("i18nize-templates %s/hbtemplates/store/*.handlebars" % (app_name))
        os.popen("i18nize-templates %s/templates/store/*.html" % (app_name))

    elif app_name == "student_testing":
        os.popen("i18nize-templates %s/hbtemplates/student_testing/*.handlebars" % (app_name))
        os.popen("i18nize-templates %s/templates/student_testing/*.html" % (app_name))

    elif app_name == "updates":
        os.popen("i18nize-templates %s/templates/updates/update_languages.html" % (app_name))

    else:
        print ">>> The django app you called is not available in /kalite directory. " \
              "Did you mispelled it?"


class Command(BaseCommand):
    """
    This management command ask the module that will be i18nize.
    this cover the handlebars template and the templates
    converting to recognizable expression by our i18n.
    usage :
        python manage.py i18nize-templates <django_app>
        e.g(python manage.py i18nize-templates coachreports)
    """
    def handle(self, *args, **option):
        for django_app in args:
            try:
                self.stdout.write(">>> i18nize hbtemplate and templates")
                django_module(app_name=django_app)
                self.stdout.write(">>> i18nize hbtemplate and templates done in %s" % (django_app))

            except:
                self.stdout.write("It seems you didn't have the tools for i18nze-templates"
                                  "Fork this tools to https://github.com/mrpau/i18nize_templates "
                                  "Install then setup.py to use this tool")
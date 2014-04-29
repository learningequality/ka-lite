import os
import sys

########################
# Import settings from INSTALLED_APPS
########################
def import_installed_app_settings(installed_apps, global_vars):
    """
    Loop over all installed_apps, and search for their
      settings.py in the path.  Then load the settings.py
      directly (to avoid running the package's __init__.py file)

    Recurse into each installed_app's INSTALLED_APPS to collect all
    necessary settings.py files.
    """
    this_filepath = global_vars.get("__file__")  # this would be the project settings file

    for app in installed_apps:
        app_settings = None
        try:
            for path in sys.path:
                app_path = os.path.join(path, app.replace(".", "/"))
                settings_filepath = os.path.join(app_path, "settings.py")
                if os.path.exists(settings_filepath):
                    app_settings = {"__package__": app}  # explicit setting of the __package__, to allow absolute package ref'ing
                    global_vars.update({"__file__": settings_filepath})  # must let the app's settings file be set to that file!
                    execfile(settings_filepath, global_vars, app_settings)
                    break

            if app_settings is None:
                raise ImportError("File not found in path: %s settings.py" % app)
        except ImportError as err:
            #print "ImportError", err, app
            continue

        # We found the app's settings.py and loaded it into app_settings;
        #   now set those variables in the global space here.
        for var, var_val in app_settings.iteritems():
            if var.startswith("_") or var == "local_settings":
                # Don't combine / overwrite global variables or local_settings
                continue
            elif isinstance(var_val, tuple):
                # combine the above tuple variables
                cur_val = global_vars.get(var, tuple())
                # The next line is critical, so best to walk through the logic.
                # This captures dependencies in the following way:
                #   * An app should declare dependencies in order (within a tuple).
                #   * Any INSTALLED_APP is a more base dependency, so its dependencies should appear first,
                #        followed by any dependencies defined within this app not already declared above.
                #
                # This means that:
                #   * We always preserve the order of cur_val and var_val
                #   * We use the order of var_val (the INSTALLED_APP), and then fill in the remaining
                #       (ordered) dependencies from the current app.
                new_val = var_val + tuple([v for v in cur_val if v not in var_val])
                global_vars.update({var: new_val})
            elif isinstance(var_val, dict):
                # combine the above dict variables
                global_vars[var] = global_vars.get(var, {})
                global_vars[var].update(var_val)
            elif var not in global_vars:
                # Unknown variables that don't exist get set
                global_vars.update({var: var_val})
            elif global_vars.get(var) != var_val:
                # Unknown variables that do exist must have the same value--otherwise, conflict!
                raise Exception("(%s) %s is already set; resetting can cause confusion." % (app, var))

        # Now if INSTALLED_APPS exist, go do those.
        if "INSTALLED_APPS" in app_settings:
                # Combine the variable values, then import
                import_installed_app_settings(set(app_settings["INSTALLED_APPS"]) - set(installed_apps), global_vars)

    global_vars.update({"__file__": this_filepath})  # Set __file__ back to the project settings file


"""


benjaoming:


This crazyness will die in 0.14


However, until then, we will continue to magically import settings to avoid too
much refactoring.

It has been necessary to change this file to not resolve modules by some
perceived file path relative to calling module's __file__, but because we
are installing in a system python environment, Python will resolve the
module imports for us.



"""


########################
# Import settings from INSTALLED_APPS
########################
def import_installed_app_settings(installed_apps, global_vars, cur_app="__root__", processed_apps=set([])):
    """
    TODO(benjaoming): This horrible way of dynamically importing stuff will soon
    die, not to worry!
    
    https://github.com/learningequality/ka-lite/issues/2952
    
    Loop over all installed_apps, and search for their
      settings.py in the path.  Then load the settings.py
      directly (to avoid running the package's __init__.py file)

    Recurse into each installed_app's INSTALLED_APPS to collect all
    necessary settings.py files.
    """
    assert not set(processed_apps).intersection(set(installed_apps)), "Should never process the same app twice."

    this_filepath = global_vars.get("__file__")  # this would be the project settings file

    for app in installed_apps:
        
        try:
            # Craziness... these apps' settings modules cannot be loaded because
            # of circularity so they got moved
            if app == 'kalite.i18n':
                app_settings = __import__('kalite.legacy.i18n_settings').legacy.i18n_settings
            elif app == 'kalite.topic_tools':
                app_settings = __import__('kalite.legacy.topic_tools_settings').legacy.topic_tools_settings
            elif app == 'kalite.caching':
                app_settings = __import__('kalite.legacy.caching_settings').legacy.caching_settings
            elif app == 'kalite.updates':
                app_settings = __import__('kalite.legacy.updates_settings').legacy.updates_settings
            else:
                app_settings = __import__(app + ".settings")
                # The module that we are importing is stored as an attribute
                # of app_settings... i.e. "kalite.x.y.z.settings" becomes
                # "app_settings.x.y.z.settings"
                for x in app.split(".")[1:]:
                    app_settings = getattr(app_settings, x)
                app_settings = getattr(app_settings, "settings")
        except ImportError:
            continue
        
        for var in dir(app_settings):
            var_val = getattr(app_settings, var)
            
            # var.upper() != var is a way of saying "contains non-uppercase
            # letters".
            if var.startswith("_") or var.upper() != var:
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
                pass
        
        processed_apps = processed_apps.union(set([app]))
        # Now if INSTALLED_APPS exist, go do those.
        if "INSTALLED_APPS" in dir(app_settings):
                # Combine the variable values, then import
                remaining_apps = set(app_settings.INSTALLED_APPS) - processed_apps
                if remaining_apps:
                    import_installed_app_settings(
                        installed_apps=remaining_apps,
                        global_vars=global_vars,
                        cur_app=app,
                        processed_apps=processed_apps)

    global_vars.update({"__file__": this_filepath})  # Set __file__ back to the project settings file

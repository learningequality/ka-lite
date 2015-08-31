import json
import os
import re
import sys
from subprocess import Popen

from docutils import nodes
from docutils.parsers.rst.directives.images import Image
from docutils.parsers.rst import Directive
import docutils.parsers.rst.directives as directives
from exceptions import NotImplementedError

from errors import ActionError
from errors import OptionError

USER_ROLES = ["guest", "coach", "admin", "learner"]
SS_DUMP_DIR = ".screenshot_dump"
OUTPUT_PATH = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), SS_DUMP_DIR))
KALITECTL_PATH = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kalitectl.py"))
# Formatted from subprocess.Popen
# Trying to import call_command to execute a Django mgmt command gets you
# into a weird import hell, probably because of import_all_child_modules...
SCREENSHOT_COMMAND = [sys.executable, KALITECTL_PATH, "manage", "screenshots"]
SCREENSHOT_COMMAND_OPTS = ["-v0", "--output-dir={0}".format(OUTPUT_PATH)]
# These keys are css styles but they need to be camelCased
FOCUS_CSS_STYLES = { "borderStyle": "solid",
                     "borderColor": "red",
                     "borderWidth": "4px",
                     "borderRadius": "8px",
                   }

def setup(app):
    app.add_directive('screenshot', Screenshot)
    app.add_config_value('screenshots_create', False, False)
    app.connect('env-purge-doc', purge_screenshots)
    app.connect('env-updated', process_screenshots)

def purge_screenshots(app, env, docname):
    if not hasattr(env, 'screenshot_all_screenshots'):
        return
    env.screenshot_all_screenshots = [s for s in env.screenshot_all_screenshots
                          if s['docname'] != docname]

def process_screenshots(app, env):
    if not hasattr(env, 'screenshot_all_screenshots'):
        return

    if not app.config['screenshots_create']:
        print("Not doing screenshots on maggies farm no more")
        return
        
    if 'SPHINX_SS_USE_PVD' in os.environ.keys() and os.environ['SPHINX_SS_USE_PVD'] == "true":
        from pyvirtualdisplay import Display
        # Start a virtual headless display
        display = Display(visible=0, size=(1024, 768))
        display.start()
    else:
        display = None
    
    # Don't bother building screenshots if we're just collecting messages.
    # Just checks if we invoked the build command with "gettext" in there somewhere
    if "gettext" in sys.argv:
        return
    all_args = map(lambda x: x['from_str_arg'], env.screenshot_all_screenshots)
    # If building in a different language, start the server in a different language
    command = SCREENSHOT_COMMAND + SCREENSHOT_COMMAND_OPTS + \
              [re.sub(r"\s", r"", "--from-str={0}".format(json.dumps(all_args)))]
    language = env.config.language
    if language:
        command += ["--lang={0}".format(language)]
    subprocess = Popen(command)
    subprocess.wait()
    try:
        if subprocess.returncode:
            raise Exception("Screenshot process had nonzero return code: {0}".format(subprocess.returncode))
    finally:
        if display:
            display.stop()

def _parse_focus(arg_str):
    """ Returns id and annotation after splitting input string.

    First argument should be the jQuery-style selector. An optional 
    annotation can follow if separated by a separator '|'. Initial
    whitespace after the '|' will be ignored.

    Example inputs:
        #an_id
        #another_id | With an annotation
        form.foo input.radio | The quick brown fox 
    """
    split_str = arg_str.split('|', 1)
    if len(split_str) == 1:
        return {'id': split_str[0].rstrip(), 'annotation': ''}
    else:
        return {'id': split_str[0].rstrip(), 'annotation': split_str[1].lstrip()}

def _parse_command(command):
    """" Parses a command into action and options.

    Returns a dictionary with following keys:
       selector (string): the selector to identify the element
       action (string): the action type (if it's recognized)
       options (list): a list of options

    Raises an error if action type is not recognized or if options are invalid.

    Example inputs:
        #sync_button click
        NEXT send_keys some keys
        NEXT send_keys special characters like TAB and ENTER can be used like this

    Note that 'TAB', 'ENTER', and 'BACKSPACE' all have special meaning for send_keys
    """
    command_args = command.split()
    if not command_args:
        return None
    else:
        selector = command_args[0]
        action = command_args[1]
        options = command_args[2:]

    if action not in ('click', 'send_keys', 'submit', ''):
        raise ActionError(action)

    # Validate input options for the specified action.
    if action == 'click' or action == 'submit':
        if options:
            raise OptionError("The action '%s' must not contain any arguments whereas supplied arguments: '%s'." % (action, repr(options)))

    return {'selector': selector, 'action': action, 'options': options}

def _parse_login(username, password, submit=""):
    """" Parses a LOGIN command.

    Returns a dictionary with following keys:
       runhandler (string):  "_login_handler".
       args (dict) : A dictionary of arguments with following keys:
         username (string):  the username.
         password (string): password.
         submit (bool): True if login form is to be submitted, false otherwise.
    """
    submit_bool = True if submit == "submit" else False
    args = {'username': username, 'password': password, 'submit': submit_bool}
    return {'runhandler': '_login_handler', 'args': args}

def _parse_nav_steps(arg_str):
    """ Here's how to specify the navigation steps:

        1. selector action [options] ["|" selector action [options]] ...
        2. aliased_action_sequence [options]

        An explanation of navigation steps follows. Some examples can be found
        in ss_examples.rst in this directory.

        Selector is a single css selector (no whitespace allowed).
            "NEXT", which just sends a tab keystroke
            "SAME", which just stays focused on the element from the last action
        Where action could be one of "click", "send_keys", or "submit":
            click has no options and just clicks the element
            send_keys sends a sequence of keystrokes specified as a string by options
                
            submit submits a form and has no options
        Multiple actions on a page can be specified by putting a | separator,
            and specifying the action using the same syntax.

        aliased_action_sequence is one of a reserved keyword which aliases a common
            sequence of actions as above (or performs special actions unavailable by
            the regular syntax) potentially with options. Available aliases:

            LOGIN username password [submit], which just navigates to the login page
                and inputs the given username and password. Submits the form is submit
                is present, otherwise not.

        Returns a dictionary with:
            runhandler: reference to function invoked in the run method
            args:       a dictionary of arguments passed to the runhandler function
    """
    # The alias with its parse function
    COMMAND_ALIASES = [("LOGIN", _parse_login)]
    
    if not arg_str:
        arg_str = ""

    # First check if we've been passed an aliased_action_sequence
    words = arg_str.split(' ')
    for name, callback in COMMAND_ALIASES:
        if words[0] == name:
            return callback(*words[1:])

    commands = arg_str.split('|')
    parsed_commands = reduce(lambda x,y: x+[y] if y else x, map(_parse_command, commands), [])
    runhandler = "_command_handler"
    return { "runhandler":  runhandler,
             "args":        {'commands': parsed_commands}}

def _parse_user_role(arg_str):
    if arg_str in USER_ROLES:
        return arg_str
    else:
        raise NotImplementedError("Unrecognized user-role: %s" % arg_str)

class Screenshot(Image):
    """ Provides directive to include screenshot based on given options.

    Since it inherits from the Image directive, it can take Image options.

    When parsed, returns an image node pointing to a temporary file.
    The actual image is created later in the build process,
    when the 'env-updated' event is triggered. If the file doesn't exist when the
    image node is created, it can cause unexpected behavior, like not copying images
    properly for html builds.
    """
    required_arguments = 0
    optional_arguments = 0
    has_content = False
    
    # Add options to the image directive.
    option_spec = Image.option_spec.copy()
    option_spec['url'] = directives.unchanged
    option_spec['user-role'] = _parse_user_role
    option_spec['navigation-steps'] = _parse_nav_steps
    option_spec['focus'] = _parse_focus
    option_spec['registered'] = lambda x: directives.choice(x, ("true", "false"))

    def run(self):
        """ During the build process directives are parsed as nodes, and then
        later the nodes are built into the target format (html, latex, pdf, etc.)
        
        run is called automatically during the parsing process and is expected to
        return a list of nodes. Here we set up our parsing environment, then defer
        to a runhandler callback for parsing. The callback is determined by the
        navigation-steps option of the screenshot directive (in _parse_nav_steps).

        Language xx can be set in conf.py or by:
        make SPHINXOPTS="-D language=xx" html
        Build language can be accessed from the BuildEnvironment.
        """
        self.env = self.state.document.settings.env
        return_nodes = []
        if not hasattr(self.env, 'screenshot_all_screenshots'):
            self.env.screenshot_all_screenshots = []
        
        if not 'registered' in self.options:
            self.options['registered'] = False
        else:
            self.options['registered'] = True if self.options['registered'] == "true" else False

        if 'focus' in self.options:
            self.focus_selector = self.options['focus']['id']
            self.focus_annotation = self.options['focus']['annotation']

        if 'user-role' in self.options:
            self.user_role = self.options['user-role']
        else:
            self.user_role = "guest"

        if 'url' in self.options:
            self.url = self.options['url']

        if 'navigation-steps' in self.options:
            from hashlib import md5
            self.filename = md5(
                "".join(map(str, self.options.values()))
            ).hexdigest()
            runhandler = self.options['navigation-steps']['runhandler']
            args = self.options['navigation-steps']['args']
            return_nodes.append(getattr(self, runhandler)(**args))
        else:
            raise NotImplementedError("navigation-steps is a required option for screenshot directives!")

        return return_nodes

    # Handlers are invoked by the run function to parse the directives.
    def _login_handler(self, username, password, submit):
        from_str_arg = { "users": ["guest"], # This will fail if not guest, because of a redirect
                         "slug": "",
                         "start_url": "/",
                         "inputs": [{"#nav_login": ""},
                                    {"#id_username": username},
                                    {"#id_password": password},
                                   ],
                         "pages": [],
                         "notes": "",
                       }
        if submit:
            from_str_arg["inputs"].append({".login-btn":""})
        from_str_arg = self._common_arg_prep(from_str_arg)
        self.env.screenshot_all_screenshots.append({
            'docname':  self.env.docname,
            'from_str_arg': from_str_arg,
        })
        return self._make_image_node()

    def _command_handler(self, commands):
        if not self.url:
            raise NotImplementedError("Please supply a url using the :url: option")
        from_str_arg = { "users": [self.user_role],
                         "slug": "",
                         "start_url": self.url,
                         "pages": [],
                         "notes": "",
                       }        
        from_str_arg['inputs'] = reduce(lambda x,y: x+y, map(_cmd_to_inputs, commands), [])
        from_str_arg = self._common_arg_prep(from_str_arg)
        self.env.screenshot_all_screenshots.append({
            'docname':  self.env.docname,
            'from_str_arg': from_str_arg,
        })
        return self._make_image_node()

    def _common_arg_prep(self, arg):
        """All commands are handled in the same way regarding these options. """
        new_arg = arg
        new_arg["inputs"].append({"<slug>":self.filename})
        if hasattr(self, "focus_selector"):
            new_arg["focus"] = {}
            new_arg["focus"]["selector"] = self.focus_selector
            new_arg["focus"]["styles"] = FOCUS_CSS_STYLES
            new_arg["notes"] = self.focus_annotation if hasattr(self, "focus_annotation") else ""
        new_arg["registered"] = self.options["registered"]
        return new_arg

    def _make_image_node(self):
        """Make an image node by safely calling Image.run (i.e. ensure the file exists)."""
        self.arguments.append(os.path.join("/", SS_DUMP_DIR, self.filename+".png"))
        
        screenshot_file = os.path.join(OUTPUT_PATH, self.filename) + ".png"
        
        if not os.path.isfile(screenshot_file):
            # Ensure empty file
            open(screenshot_file, 'w').close()
        
        (image_node,) = Image.run(self)
        return image_node


# Implementation-specific functions for the screenshots management command
def _specialkeys(k):
    from selenium.webdriver.common.keys import Keys
    if k == "TAB":
        return Keys.TAB
    elif k == "ENTER":
        return Keys.ENTER
    elif k == "BACKSPACE":
        return Keys.BACKSPACE
    else:
        return k

def _cmd_to_inputs(cmd):
    from selenium.webdriver.common.keys import Keys
    inputs = []
    if cmd['selector'] == 'NEXT':
        sel = ""
        inputs.append({"": Keys.TAB})
    elif cmd['selector'] == 'SAME':
        sel = ""
    else:
        sel = cmd['selector']
    if cmd['action']=='click':
        inputs.append({sel: ""})
    elif cmd['action']=='submit':
        inputs.append({"<submit>": ""})
    elif cmd['action']=='send_keys':
        inputs.append({sel: ' '.join(map(_specialkeys,cmd['options']))})
    return inputs


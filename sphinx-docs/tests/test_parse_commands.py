"""
    Tests parse functions used in screenshot directive.

    Usage: Run `nosetests tests/test_parse_commands.py` to run just this file or
    `nosetests tests` to run all tests from files inside 'tests' directory.
    Either of the two commands must be run from the 'sphinx-docs' directory.
"""


from errors import ActionError, OptionError

from nose.tools import assert_equal, raises, with_setup

import sys, os

sys.path.insert(0, os.path.abspath(os.path.join('..','python-packages')))
import screenshot

def test_parse_focus():
    """ Test screenshot._parse_focus() function.
    """
    # Test with just the id and no annotation.
    arg_str = 'id_with_no_annotation'
    expected_output = {'id': 'id_with_no_annotation', 'annotation': ''}
    actual_output = screenshot._parse_focus(arg_str)
    assert_equal(expected_output, actual_output)

    # Test with id and a non-empty annotation.
    arg_str = 'id_with_annotation | test annotation'
    expected_output = {'id': 'id_with_annotation', 'annotation': 'test annotation'}
    actual_output = screenshot._parse_focus(arg_str)
    assert_equal(expected_output, actual_output)

def test_parse_command():
    """ Test screenshot._parse_command() function.

    Tests cases where the command completes successfully. Cases in which
    exceptions are raised are handled separately.
    """
    # Test 'click' action with no options.
    arg_str = 'selector click'
    expected_output = {'selector': 'selector', 'action': 'click', 'options': []}
    actual_output = screenshot._parse_command(arg_str)
    assert_equal(expected_output, actual_output)

    # Test 'submit' action with no options.
    arg_str = 'selector submit'
    expected_output = {'selector': 'selector', 'action': 'submit', 'options': []}
    actual_output = screenshot._parse_command(arg_str)
    assert_equal(expected_output, actual_output)

    # Test 'send_keys' action with no options.
    arg_str = 'selector send_keys'
    expected_output = {'selector': 'selector', 'action': 'send_keys', 'options': []}
    actual_output = screenshot._parse_command(arg_str)
    assert_equal(expected_output, actual_output)

    # Test 'send_keys' action with few options.
    arg_str = 'selector send_keys keystroke1 keystroke2'
    expected_output = {'selector': 'selector', 'action': 'send_keys', 'options': ['keystroke1', 'keystroke2']}
    actual_output = screenshot._parse_command(arg_str)
    assert_equal(expected_output, actual_output)

@raises(ActionError)
def test_parse_command_action_error():
    """ Test ActionError(s) raised by screenshot._parse_command() function.
    """
    # Test with an invalid action, should thrown an exception.
    arg_str = 'selector invalid_action'
    screenshot._parse_command(arg_str)

@raises(OptionError)
def test_parse_command_option_error():
    """ Test OptionError(s) raised by screenshot._parse_command() function.
    """
    # Test 'click' action with options, should thrown an exception.
    arg_str = 'selector click options'
    screenshot._parse_command(arg_str)

    # Test 'submit' action with options, should thrown an exception.
    arg_str = 'selector click options'
    screenshot._parse_command(arg_str)

def test_parse_login():
    """ Test screenshot._parse_login() function.
    """
    # Test LOGIN command without submit.
    args = ('username', 'password', '')
    expected_output = {'runhandler': '_login_handler', 'args': {'username': 'username', 'password': 'password', 'submit': False}}
    actual_output = screenshot._parse_login(*args)
    assert_equal(expected_output, actual_output)

    # Test LOGIN command with submit.
    args = ('username', 'password', 'submit')
    expected_output = {'runhandler': '_login_handler', 'args': {'username': 'username', 'password': 'password', 'submit': True}}
    actual_output = screenshot._parse_login(*args)
    assert_equal(expected_output, actual_output)

def test_parse_nav_steps():
    """ Test screenshot._parse_nav_steps() function.
    """
    print sys.path
    # Test with just one command.
    arg_str = 'selector click'
    expected_output = {'runhandler': '_command_handler', 'args': {'commands': [{'action': 'click', 'options': [], 'selector': 'selector'}]}}
    actual_output = screenshot._parse_nav_steps(arg_str)
    assert_equal(expected_output, actual_output)

    # Test with just two commands separated by '|'.
    arg_str = 'selector click | selector2 click'
    expected_output = {'runhandler': '_command_handler', 'args': {'commands': [{'action': 'click', 'options': [], 'selector': 'selector'},{'action': 'click', 'options': [], 'selector': 'selector2'}]}}
    actual_output = screenshot._parse_nav_steps(arg_str)
    assert_equal(expected_output, actual_output)

    # Test with no commands
    arg_str = ''
    expected_output = {'runhandler': '_command_handler', 'args': {'commands': []}}
    actual_output = screenshot._parse_nav_steps(arg_str)
    assert_equal(expected_output, actual_output)

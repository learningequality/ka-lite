"""
Tests that arguments are parsed correctly by bin/kalite.
Just try a few management commands and get their output.

To run these tests, just run this script: `python test_cli.py`.
It will return a nonzero value if the tests fail.
"""
import os

from subprocess import check_output, check_call, CalledProcessError

filepath = os.path.dirname(__file__)
TEST_BASE = "python " + os.path.join(filepath, "bin", "kalite") + " manage test --test-cli "

print TEST_BASE

expect_success = [  # (argument, expected output)
    ("-z123", "123"),
    ("-zabc", "abc"),
    ("--fake-arg=abc123", "abc123"),
]

expect_failure = [
    "--fake-arg2 --fake-arg=blah",  # A failure because --fake-arg2 requires an argument
    "-y --fake-arg=blah",
    "--fake-arg2 -zblah",
    "-y -zblah",  # Variations on a theme
    "--fake-arg abc123",  # Whitespace is verboten
]

for arg, expected_output in expect_success:
    cmd = TEST_BASE + arg
    print("Testing: " + cmd)
    output = check_output(args=cmd)
    print("Output was: " + output)
    assert expected_output in output.split(), "Did not find expected output"

for arg in expect_failure:
    cmd = TEST_BASE + arg
    print("Testing: " + cmd)
    try:
        check_call(args=cmd)
        assert False, "Expected check_call to fail"
    except CalledProcessError:
        pass  # All is well


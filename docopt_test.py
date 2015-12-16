"""
We messed around with the internals of docopt in order to get parsing *just right*, but we paid the price because
it only parses *almost right* -- it's got issues with "--options that have whitepsace".

This script is meant to put our messed-around-with docopt function through it's paces.

Usage: run from the command line. Outputs a bunch of debug info, and raises an assertion error if docopt fails
  to parse something correctly. Additionally, raises an error if docopt quietly parses something we *don't* want
  it to parse.
"""
import kalitectl

from kalitectl import docopt, DocoptExit

valid_commands = [
    # Sanity check -- these commands worked before and should continue to work
    (
        "kalite start",
        {
            '--debug': False,
            '--foreground': False,
            '--help': False,
            '--port': None,
            '--settings': None,
            '--skip-job-scheduler': False,
            '--version': False,
            '--watch': False,
            'COMMAND': None,
            'DJANGO_OPTIONS': [],
            'diagnose': False,
            'manage': False,
            'restart': False,
            'shell': False,
            'start': True,
            'status': False,
            'stop': False,
            'test': False
        }
     ),
    (
        "kalite start --port=8010",
        {
            '--debug': False,
            '--foreground': False,
            '--help': False,
            '--port': '8010',
            '--settings': None,
            '--skip-job-scheduler': False,
            '--version': False,
            '--watch': False,
            'COMMAND': None,
            'DJANGO_OPTIONS': [],
            'diagnose': False,
            'manage': False,
            'restart': False,
            'shell': False,
            'start': True,
            'status': False,
            'stop': False,
            'test': False
        }
    ),
    (
        "kalite manage unpack_assessment_zip my_cool_file.zip",
        {
            '--debug': False,
            '--foreground': False,
            '--help': False,
            '--port': None,
            '--settings': None,
            '--skip-job-scheduler': False,
            '--version': False,
            '--watch': False,
            'COMMAND': 'unpack_assessment_zip',
            'DJANGO_OPTIONS': ['my_cool_file.zip'],
            'diagnose': False,
            'manage': True,
            'restart': False,
            'shell': False,
            'start': False,
            'status': False,
            'stop': False,
            'test': False
        }
    ),
    (
        "kalite manage runserver 0.0.0.0:8008 --settings=kalite.project.settings.dev",
        {
            '--debug': False,
            '--foreground': False,
            '--help': False,
            '--port': None,
            '--settings': 'kalite.project.settings.dev',
            '--skip-job-scheduler': False,
            '--version': False,
            '--watch': False,
            'COMMAND': 'runserver',
            'DJANGO_OPTIONS': ['0.0.0.0:8008'],
            'diagnose': False,
            'manage': True,
            'restart': False,
            'shell': False,
            'start': False,
            'status': False,
            'stop': False,
            'test': False
        }
    ),

    # Commands that don't work, but should:
    (
        "kalite start --port 8010",
        {
            '--debug': False,
            '--foreground': False,
            '--help': False,
            '--port': '8010',
            '--settings': None,
            '--skip-job-scheduler': False,
            '--version': False,
            '--watch': False,
            'COMMAND': None,
            'DJANGO_OPTIONS': [],
            'diagnose': False,
            'manage': False,
            'restart': False,
            'shell': False,
            'start': True,
            'status': False,
            'stop': False,
            'test': False
        }
    ),
    (
        "kalite manage runserver 0.0.0.0:8008 --settings kalite.project.settings.dev",
        {
            '--debug': False,
            '--foreground': False,
            '--help': False,
            '--port': None,
            '--settings': 'kalite.project.settings.dev',
            '--skip-job-scheduler': False,
            '--version': False,
            '--watch': False,
            'COMMAND': 'runserver',
            'DJANGO_OPTIONS': ['0.0.0.0:8008'],
            'diagnose': False,
            'manage': True,
            'restart': False,
            'shell': False,
            'start': False,
            'status': False,
            'stop': False,
            'test': False
        }
    ),
    (
        "kalite manage contentload -dD:\ka-lite\import_test\ --import",
        {
            '--debug': False,
            '--foreground': False,
            '--help': False,
            '--port': None,
            '--settings': None,
            '--skip-job-scheduler': False,
            '--version': False,
            '--watch': False,
            'COMMAND': 'contentload',
            'DJANGO_OPTIONS': ["-dD:\ka-lite\import_test\\", '--import'],
            'diagnose': False,
            'manage': True,
            'restart': False,
            'shell': False,
            'start': False,
            'status': False,
            'stop': False,
            'test': False
        }
     ),
    (
        "kalite manage contentload --import -dD:\ka-lite\import_test\\",
        {
            '--debug': False,
            '--foreground': False,
            '--help': False,
            '--port': None,
            '--settings': None,
            '--skip-job-scheduler': False,
            '--version': False,
            '--watch': False,
            'COMMAND': 'contentload',
            'DJANGO_OPTIONS': ['--import', "-dD:\ka-lite\import_test\\"],
            'diagnose': False,
            'manage': True,
            'restart': False,
            'shell': False,
            'start': False,
            'status': False,
            'stop': False,
            'test': False
        }
     ),
    (
        "kalite manage contentload --import --data=D:\ka-lite\import_test\\",
        {
            '--debug': False,
            '--foreground': False,
            '--help': False,
            '--port': None,
            '--settings': None,
            '--skip-job-scheduler': False,
            '--version': False,
            '--watch': False,
            'COMMAND': 'contentload',
            'DJANGO_OPTIONS': ['--import', "--data=D:\ka-lite\import_test\\"],
            'diagnose': False,
            'manage': True,
            'restart': False,
            'shell': False,
            'start': False,
            'status': False,
            'stop': False,
            'test': False
        }
    ),
    (
        "kalite manage contentload --import --data D:\ka-lite\import_test\\",
        {
            '--debug': False,
            '--foreground': False,
            '--help': False,
            '--port': None,
            '--settings': None,
            '--skip-job-scheduler': False,
            '--version': False,
            '--watch': False,
            'COMMAND': 'contentload',
            'DJANGO_OPTIONS': ['--import', "--data", "D:\ka-lite\import_test\\"],
            'diagnose': False,
            'manage': True,
            'restart': False,
            'shell': False,
            'start': False,
            'status': False,
            'stop': False,
            'test': False
        }
    ),
]

invalid_commands = [
    "kalite manage contentload --import -d D:\ka-lite\import_test\\",  # Should this be invalid? I dunno.
]

if __name__ == "__main__":
    print("valid commands:")
    for cmd, check in valid_commands:
        arguments = docopt(kalitectl.__doc__, argv=cmd.split(' ')[1:], version="9.9.9", options_first=False)
        print('"' + cmd + '"' + ":\n" + str(arguments))
        assert arguments == check, reduce(
            lambda l, x: l + "\n" + x,
            [str((k, v)) + " expected, but instead got " + str((k, arguments[k])) for k, v in check.iteritems() if arguments[k] != v],
            ""
        )

    print("invalid commands:")
    for cmd in invalid_commands:
        arguments = docopt(kalitectl.__doc__, argv=cmd.split(' ')[1:], version="9.9.9", options_first=False)
        print(cmd + ":\n" + str(arguments))
        assert arguments is None, "Docopt should have exited!"
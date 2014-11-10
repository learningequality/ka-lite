"""Utility for cleaning up exercise files using lxml.

Passes the exercise through lxml and then serializes it, cleaning up
un-closed tags, improper entities, and other mistakes.
"""

import argparse
import lint_i18n_strings

import lxml.html.html5parser


def main():
    """Handle running this program from the command-line."""
    # Handle parsing the program arguments
    arg_parser = argparse.ArgumentParser(
        description='Clean up HTML exercise files.')
    arg_parser.add_argument('html_files', nargs='+',
        help='The HTML exercise files to clean up.')

    args = arg_parser.parse_args()

    for filename in args.html_files:
        # Parse the HTML tree.  The parser in lint_i18n_strings properly
        # handles utf-8, which the default lxml parser doesn't. :-(
        html_tree = lxml.html.html5parser.parse(
            filename, parser=lint_i18n_strings.PARSER)

        with open(filename, 'w') as f:
            f.write(lint_i18n_strings.get_page_html(html_tree))


if __name__ == '__main__':
    main()

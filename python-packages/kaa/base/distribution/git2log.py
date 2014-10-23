# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# git2log.py - create ChangeLog file based on git log
# -----------------------------------------------------------------------------
# Copyright 2012 Jason Tackaberry
#
# Please see the file AUTHORS for a complete list of authors.
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version
# 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA
#
# -----------------------------------------------------------------------------
import os
import textwrap

def git2log():
    """
    Generates a GNU style ChangeLog based on git log.

    This function assumes it's being invoked from within a git repository and
    will output a ChangeLog file in the current directory.
    """
    commits = []
    commit = {}
    for line in os.popen('git log --raw --name-status --date=iso --no-color'):
        if line.startswith('commit'):
            if commit:
                commits.append(commit)
            commit = {}
        elif line.startswith('Author:'):
            commit['author'] = line[8:].strip()
        elif line.startswith('Date:'):
            commit['date'] = line[5:].strip()[:10]
        elif not line.strip():
            if 'log' in commit:
                # Empty line after we already have log lines. Set a flag to skip
                # subsequent lines from this commit log.
                commit['skip'] = True
        elif line[0] == ' ':
            # Commit log line.
            if not commit.get('skip'):
                commit.setdefault('log', []).append(line.strip())
        elif line[1] == '\t':
            # A file line: first byte is status, followed by tab and filename.
            try:
                status, name = line.strip().split('\t')
            except ValueError:
                # This shouldn't happen, but skip the line if it does.
                continue
            if status == 'A':
                name += ' (added)'
            elif status == 'D':
                name += ' (deleted)'
            commit.setdefault('files', []).append(name)
    if commit:
        commits.append(commit)

    # Now that all the commits are parsed, write them to the ChangeLog
    # file, collapsing separate commits from the same author on the same
    # date into one ChangeLog entry.
    file_wrapper = textwrap.TextWrapper(initial_indent='\t* ', subsequent_indent='\t',
                                        break_on_hyphens=False, break_long_words=False)
    log_wrapper = textwrap.TextWrapper(initial_indent='\t', subsequent_indent='\t')
    out = open('ChangeLog', 'w')
    last = None
    for commit in commits:
        if not last or (commit['date'] != last['date'] or commit['author'] != last['author']):
            out.write('%s  %s\n\n' % (commit['date'], commit['author']))
        if 'files' in commit:
            files = file_wrapper.wrap(', '.join(commit['files']))
        else:
            files = []
        log = log_wrapper.wrap(' '.join(commit['log']))

        # If files and log fits on a single line, print it that way.
        if len(log) == len(files) == 1 and len(files[0]) + len(log[0]) < 70:
            out.write('%s: %s\n' % (files[0], log[0].lstrip()))
        else:
            if files:
                out.write('\n'.join(files) + ':\n')
            out.write('\n'.join(log) + '\n')
        out.write('\n')
        last = commit

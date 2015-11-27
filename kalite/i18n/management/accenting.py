# -*- coding: utf-8 -*-
"""**accenting** allows you to convert certain ascii strings to their
accented versions (the convert function). There's also convert_msg, a
convenience function useful for converting po/mo file entries. Used
mainly for debugging i18n.

"""
import re
import itertools


# Acquired from
# https://github.com/edx/i18n-tools/blob/master/i18n/dummy.py and
# https://github.com/edx/i18n-tools/blob/master/i18n/converter.py
class Converter(object):
    r"""Converter is an class that transforms strings.  It hides embedded
       tags (HTML or Python sequences) from transformation, and
       converts certain letters into their accented counterparts (see
       Converter.TABLE for the exact mapping.)

       To implement Converter, provide implementation for inner_convert_string()

       Strategy:
         1. extract tags embedded in the string
           a. use the index of each extracted tag to re-insert it later
           b. replace tags in string with numbers (<0>, <1>, etc.)
           c. save extracted tags in a separate list
         2. convert string
         3. re-insert the extracted tags

    Each property file is derived from the equivalent en_US file, with these
    transformations applied:

    1. Every vowel is replaced with an equivalent with extra accent marks.

    2. Every string is padded out to +30% length to simulate verbose languages
       (such as German) to see if layout and flows work properly.

    3. Every string is terminated with a '#' character to make it easier to detect
       truncation.

    Example use::

        >>> from dummy import Dummy
        >>> c = Dummy()
        >>> c.convert("My name is Bond, James Bond")
        u'M\xfd n\xe4m\xe9 \xefs B\xf8nd, J\xe4m\xe9s B\xf8nd \u2360\u03c3\u044f\u0454\u043c \u03b9\u03c1#'
        >>> print c.convert("My name is Bond, James Bond")
        Mý nämé ïs Bønd, Jämés Bønd Ⱡσяєм ιρ#
        >>> print c.convert("don't convert <a href='href'>tag ids</a>")
        døn't çønvért <a href='href'>täg ïds</a> Ⱡσяєм ιρѕυ#
        >>> print c.convert("don't convert %(name)s tags on %(date)s")
        døn't çønvért %(name)s tägs øn %(date)s Ⱡσяєм ιρѕ#
    """

    TABLE = dict(zip(
        u"AabCcEeIiOoUuYy",
        u"ÀäßÇçÉéÌïÖöÛüÝý"
    ))

    # matches tags like these:
    #   HTML:   <B>, </B>, <BR/>, <textformat leading="10">
    #   Python: %(date)s, %(name)s
    tag_pattern = re.compile(
        r'''
        (<[^>]+>)           |       # <tag>
        ({[^}]+})           |       # {tag}
        (%\([\w]+\)\w)      |       # %(tag)s
        (&\w+;)             |       # &entity;
        (&\#\d+;)           |       # &#1234;
        (&\#x[0-9a-f]+;)    |       # &#xABCD;
        (\[\[.*\]\])                # [[snowman radio]];
        ''',
        re.IGNORECASE | re.VERBOSE
    )

    def convert(self, string):
        """Returns: a converted tagged string
           param: string (contains html tags)

           Don't replace characters inside tags
        """
        (string, tags) = self.detag_string(string)
        string = self.inner_convert_string(string)
        string = self.retag_string(string, tags)
        return string

    def detag_string(self, string):
        """Extracts tags from string.

           returns (string, list) where
           string: string has tags replaced by indices (<BR>... => <0>, <1>, <2>, etc.)
           list: list of the removed tags ('<BR>', '<I>', '</I>')
        """
        counter = itertools.count(0)
        count = lambda m: '<%s>' % counter.next()
        tags = self.tag_pattern.findall(string)
        tags = [''.join(tag) for tag in tags]
        (new, nfound) = self.tag_pattern.subn(count, string)
        if len(tags) != nfound:
            raise Exception('tags dont match:' + string)
        return (new, tags)

    def retag_string(self, string, tags):
        """substitutes each tag back into string, into occurrences of <0>, <1> etc"""
        for i, tag in enumerate(tags):
            bracketed = '<%s>' % i
            try:
                string = re.sub(bracketed, tag, string, 1)
            except Exception as e:  # re module raising vague errors, WHY
                continue
        return string

    def inner_convert_string(self, string):
        for old, new in self.TABLE.items():
            string = string.replace(old, new)
        return self.pad(string)

    def pad(self, string):
        return string

    def convert_msg(self, msg):
        """
        Takes one POEntry object and converts it (adds a dummy translation to it)
        msg is an instance of polib.POEntry
        """
        source = msg.msgid
        if not source:
            # don't translate empty string
            return

        plural = msg.msgid_plural
        if plural:
            # translate singular and plural
            foreign_single = self.convert(source)
            foreign_plural = self.convert(plural)
            plural = {
                '0': self.final_newline(source, foreign_single),
                '1': self.final_newline(plural, foreign_plural),
            }
            msg.msgstr_plural = plural
        else:
            foreign = self.convert(source)
            msg.msgstr = self.final_newline(source, foreign)

    def final_newline(self, original, translated):
        """ Returns a new translated string.
            If last char of original is a newline, make sure translation
            has a newline too.
        """
        if original:
            if original[-1] == '\n' and translated[-1] != '\n':
                translated += '\n'
        return translated

# Main API
"""Convert certain ascii characters in a string into their accented
versions.
"""
convert = Converter().convert

"""Convert the msgstr of a (M|P)OEntry into its accented version.
"""
convert_msg = Converter().convert_msg

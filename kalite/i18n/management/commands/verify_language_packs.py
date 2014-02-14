"""
This command helps to identify SRT files that are empty or malformed, and
some translations that are broken and need a-fixin'.

When it identifies issues, it will either auto-fix
(for example, by deleting rogue SRTs), or halt language pack
creation for languages with errors

NOTE: all language codes internally are assumed to be in django format (e.g. en_US)
"""
import datetime
import glob
import os
import re
import shutil

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

import settings
from i18n import lcode_to_django
from main.topic_tools import get_node_cache
from settings import LOG as logging
from update_language_packs import handle_po_compile_errors
from update_po import compile_po_files
from utils.general import ensure_dir, datediff


class Command(BaseCommand):
    help = 'Updates all language packs'

    option_list = BaseCommand.option_list + (
        make_option('-l', '--lang_code',
                    action='store',
                    dest='lang_code',
                    default="all",
                    metavar="LANG_CODE",
                    help="Language code to update (default: all)"),
    )

    def handle(self, **options):
        if not settings.CENTRAL_SERVER:
            raise CommandError("This must only be run on the central server.")
        if not options["lang_code"] or options["lang_code"].lower() == "all":
            lang_codes = os.listdir(settings.LOCALE_PATHS[0])

        else:
            lang_codes = [lcode_to_django(lc) for lc in options["lang_code"].split(",")]

        # Raw language code for srts
        validate_srts(lang_codes=lang_codes)

        # Converted language code for language packs
        validate_translations(lang_codes=lang_codes)


def validate_srts(lang_codes, forcefully=False):
    """
    Validate that srt files are not empty or malformed. If invalid, delete or fix them.
    """


    def validate_single_srt(srt_file):
        """
        Validate a single srt file based on the following criteria:
            - YouTube ID must be in topic tree
            - line counters in srt file proceed in order and that it isn't empty
            - the timestamps for the subtitles make sense for the video
            - basic string validation: the strings aren't duplicate characters
        """
        #logging.debug("Validating %s" % srt_file)
        srt_issues = []

        with open(srt_file, "r") as fp:
            srt_content = fp.read()

        def validate_mapping(srt_file, srt_issues):
            youtube_id = os.path.basename(srt_file)[:-4]
            if youtube_id not in get_node_cache("Video"):
                srt_issues.append("youtube ID unknown: %s" % youtube_id)
        validate_mapping(srt_file, srt_issues)

        # First, check that counts make sense
        def validate_counts(srt_content, srt_issues):
            counts = re.findall("([0-9]+)\r\n[0-9:,]+ --> [0-9:,]+\r\n", srt_content, re.S | re.M)

            diff = [1 != (int(counts[i])-int(counts[i-1])) for i in range(1, len(counts))]
            if any(diff):
                srt_issues.append("Subtitles don't seem to proceed in an integer sequence.")

            max_count = int(counts[-1]) if counts else 0
            if not max_count:
                srt_issues.append("Srt is empty / whitespace")
        validate_counts(srt_content, srt_issues)

        # Second, check the coverage
        def validate_times(srt_content, srt_issues):
            times = re.findall("([0-9:,]+) --> ([0-9:,]+)\r\n", srt_content, re.S | re.M)

            parse_time = lambda str: datetime.datetime.strptime(str, "%H:%M:%S,%f")
            for i in range(len(times)):
                try:
                    between_subtitle_time = datediff(parse_time(times[i][0]), parse_time(times[i-1][1] if i > 0 else "00:00:00,000"))
                    within_subtitle_time  = datediff(parse_time(times[i][1]), parse_time(times[i][0]))

                    if between_subtitle_time > 60.:
                        srt_issues.append("Between-subtitle gap of %5.2f seconds" % between_subtitle_time)

                    if within_subtitle_time > 60.:
                        srt_issues.append("Within-subtitle duration of %5.2f seconds" % within_subtitle_time)
                    elif within_subtitle_time == 0.:
                        logging.debug("Subtitle flies by too fast (%s --> %s)." % times[i])

                    #print "Start: %s\tB: %5.2f\tW: %5.2f" % (parse_time(times[i][0]), between_subtitle_time, within_subtitle_time)
                except Exception as e:
                    if not times[i][1].startswith('99:59:59'):
                        srt_issues.append("Error checking times: %s" % e)
                    else:
                        if len(times) - i > 1 and len(times) - i - 1 > len(times)/10.:
                            if i == 0:
                                srt_issues.append("No subtitles have a valid starting point.")
                            else:
                                logging.debug("Hit end of movie, but %d (of %d) subtitle(s) remain in the queue." % (len(times) - i - 1, len(times)))
                        break
        validate_times(srt_content, srt_issues)

        # Third, check out the strings
        def validate_strings(srt_content, srt_issues):
            strings = re.findall("([^\r]*[^\n])\r\n\r\n[0-9]+\r\n[0-9:,]+ --> [0-9:,]+\r\n", srt_content, re.S | re.M)

            n_empty = 0
            for str in strings:
                n_empty += int(len(str.strip()) == 0)

                if len(str.strip()) > 1 and len(set(str)) == 1 and "." not in str:
                    srt_issues.append("srt contains string of all one character: %s" % str)

            if n_empty > len(strings)/10.:  # 10%
                srt_issues.append("%d (of %d) empty subtitle(s)." % (n_empty, len(strings)))
        validate_strings(srt_content, srt_issues)

        # Finally, return all issues.
        return srt_issues


    n_srts_with_issues = 0
    for lang_code in lang_codes:
        for locale_path in settings.LOCALE_PATHS:
            all_srts = glob.glob(os.path.join(locale_path, lang_code, "subtitles", "*.srt"))
            for srt_file in all_srts:
                srt_issues = validate_single_srt(srt_file)
                if not srt_issues:
                    continue
                logging.info("Issues with %s: %s" % (os.path.basename(srt_file), ", ".join(srt_issues)))
                if forcefully:
                    os.remove(srt_file)  # given the structure of cache_srts, this won't trigger a re-download.
                elif os.path.exists(os.path.join(settings.CONTENT_ROOT, os.path.basename(srt_file).replace(".srt", ".mp4"))):
                    logging.info("")
                n_srts_with_issues += 1

    logging.info("%s of %s subtitles had some sort of issue." % (n_srts_with_issues, len(all_srts)))

def validate_translations(lang_codes=None, forcefully=False):
    """
    """

    # Compile
    (out, err, rc) = compile_po_files(lang_codes=lang_codes)  # converts to django
    broken_langs = handle_po_compile_errors(lang_codes=lang_codes, out=out, err=err, rc=rc)

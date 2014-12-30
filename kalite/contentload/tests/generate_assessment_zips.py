import os
import urllib3
import vcr

from kalite.testing import KALiteTestCase

HTTREPLAY_RECORDINGS_DIR = os.path.join(os.path.dirname(__file__),
                                        "fixtures")


class GenerateAssessmentItemsCommandTests(KALiteTestCase):

    @vcr.use_cassette("fixtures/generate_assessment_zips_tests.yml")
    def test_fetches_assessment_items(self):
        urllib3.urlopen(
            "https://s3.amazonaws.com/uploads.hipchat.com/86198%2F624195%2FtYo7Ez0tt3e1qQW%2Fassessmentitems.json"
        )

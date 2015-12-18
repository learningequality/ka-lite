#from kalite import ROOT_DATA_PATH
#from kalite.topic_tools.settings import CHANNEL
#from kalite.version import VERSION, SHORTVERSION
import os

def begin_download():
    print "dl_assess.py invoked"

    # for extracting assessment item resources
    ASSESSMENT_ITEMS_ZIP_URL = "https://learningequality.org.downloads/ka-lite/{version}/content/{channel}_assessment.zip".format(version=SHORTVERSION, channel=CHANNEL)

print "\nnew process, dl_assess.py:"
import sys
print "sys.path is: "
print sys.path
print "\n\n\ncurrent working directory: " + os.getcwd()

if __name__ == "__main__":
    import version
    #begin_download()

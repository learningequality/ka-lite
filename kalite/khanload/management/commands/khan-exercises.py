# Script to download the latest version of Khan-Exercises from github master repository.
# Currently just to be run before code distribution.

#WARNING: Do not run. Latest version of Khan Exercises is currently incompatible with KA Lite codebase.

import requests
import StringIO
import zipfile
import os
import shutil

data_path = os.path.dirname(os.path.realpath(__file__)) + "/../static/js/"

khanexercisesurl = "https://github.com/Khan/khan-exercises/archive/master.zip"

exercisezip = requests.get(khanexercisesurl)

if exercisezip.status_code == 200:
    try:
        exercisefile = StringIO.StringIO(exercisezip.content)
        output = zipfile.ZipFile(exercisefile)
        output.extractall(data_path)
        shutil.rmtree(data_path + "khan-exercises")
        os.rename(data_path + "khan-exercises-master", data_path + "khan-exercises")
    except zipfile.BadZipfile:
        print "File stream was not a valid zip file"
else:
    print "Response ", exercisezip.status_code, " from server"

# subtitle zombie downloader
import json
import pdb
import os
import time

import subtitles

# json generated from aggregate_video_subtitles.py
srts_dict = json.loads(open(os.path.dirname(
    os.path.realpath(__file__)) + "/../static/data/video_srts.json").read())

success_counter = 0
for youtube_id, content in srts_dict.items():
	for code in content["language_codes"]:
		print "Attempting to download: " + youtube_id + ": " + code
		# pdb.set_trace()
		if subtitles.download_subtitles(youtube_id, code):
			success_counter += 1 
		time.sleep(0.5)
	print "Srts downloaded during this session: %s" % str(success_counter)

    

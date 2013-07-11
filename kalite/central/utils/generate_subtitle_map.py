# updates the file in static/data/subtitledata/video_srts.json
# can completely remap from Amara API or only re-check the ones
# from our data file that had HTTP errors during the previous API request

import argparse
import json
import logging
import time
import os
import sys

import requests

data_path = os.path.dirname(os.path.realpath(
	__file__)) + "/../../static/data/subtitledata/"

logger = logging.getLogger('generate_subtitles_map.py')


def update_subtitle_map(new_flag, code_to_check):
	# For new mapping, iterate through all videos
	if new_flag:
		nodecache = json.load(open(data_path + 'nodecache.json', 'r'))
		videos = nodecache['Video']
		new_json = {}
		for video, data in videos.iteritems():
			youtube_id = data['youtube_id']
			new_json.update(update_video_entry(youtube_id))
			# TODO(dylan) 3000+ videos - can't expect process to complete before
			# saving. need an interim step
		with open(data_path + 'video_srts.json', 'wb') as fp:
			json.dump(new_json, fp)

	# otherwise load the json file and only re-check specified videos
	else:
		srts_dict = json.loads(open(data_path + "video_srts.json").read())
		for youtube_id, data in srts_dict.items():
			response_code = data.get("api-response")
			if not response_code:
				return "This schema is old. Please run generate_subtitles_map.py -N to generate correct schema."
			elif code_to_check == "all" or response_code == code_to_check:
				srts_dict.update(update_video_entry(youtube_id))


def update_video_entry(youtube_id):
	"""Return a dictionary to be appended to the current schema:
		{ youtube_id: {
				"amara_code": "3x4mp1e",
				"language_codes": ["en", "es", "etc"],
				"api-response": "success",
			}
		}

	"""
	entry = {}
	request_url = "https://www.amara.org/api2/partners/videos?format=json&video_url=http://www.youtube.com/watch?v=%s" % (youtube_id)
	r = make_request(request_url)
	entry[youtube_id] = {
						"api-response": "",
					}
	# add api response first to prevent empty json on errors
	if r == "client-error" or r == "server-error":
		entry[youtube_id]["api-response"] = r
	else:
		entry[youtube_id]["api-response"] = "success"
		content = json.loads(r.content)
		# index into data to extract languages and amara code, then add them
		if content.get("objects"):
			languages = json.loads(r.content)['objects'][0]['languages']
			if languages: # ensuring it isn't an empty list
				amara_code = languages[0].get("subtitles_uri").split("/")[4]
				assert len(amara_code) == 12 # in case of future API change 
				entry[youtube_id]["amara_code"] = amara_code
				for language in languages:
					entry[youtube_id]["language_codes"].append(language['code'])
	return entry


def make_request(url):
	"""Return response from url; retry up to 5 times for server errors; when returning an error, return human-readable status code"""
	if not known_bad_url(url):
		for retries in range(1, 5):
			r = requests.get(url, headers=headers)
			if r.status_code > 499:
				logging.warning("Server error: %s at %s" % (str(r.status_code), url))
				if retries == 4:
					logging.info("Maxed out retries: adding %s to bad urls list" % url)
					r = "server-error"
			elif r.status_code > 399:
				logging.warning("Client error: %s at %s" % (str(r.status_code), url))
				logging.info("Adding %s to bad urls list" % url)
				r = "client-error"
				break
			else:
				logging.info("Good request: %s at %s" % (str(r.status_code), url))
	return r


def create_parser():
	# parses command line args
	parser = argparse.ArgumentParser()
	parser.add_argument('-N', '--new', action='store_true',
						help="Force a new mapping. Pings Amara's API for each and every one of our videos and overwrites current data with fresh data from Amara. Should be run fairly infrequently.")
	parser.add_argument('-c', '--check', default=None,
						help="Which status to recheck, options: 'all', 'client-error', or 'server-error'.")
	return parser

def setup_logging():
	logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s - %(levelname)s: %(message)s',
                    datefmt='%m-%d %H:%M')

if __name__ == '__main__':
	import pdb
	pdb.set_trace()
	setup_logging()
	parser = create_parser()
	args = parser.parse_args()
	if not args.check:
		logger.info("Please specifiy which srt status to check")
		parser.print_help()
		sys.exit(1)
	else:
		update_subtitle_map(args.new, args.check)



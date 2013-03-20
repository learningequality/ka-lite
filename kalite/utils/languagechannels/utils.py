"""
This script returns 
"""
import optparse
import logging
import urllib2	
from urllib2 import Request, urlopen, URLError, HTTPError
import json 
import pdb
import csv
import time 

def update_all_language_channels_json():
	"""
	References a built in YouTube KA Language Channel Dictionary to write
	new JSON files for each major YouTube API request. 
	"""
	logging.info("Updating all language channels:")
	channel_dictionary = language_channels_dictionary()
	for channel_id, language_code in channel_dictionary.iteritems():
		update_language_channel_json(channel_id)


def update_language_channel_json(channel_id):
	"""
	Takes a YouTube Channel ID and rewrites the related JSON files 
	according to API responses.
	"""
	uploads_json = channel_uploads(channel_id)
	playlists_json, playlist_ids_list = playlist_ids(channel_id)
	playlist_videos_json = {}
	for pl_id in playlist_ids_list:
		playlist_videos_json[pl_id] = playlist_videos(pl_id)

	full_channel_json = {
		"video_uploads": uploads_json,
		"playlists": playlists_json,
		"playlist_videos": playlist_videos_json
	}

	logging.info("Writing data to 'youtube_data/%s.json'." % channel_id)
	with open('youtube_data/%s.json' % channel_id, 'wb') as fp:
		json.dump(full_channel_json, fp)


def channel_uploads(channel_id):
	"""
	Returns the combined JSON YouTube API response of all the 
	channels uploaded videos.
	"""
	logging.info("Getting all uploads for %s" % channel_id)
	video_entries = []
	start_index = 1
	more_videos = True
	while more_videos:
		url = "https://gdata.youtube.com/feeds/api/users/%s/uploads?alt=json&max-results=50&start-index=%d" % (channel_id, start_index)
		response = make_request(url)
		if response.get("error"):
			logging.info("Setting more_videos to false to continue execution.")
			more_videos = False
		else: 
			entry = response.get("feed").get("entry")
			if entry == None:
				more_videos = False
			else:
				start_index += 50
				video_entries += entry
	return video_entries


def playlist_ids(channel_id):
	"""
	Returns the combined JSON YouTube API response of all the 
	playlists affiliated with the channel.
	"""
	logging.info("Getting all playlists for %s" % channel_id)
	playlist_ids = []
	url = "https://gdata.youtube.com/feeds/api/users/%s/playlists?v=2&alt=json&max-results=50" % channel_id
	response = make_request(url)
	if response.get("error"):
		logging.info("Returning empty dictionary & list, continuing execution.")
		return {}, []
	else:
		entry = response.get("feed").get("entry")
		if entry == None:
			return {}, []
		else: 
			for playlist_id in entry:
				begin = playlist_id["id"]["$t"].rfind(":") + 1
				playlist_ids.append(playlist_id["id"]["$t"][begin:])
			return entry, playlist_ids


def playlist_videos(playlist_id):
	"""Returns the combined JSON YouTube API response of all the videos in the playlist."""
	logging.info("Getting all videos for playlist: %s" % playlist_id)
	playlist_entries = []
	start_index = 1
	more_videos = True
	while more_videos:
		url = "http://gdata.youtube.com/feeds/api/playlists/%s?v=2&alt=json&max-results=50&start-index=%d" % (playlist_id, start_index) 
		response = make_request(url)
		if response.get("error"):
			loggin.info("Setting more_videos to false to continue execution.")
			more_videos = False
		else: 
			entry = response.get("feed").get("entry")
			if entry == None:
				more_videos = False
			else: 
				start_index += 50
				playlist_entries += entry
	return playlist_entries


def make_request(url):
	"""
	Makes an API request and handles errors, retrying up to 5 times if 
	there is an error.
	"""
	for n in range(5):
		time.sleep(1)
		try:
			request = urllib2.Request(url)
			response = json.load(urllib2.urlopen(request))
		except Exception, e:
			logging.error("Error during request. Trying again %d/5 times." % (n+1))
			logging.debug("Error: %s.\nURL: %s" % (e, url))
			response = { "error": e }
		else:
			break
	return response


def video_ids_set(channel_ids=None):
	"""
	Returns a set of all video IDs in the specified language channels. 
	Returns all video IDs if left empty.
	"""
	video_ids = set()       
	if channel_ids:
		logging.info("Set of video IDs for %s" % ", ".join(channel_ids))
		for channel_id in channel_ids:
			if ensure_existence(channel_id):
				video_ids.update(extract_ids(channel_id))
	else:
		logging.info("Returning set of all language channel video IDs")
		channel_list = language_channels_dictionary().keys()
		for channel_id in channel_list:
			video_ids.update(extract_ids(channel_id))
	return video_ids


def extract_ids(channel_id):
	"""
	Returns a set of video IDs that have been uploaded or included in 
	playlists of the channel
	"""
	video_ids = set()
	data = json.load(open('youtube_data/%s.json' % channel_id))
	# Extract uploaded video IDs 
	for entry in data["video_uploads"]:
		video_ids.add(entry["id"]["$t"].replace("http://gdata.youtube.com/feeds/api/videos/", ""))
	# Extract playlist video IDs
	for playlist_id in data["playlist_videos"]:
		for video in data["playlist_videos"][playlist_id]:
			video_ids.add(video["media$group"]["yt$videoid"]["$t"])
	return video_ids


def language_channels_dictionary():
	"""
	Returns a reference dictionary mapping all Khan Academy Language 
	Channel IDs to their language code.
	"""
	return json.load(open('known_channels.json'))

def ensure_existence(channel_id):
	"""
	Ensures that the language channel ID given exists inside the language 
	channel dictionary. 
	"""
	if not language_channels_dictionary().get(channel_id):
		return logging.error("'%s' is not a language channel. Check for misspellings and try again! :)" % channel_id)
	return True


def setup_logging():
	"""Sets log messages to display in the console"""
	logging.basicConfig(level=logging.INFO,
		format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


def main():
	"""Handles command line args directs the script"""
	parser = optparse.OptionParser()

	parser.add_option("-U", "--update", action="store_true", dest="update", 
		help="Request updated data on language channels via the YouTube API.",
		default=False)

	parser.add_option("-l", "--language-channel", action="append", 
		dest="language_channels", help="Languages to update. Ex: -l "
		"'KhanAcademyRussian' -l 'KhanAcademyDansk'. Default is all.",
		default=None)

	parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
		help="Suppress output.")

	parser.add_option("-v", "--videos", action="store_true", dest="videos_set",
		help="Return a set of videos for the specified language channels. "
		"If language channels are not specified it will return a set of all " 
		"video ids for all language channels.")

	options, args = parser.parse_args()

	if not options.quiet:
		setup_logging() 

	if options.update:
		if not options.language_channels:
			update_all_language_channels_json()
		else:
			for language_ch in options.language_channels:
				if ensure_existence(language_ch):
					update_language_channel_json(language_ch)

	if options.videos_set:
		return video_ids_set(options.language_channels)

	if not options.videos_set and not options.language_channels and not options.update:
		logging.info("Use --help to see runnable options.")


if __name__ == '__main__':
	main()
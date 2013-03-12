"""This script generates two CSV files - dubbed_videos.csv and summary_statistics.csv. 
Together they contain most relevant information on the KA Language Channels and the videos 
they have uploaded and added to their playlists. 

To run, simply use the command: 
    python language_channel_data.py
"""

import urllib2	
from urllib2 import Request, urlopen, URLError, HTTPError
import json 
import pdb
import dubbed_video_spreadsheet_extract
import csv 
import codecs 
import time
import logging
import prettytable

def collect_channel_videos(user_id):
	"""Returns a dictionary mapping each video to its viewing statistics.
		E.g.
		{ "sdkj89w_Ds": {
			"avg_rating": 4.3,
			"num_raters": 2,
			"favorite_count": 0,
			"view_count": 5
		}, etc.}
	"""
	all_videos_stats = {}
	start_index = 1
	more_videos = True
	while more_videos:
		url = "https://gdata.youtube.com/feeds/api/users/%s/uploads?alt=json&max-results=50&start-index=%d" % (user_id, start_index)
		response = make_request(url)
		if response.get("error"):
			print "Error during request. Channel ID is %s. Check error_log.txt for more info." % user_id
			print "Setting more_videos to false to continue execution."
			more_videos = False
		else: 
			entry = response.get("feed").get("entry")
			if entry == None:
				more_videos = False
			else:
				start_index += 50
				for video in entry:
					video_id = video["id"]["$t"].replace("http://gdata.youtube.com/feeds/api/videos/", "")
					all_videos_stats = get_video_stats(all_videos_stats, video, video_id)
	return all_videos_stats


def playlist_ids(user_id):
	"""Returns a dictionary mapping the playlist ID to its title
		E.g.
		{ "PL91B49E8280E58313": "Arytmetyka", etc.}
	"""
	url = "https://gdata.youtube.com/feeds/api/users/%s/playlists?v=2&alt=json&max-results=50" % user_id
	response = make_request(url)
	if response.get("error"):
		print "Error during request for playlist ID's for user: %s. Check error_log.txt for more information." % user_id
		print "Returning empty lists and dictionaries, continuing execution."
		return {}
	else:
		entry = response.get("feed").get("entry")
		if entry == None:
			return {}
		else: 
			playlist_titles_dict = {}
			for playlist_id in entry:
				begin = playlist_id["id"]["$t"].rfind(":") + 1
				pl_id = playlist_id["id"]["$t"][begin:]
				playlist_title = playlist_id["title"]["$t"].encode("UTF-8")
				playlist_titles_dict[pl_id] = playlist_title
			return playlist_titles_dict


def playlist_videos(playlist_id):
	"""Returns a dictionary mapping the video ID to its playlist ID, and a dictionary mapping 
		each video ID to it's viewership stats
		Video -> Playlist Map example: 
		{ "PL91B49E8280E58313": "Arytmetyka", etc.}
		Video -> Stats example:
		{ "sdkj89w_Ds": {
			"avg_rating": 4.3,
			"num_raters": 2,
			"favorite_count": 0,
			"view_count": 5
		}, etc.}
	"""	
	video_ids = []
	playlist_map = {}
	all_videos_stats = {}
	start_index = 1
	more_videos = True
	while more_videos:
		url = "http://gdata.youtube.com/feeds/api/playlists/%s?v=2&alt=json&max-results=50&start-index=%d" % (playlist_id, start_index) 
		response = make_request(url)
		if response.get("error"):
			print "Error inside playlist videos where playlist ID is %s" % playlist_id
			print "Setting more_videos to false to continue execution."
			more_videos = False
		else: 
			entry = response.get("feed").get("entry")
			if entry == None:
				more_videos = False
			else: 
				start_index += 50
				for video in entry:
					video_id = video["media$group"]["yt$videoid"]["$t"]
					video_ids.append(video_id)
					playlist_map[video_id] = playlist_id
					all_videos_stats = get_video_stats(all_videos_stats, video, video_id)
	return playlist_map, all_videos_stats

def get_video_stats(stats_dict, video_obj, video_id):
	"""Returns a dictionary mapping the video's ID to it's viewing stats."""
	stats_dict[video_id] = {
		"avg_rating": '',
		"num_raters": '',
		"favorite_count": '',
		"view_count": ''
	}
	if video_obj.get("gd$rating"):
		stats_dict[video_id]["avg_rating"] = video_obj.get("gd$rating").get("average")
		stats_dict[video_id]["num_raters"] = video_obj.get("gd$rating").get("numRaters")
	if video_obj.get("yt$statistics"):
		stats_dict[video_id]["favorite_count"] =  video_obj.get("yt$statistics").get("favoriteCount")
		stats_dict[video_id]["view_count"] = video_obj.get("yt$statistics").get("viewCount")
	return stats_dict

def make_request(url):
	# Try up to 5 times
	for n in range(5):
		time.sleep(1)
		try:
			request = urllib2.Request(url)
			response = json.load(urllib2.urlopen(request))
		except Exception, e:
			print "Error during request. Trying again %d/5 times." % (n+1)
			logging.debug("Error: %s.\nURL: %s" % (e, url))
			response = { "error": e }
		else:
			break
	return response

def videos_in_playlists(user_id):
	playlist_titles_dict = playlist_ids(user_id)
	playlists = playlist_titles_dict.keys()
	ids_in_playlists = []
	playlist_mapping = {}
	all_videos_stats = {}
	for pl in playlists:
		pl_map, new_videos_stats = playlist_videos(pl)
		all_videos_stats.update(new_videos_stats)
		playlist_mapping.update(pl_map)
		for video in playlist_mapping.keys():
			ids_in_playlists.append(video)
	return ids_in_playlists, playlist_mapping, playlist_titles_dict, all_videos_stats


def create_dubbed_csv(spreadsheet_json):
	# CSV stuff
	f = codecs.open("dubbed_videos.csv", "wt")
	s = codecs.open("summary_statistics.csv", "wt")
	dubbed_csv = csv.writer(f)
	summary_statistics = csv.writer(s)
	dubbed_csv.writerow(["Channel Name", "Language Code", "YouTube ID", "URL", "Playlist ID", "Playlist Title", "English Video ID", "Average Rating", "Number of Ratings", "Favorite Count", "View Count"])
	summary_statistics.writerow(["Channel Name", "Language Code", "URL", "Videos Uploaded", "Playlists", "Videos in Playlists", "Videos NOT in Playlists", "NOT in Spreadsheet"])
	# Recording stuff
	not_in_spreadsheet = {}
	current_cycle = 0
	language_cycles = len(yt_channel_dict.keys())
	for channel_id, language_code in yt_channel_dict.iteritems():
		t1 = time.time()
		current_cycle += 1
		print "**********\nStarting to index %s..." % channel_id
		# Get all videos in channel
		channel_videos_stats = collect_channel_videos(channel_id)
		channel_videos = channel_videos_stats.keys()
		# Get all playlist info
		playlist_videos_list, map_of_playlists, playlist_titles_dict, playlist_videos_stats = videos_in_playlists(channel_id)
		# Combine data
		channel_videos_stats.update(playlist_videos_stats)
		all_videos_set = set(playlist_videos_list + channel_videos)
		playlist_videos_set = set(playlist_videos_list)
		channel_videos_set = set(channel_videos)
		channel_videos_not_in_playlists_set = channel_videos_set - playlist_videos_set
		# Compare to spreadsheet extraction
		if not spreadsheet_json.get(language_code):
			not_in_spreadsheet[language_code] = all_videos_set
		else:
			in_spreadsheet_set = set(spreadsheet_json.get(language_code).keys()) - set([""])
			not_in_spreadsheet[language_code] = all_videos_set - in_spreadsheet_set
		# Add a row for each video in this channel	
		for video_id in all_videos_set:
			playlist_id = map_of_playlists.get(video_id)
			video_stats = channel_videos_stats[video_id]
			if spreadsheet_json.get(language_code):
				english_vid_id = spreadsheet_json.get(language_code).get(video_id)
			else: 
				english_vid_id = ''
			dubbed_row = [channel_id, language_code, video_id, "http://www.youtube.com/watch?v=%s" % video_id, playlist_id, playlist_titles_dict.get(playlist_id), english_vid_id, video_stats["avg_rating"], video_stats["num_raters"], video_stats["favorite_count"], video_stats["view_count"]]
			dubbed_csv.writerow(dubbed_row)
		summary_row = [channel_id, language_code, "http://www.youtube.com/user/%s" % channel_id, len(channel_videos_set), len(set(map_of_playlists.values())), len(playlist_videos_set), len(channel_videos_not_in_playlists_set), len(not_in_spreadsheet[language_code])]
		summary_statistics.writerow(summary_row)
		# Draw console summary table for finished Language Channel
		t2 = time.time()
		time_taken = t2-t1
		summary_table = prettytable.PrettyTable(["Channel Name", "Time Taken", "Videos Uploaded", "Playlists", "Videos in Playlists", "Videos NOT in Playlists", "NOT in Spreadsheet"])
		summary_table.add_row([channel_id, time_taken, len(channel_videos_set), len(set(map_of_playlists.values())), len(playlist_videos_set), len(channel_videos_not_in_playlists_set), len(not_in_spreadsheet[language_code])])
		print "%s completed. (%d/%d languages done)." % (channel_id, current_cycle, language_cycles)
		print summary_table

yt_channel_dict = {
	"KhanAcademyAfrikaans": "af",
	"KhanAcademyAlbanian": "sq",
	"KhanAcademyArabi": "ar",
	"KhanAcademyArmenian": "hy",
	"KhanAcademyAzeri": "az",
	"KhanAcademyBahasaInd": "id",
	"KhanAcademyBMalaysia": "ms",
	"KhanAcademyBangla": "bn",
	"KhanAcademyBulgarian": "bg",
	"KhanAcademyBurmese": "my",
	"KhanAcademyCzech": "cs",
	"KhanAcademyDansk": "da",
	"KhanAcademyDari": "fa_AD",
	"KhanAcademyDeutsch": "de",
	"KhanAcademyEspanol": "es",
	"KhanAcademyFarsi": "fa",
	"KhanAcademyFrancais": "fr",
	"KhanAcademyGreek": "el",
	"KhanAcademyGujarati": "gu",
	"KhanAcademyHebrew": "he",
	"KhanAcademyHindi": "hi",
	"KhanAcademyItaliano": "it",
	"KhanAcademyJapanese": "ja",
	"KhanAcademyKannada": "kn",
	"KhanAcademyKhmer": "km",
	"KhanAcademyKiswahili": "sw",
	"KhanAcademyKorean": "ko",
	"KhanAcademyMagyar": "hu",
	"KhanAcademyMalayalam": "ml",
	"KhanAcademyMandarin": "zn",
	"KhanAcademyMarathi": "mr",
	"KhanAcademyMongolian": "mn",
	"KhanAcademyNederland": "nl",
	"KhanAcademyNepali": "ne",
	"KhanAcademyNorsk": "nn",
	"KhanAcademyOromo": "om",
	"KhanAcademyPashto": "ps",
	"KhanAcademyPolski": "pl",
	"KhanAcademyPortugues": "pt_BR",
	"KhanAcademyPortugal": "pt",
	"KhanAcademyPunjabi": "pa",
	"KhanAcademyRussian": "ru",
	"KhanAcademySindhi": "sd",
	"KhanAcademySinhala": "si",
	"KhanAcademySvenska": "sv",
	"KhanAcademyTagalog": "tl",
	"KhanAcademyTamil": "ta",
	"KhanAcademyTelugu": "te",
	"KhanAcademyThai": "th",
	"KhanAcademyTiengViet": "vi",
	"KhanAcademyTurkce": "tr",
	"KhanAcademyUkrainian": "uk",
	"KhanAcademyUrdu": "ur",
	"KhanAcademyXhosa": "xh"
}


if __name__ == '__main__':
	logging.basicConfig(filename='error_log.txt', level=logging.DEBUG, filemode='w')
	print "Extracting information from spreadsheet..."
	spreadsheet_json = dubbed_video_spreadsheet_extract.map_dubbed_ids("../static/data/dubbedvideoslist.xlsx", "Master List")
	create_dubbed_csv(spreadsheet_json)
	print "**********************************"
	print "Excellent! Check out the file 'summary_statistics.csv' for a summary of the language channel statistics and 'dubbed_videos.csv' for information on each video."
	print "The files will be in the same directory as this script."
	print "**********************************"






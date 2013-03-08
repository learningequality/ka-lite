# This script 

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
from functools import wraps

def collect_channel_videos(user_id):
	"""Returns a dictionary mapping each video to its viewing statistics."""
	videos_stats = {}
	start_index = 1
	more_videos = True
	while more_videos:
		url = "https://gdata.youtube.com/feeds/api/users/%s/uploads?alt=json&max-results=50&start-index=%d" % (user_id, start_index)
		response = make_request(url)
		if response.get("error"):
			# print response["error"]
			print "Error inside channel video ids where channel ID is %s" % user_id
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
					videos_stats[video_id] = {
						"avg_rating": '',
						"num_raters": '',
						"favorite_count": '',
						"view_count": ''
					}
					if video.get("gd$rating"):
						videos_stats[video_id]["avg_rating"] = video.get("gd$rating").get("average")
						videos_stats[video_id]["num_raters"] = video.get("gd$rating").get("numRaters")
					if video.get("yt$statistics"):
						videos_stats[video_id]["favorite_count"] =  video.get("yt$statistics").get("favoriteCount")
						videos_stats[video_id]["view_count"] = video.get("yt$statistics").get("viewCount")
						
	# print "There are %d video_ids for %s" % (len(video_ids), user_id)
	# print video_ids
	return videos_stats


def playlist_ids(user_id):
	"""Returns a dictionary mapping the playlist ID to its title"""
	url = "https://gdata.youtube.com/feeds/api/users/%s/playlists?v=2&alt=json&max-results=50" % user_id
	response = make_request(url)
	if response.get("error"):
		# print response["error"]
		print "Error inside playlist IDs: %s" % user_id
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
			# print "There are %d playlists in %s's Channel" % (len(playlist_ids), user_id)
			# print playlist_ids
			return playlist_titles_dict


def playlist_videos(playlist_id):
	# helper function for videos_in_playlist - returns list of video ids in the playlist 
	video_ids = []
	playlist_map = {}
	videos_stats = {}
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
					videos_stats[video_id] = {
						"avg_rating": '',
						"num_raters": '',
						"favorite_count": '',
						"view_count": ''
					}
					if video.get("gd$rating"):
						videos_stats[video_id]["avg_rating"] = video.get("gd$rating").get("average")
						videos_stats[video_id]["num_raters"] = video.get("gd$rating").get("numRaters")
					if video.get("yt$statistics"):
						videos_stats[video_id]["favorite_count"] =  video.get("yt$statistics").get("favoriteCount")
						videos_stats[video_id]["view_count"] = video.get("yt$statistics").get("viewCount")
		# print "There are %d videos in this playlist, id: %s" % (len(video_ids), playlist_id)
		# print video_ids
		# return video_ids
	return playlist_map, videos_stats

def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck, e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print msg
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry

@retry(urllib2.URLError, tries=3, delay=3, backoff=3)
def make_request(url):
	request = urllib2.Request(url)
	try: 
		response = json.load(urllib2.urlopen(request))
		time.sleep(1)
	except HTTPError, e: 
		logging.debug("HTTP Error... URL: %s" % (url))
		logging.debug("Error code: %s" % e.code)
		# logging.debug("Error: %s" % e)
		return { "error": e }
	except URLError, e: 
		logging.debug("URL Error... URL: %s" % (url))
		logging.debug("Reason for error: %s" % e.reason)
		# logging.debug("Error: %s" % e)
		return { "error": e }
	except Exception, e:
		logging.debug("So, it has come to this... %s " % e ) 
		logging.debug("tried this url %s" % url)
		logging.debug("Setting more videos to false for the sake of sanity...")
		return { "error": e }
	else:
		return response

def videos_in_playlists(user_id):
	playlist_titles_dict = playlist_ids(user_id)
	playlists = playlist_titles_dict.keys()
	ids_in_playlists = []
	playlist_mapping = {}
	videos_stats = {}
	for pl in playlists:
		pl_map, new_videos_stats = playlist_videos(pl)
		videos_stats.update(new_videos_stats)
		playlist_mapping.update(pl_map)
		for video in playlist_mapping.keys():
			ids_in_playlists.append(video)
	# print "There are %d videos in %d playlists." % (len(ids_in_playlists), len(playlists))
	# print video_ids
	return ids_in_playlists, playlist_mapping, playlist_titles_dict, videos_stats


def create_dubbed_csv():
	# Reference 
	not_in_spreadsheet = {}
	f = codecs.open("dubbed_videos_updated.csv", "wt")
	s = codecs.open("summary_statistics_updated.csv", "wt")
	dubbed_csv = csv.writer(f)
	summary_statistics = csv.writer(s)
	dubbed_csv.writerow(["Channel Name", "Language Code", "YouTube ID", "URL", "Playlist ID", "Playlist Title", "English Video ID", "Average Rating", "Number of Ratings", "Favorite Count", "View Count"])
	summary_statistics.writerow(["Channel Name", "Language Code", "URL", "Videos Uploaded", "Playlists", "Videos in Playlists", "Videos NOT in Playlists", "NOT in Spreadsheet"])

	i = 0
	language_cycles = len(yt_channel_dict.keys())
	for channel_id, language_code in yt_channel_dict.iteritems():
		t1 = time.time()
		print "**********\nStarting to index %s..." % channel_id
		i += 1
		channel_videos_stats = collect_channel_videos(channel_id)
		channel_videos = channel_videos_stats.keys()
		playlist_videos_list, map_of_playlists, playlist_titles_dict, playlist_videos_stats = videos_in_playlists(channel_id)
		# pdb.set_trace()
		channel_videos_stats.update(playlist_videos_stats)
		all_videos_set = set(playlist_videos_list + channel_videos)
		playlist_videos_set = set(playlist_videos_list)
		channel_videos_set = set(channel_videos)
		channel_videos_not_in_playlists_set = channel_videos_set - playlist_videos_set

		if not spreadsheet_json.get(language_code):
			not_in_spreadsheet[language_code] = all_videos_set
		else:
			in_spreadsheet_set = set(spreadsheet_json.get(language_code).keys()) - set([""])
			not_in_spreadsheet[language_code] = all_videos_set - in_spreadsheet_set

		for video_id in all_videos_set:
			playlist_id = map_of_playlists.get(video_id)
			# pdb.set_trace()
			video_stats = channel_videos_stats[video_id]
			if spreadsheet_json.get(language_code):
				english_vid_id = spreadsheet_json.get(language_code).get(video_id)
			else: 
				english_vid_id = ''
			dubbed_row = [channel_id, language_code, video_id, "http://www.youtube.com/watch?v=%s" % video_id, playlist_id, playlist_titles_dict.get(playlist_id), english_vid_id, video_stats["avg_rating"], video_stats["num_raters"], video_stats["favorite_count"], video_stats["view_count"]]
			dubbed_csv.writerow(dubbed_row)

		# pdb.set_trace()
		summary_row = [channel_id, language_code, "http://www.youtube.com/user/%s" % channel_id, len(channel_videos_set), len(set(map_of_playlists.values())), len(playlist_videos_set), len(channel_videos_not_in_playlists_set), len(not_in_spreadsheet[language_code])]
		summary_statistics.writerow(summary_row)

		t2 = time.time()
		time_taken = t2-t1
		summary_table = prettytable.PrettyTable(["Channel Name", "Time Taken", "Videos Uploaded", "Playlists", "Videos in Playlists", "Videos NOT in Playlists", "NOT in Spreadsheet"])
		summary_table.add_row([channel_id, time_taken, len(channel_videos_set), len(set(map_of_playlists.values())), len(playlist_videos_set), len(channel_videos_not_in_playlists_set), len(not_in_spreadsheet[language_code])])
		print "%s completed. (%d/%d languages done)." % (channel_id, i, language_cycles)
		print summary_table

	# print "*** %s ***" % channel_id
	# print "There are %d video IDs on the channel that have not been assigned to any playlists:" % len(channel_videos_not_in_playlists_set)
	# print ', '.join(channel_videos_not_in_playlists_set)
	# print ""
	# print "There are %d video IDs missing from the spreadsheet:" % len(not_in_spreadsheet[language_code])
	# print ', '.join(not_in_spreadsheet[language_code])
	# print "\n"

spreadsheet_json = dubbed_video_spreadsheet_extract.map_dubbed_ids("../static/data/dubbedvideoslist.xlsx", "Master List")
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
	create_dubbed_csv()
	print "**********************************"
	print "Excellent! Check out the file 'summary_statistics.csv' for a summary of the language channel statistics and 'dubbed_videos.csv' for information on each video."
	print "The files will be in the same directory as this script."
	print "**********************************"






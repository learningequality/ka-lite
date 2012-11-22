import requests, json, os

data_path = os.path.dirname(os.path.realpath(__file__)) + "/../static/data/"

base_url = "https://www.universalsubtitles.org/api2/partners/videos"

nodecache = json.load(open(data_path + 'nodecache.json','r'))

videos = nodecache['Video']

videolanguages = {}

languagenos = {}

for video,data in videos.iteritems():
    r = requests.get("%s?video_url=http://www.youtube.com/watch?v=%s" % (base_url, data['youtube_id']))
    content = json.loads(r.content)
    if content.has_key("objects"):
        languages = json.loads(r.content)['objects'][0]['languages']
        videolanguages[video] = []
        for language in languages:
            videolanguages[video].append(language['code'])
            if languagenos.has_key(language['code']):
                languagenos[language['code']] += 1
            else:
                languagenos[language['code']] = 1
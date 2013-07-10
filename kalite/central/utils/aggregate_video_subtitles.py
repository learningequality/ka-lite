import requests, json, os, time

data_path = os.path.dirname(os.path.realpath(__file__)) + "/../static/data/"

base_url = "https://www.amara.org/api2/partners/videos"

nodecache = json.load(open(data_path + 'nodecache.json','r'))

videos = nodecache['Video']

videolanguages = {}

languagenos = {}

srts_dict = json.loads(open(os.path.dirname(
    os.path.realpath(__file__)) + "/../static/data/video_srts.json").read())

counter = 0
for video,data in videos.iteritems():

    if not videos_dict.get(video):
        for retries in range (1, 5):
            r = requests.get("%s?format=json&video_url=http://www.youtube.com/watch?v=%s" % (base_url, data['youtube_id']))
            if r.status_code < 399:
                break
            else:
                continue
        try: 
            content = json.loads(r.content)
        except:
            import pdb
            pdb.set_trace()
            continue # will skip this video... not perfect
        else: 
            if content.has_key("objects"):
                languages = json.loads(r.content)['objects'][0]['languages']
                if len(languages) > 0:
                    amara_code = languages[0].get("subtitles_uri").split("/")[4]
                    assert len(amara_code) == 12 #think they are uniform ids, could be wrong :)
                    videolanguages[data['youtube_id']] = {
                        "amara_code": amara_code,
                        "language_codes": []
                    }
                    for language in languages:
                        videolanguages[data['youtube_id']]["language_codes"].append(language['code'])
                        if languagenos.has_key(language['code']):
                            languagenos[language['code']] += 1
                        else:
                            languagenos[language['code']] = 1
    else:
        print "Already did this one"
    counter += 1
    time.sleep(0.25)
    print "Loop: %s, ID: %s" % (str(counter), data['youtube_id'])
    # print "Youtube ID: %s" % data['youtube_id']
    if(counter%50 == 0):
        print "Writing to JSON to store what we got at loop number " + str(counter)
        with open('video_srts.json', 'wb') as fp:
            json.dump(videolanguages, fp)
    # else: 
    #     print "Loop: %s" % str(counter)


    

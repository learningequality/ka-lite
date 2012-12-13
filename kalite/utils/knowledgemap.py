import requests, json, os, sys

baseurl = "http://www.khanacademy.org/api/v1/"

download_path = os.path.dirname(os.path.realpath(__file__)) + "/../static/data/"

maplayout = requests.get(baseurl + "topicversion/default/maplayout")

maplayoutfile = file(download_path+"maplayout_data.json","w")

maplayout_data = json.loads(maplayout.content)

json.dump(maplayout_data,maplayoutfile)

maplayoutfile.close()

exceptions = {
    "multiplication-division": ["arithmetic_word_problems", "negative_number_word_problems"],
    "conic-sections": ["parabola_intuition_3"]
}

for key,value in maplayout_data["topics"].items():
    topicget = requests.get(baseurl + "topic/%s/exercises" % key)
    print topicget.content
    topicdata = json.loads(topicget.content)
    
    if exceptions.has_key(key):
        topic_exceptions = exceptions[key]
    else:
        topic_exceptions = []
           
    if topic_exceptions:
        for i,exercise in enumerate(topicdata):
            if exercise["name"] in topic_exceptions:
                topicdata[i] = []
    
    topicfile = file(download_path + "topicdata/%s.json" % key,"w")
    json.dump(topicdata,topicfile)
    topicfile.close()
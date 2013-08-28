import requests, json, os

save_path = os.path.dirname(os.path.realpath(__file__)) + "/../static/data/subtitles/"

get_langs = requests.get('https://amara.org/api2/partners/languages/?format=json')

langs = json.loads(get_langs.content)

langs = langs['languages']

output = open(save_path + 'languagelookup.json','w')

json.dump(langs, output)

output.close()
import requests, json, os

save_path = os.path.dirname(os.path.realpath(__file__)) + "/../static/data/"

get_langs = requests.get('https://staging.universalsubtitles.org/api2/partners/languages/')

langs = json.loads(get_langs.content)

langs = langs['languages']

output = open(save_path + 'languages.json','w')

json.dump(langs, output)

output.close()
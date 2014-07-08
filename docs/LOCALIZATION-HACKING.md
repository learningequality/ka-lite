# How to (hopefully) hack together a localized version of KA Lite 

#### We expect to have full i18n support by early 2014, but if you have a project that needs KA Lite i18n'd before that, here's some basic instructions on how you can try and make that happen.

*Please note that the KA Lite team regretfully does not have the bandwidth to support anything if it goes wrong for you. We are working as hard as we can to make this available for everyone as soon as possible!*

## Ordered Steps
### 1. Obtain Background Knowledge

1. Understand that KA Lite is a [Django Application](https://www.djangoproject.com/). If you are unfamiliar with Python and Django, all is not lost, but having a basic understanding will make things easier. 

2. Understand [Django's approach to internationalization](https://docs.djangoproject.com/en/dev/topics/i18n/translation/). Start with the KA Lite i18n Documentation (sibling to this document), and then read Django's Internationalization Docs. 

### 2. Understand the three parts to internationalization

1. User interface translations. This is what the i18n docs are all about. 

2. Subtitle support. (For your purposes, this already exists! You don't have to worry about it.)

3. Dubbed videos.

**So we need to focus on UI translations and dubbed video support.**

### 3. Getting KA Lite UI translations

*If these instructions don't make sense, please read the i18n documentation for KA Lite and the Django i18n docs again*

1. Encourage volunteer translators to complete the translations of [KA Lite's UI](http://crowdin.net/project/ka-lite) and of [Khan Academy's content](http://crowdin.net/project/khanacademy). Please be aware that not all KA content get's reused in KA Lite. Please ask your translators to focus on the content under the folder _high_priority_content. Everything in this section, with the exception of the _learn_math.applied-math.articles folder, are video titles, descriptions, and exercise content, which is shared by KA Lite.  

2. Download the po files from the CrowdIn links in (1). You should have two po files for KA Lite and quite a few for the content directory. Put all of these po files in the locale directory: `locale/<your_lang_code>/LC_MESSAGES/<put_po_files_here>`

3. Run `compilemessages` (re-read i18n docs if this isn't familiar)

4. In the `settings.py` folder, make sure you change LANGUAGE_CODE = "<your_lang_code>"

5. Run the server and keep your fingers crossed. :+1:


### 4. Adding in Dubbed Video Support

1. KA Lite loads in video content using the `content/` directory and the json file `kalite/static/data/topics.json`. Take a look at that json data.

2. Basically, what you have to do is put your videos inside of the content directory and update the json file to reflect your videos instead of Khan Academy's. It's not super simple, but it isn't that hard either. It's mostly a matter of working out which dubbed video corresponds to which KA video, replacing the metadata in the JSON with the metadata you have, and then trial and error. I will do my best to add more to this later, but with perserverance, hopefully I have given you enough to work with to accomplish your goal.
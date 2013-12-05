___Setting up a Spanish-language demo___
* To the file `ka-lite/kalite/local_settings.py`, add the following lines:
    * `CENTRAL_SERVER_HOST = "kalite.learningequality.org:7007"`
    * `SECURESYNC_PROTOCOL = "http"`
    * `CACHE_TIME = 0`
* Run `scrape_videos -l es` to get all the dubbed videos
* Run `scrape_exercises -l es` to get all the localized exercises.
* Install the spanish language pack
    * Start the server
    * Log in as the admin user
    * Go to Updates, choose "Manage" language packs.
    * In the dropdown, select spanish, and click "get language pack"
* Select spanish as the default language

DONE!!!

___Want to have more language packs available?___

1. Log into the central server
2. In the `ka-lite-develop/kalite` folder, run `./manage.py update_language_packs -l [lang_code]
    * Useful language codes: de (German), ar (Arabic), zh-CN (simplified Chinese), pt-BR (brazilian portuguese), en (english)
3. Go back to your distributed server, and refresh--you'll find the language packs there.

___New commands___
* `scrape_videos -l es` - [run on distributed server] download all known dubbed videos in spanish, from youtube, and save as mp4
    * NOTE: Only the following languages are supported: `da`, `he`, `pt-BR`, `tr`, `es`
* `scrape_exercises -l es` - [run on distributed server] download all exercises in spanish, from khan academy, and put them in the proper place for use.


___Download Videos___

Using this to download: http://rg3.github.io/youtube-dl/index.html

This spreadsheet (or other list, wink-wink) to pick the videos: https://docs.google.com/a/learningequality.org/spreadsheet/ccc?key=0AhvqOn88FUVedEM5U3drY3E1MENfeWlLMVBnbnczT3c#gid=13

Sample command: youtube-dl --id -f mp4 www.youtube.com/watch?v=Pytw-oTpUNk
Downloaded:  حل المعادلات التربيعية بالتحليل إلى العوامل-Pytw-oTpUNk.mp4 for me :)
rename the Pytw-oTpUNk.mp4
DONE!

___Download Localized Exercises___

1. Download https://es.khanacademy.org/khan-exercises/exercises/vertical_angles.html?lang=es
2. Put into the `ka-lite/kalite/static/js/khan-exercises/exercises/` folder to replace the english version
3. Repeat for all files in the directory!

[note: this works!]

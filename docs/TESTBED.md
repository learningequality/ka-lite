Setting up KA Lite testing servers
===

### Basic setup (one-time only)
1. Fork the `learningequality/ka-lite.git` repository into your own github.com account
2. Clone your github.com ka-lite.git (remote) repository to your local machine
3. Install the KA Lite server (from the `ka-lite` directory, run `install.sh` or `install.bat`)


### Testing a distributed server
1. From the `ka-lite/kalite` directory, run `python manage.py runserver 8008`
2. Browse your web browser to [http://localhost:8008/](http://localhost:8008/)


### Testing CENTRAL server
1. Create file `kalite/local_settings.py`
2. Add the following to local_settings.py:    
`DEBUG=True`  
`CENTRAL_SERVER=True`

3. Run `python kalite/manage.py syncdb --migrate` to set up the CENTRAL server database.
4. Run `python kalite/manage.py runserver 8001` to start the CENTRAL server.
5. Browse your web browser to [http://127.0.0.1:8001/](http://127.0.0.1:8001/)


### Testing Central Server Registration
0. Follow the steps above for "Testing Central Server" 
1. Enable viewing sent emails, either by outputting to the console, or by actually sending.
    * **Outputting to the console (emails not actually sent):** (preferred)
        1. Add the following line to kalite/local_settings.py    
`EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"`  
    * Actually sending (sending email via http): (used in special cases)
        1. Install httplib2 python module from (https://code.google.com/p/httplib2/downloads/list)
        2. Register for an account at (http://postmarkapp.com)
        3. At (http://postmarkapp.com), add a signature email for test email address (that you have control of)
        4. At (http://postmarkapp.com), go to servers->credentials and copy the API key
        5. Add the following line to kalite/local_settings.py  
        `POSTMARK_API_KEY = "[your api key]"`  
        6. Add the following lines to kalite/local_settings.py:    
`CENTRAL_FROM_EMAIL    = "[your 'signature' email address]"`  
`CENTRAL_ADMIN_EMAIL   = "[your 'signature' email address]"`  
`CENTRAL_CONTACT_EMAIL = "[your 'signature' email address]"`  

2. Run `python kalite/manage.py runserver 8001` to start the CENTRAL server.
3. Browse your web browser to [http://127.0.0.1:8001/accounts/register/](http://127.0.0.1:8001/accounts/register/)
4. When you register, all "emails" will be printed to the console, rather than sent to you.


### Testing securesync completely locally
1. Set up one clone running KA lite local server (default).  Call this "LOCAL" below.
2. Set up one clone running KA lite "central".  Call this "CENTRAL" below.
    1. Create second clone (git clone git@github.com/[etc...] central) in the "central" directory, and "install".
    2. Set up "Testing Central Server" (see above)
    3. Set up "Testing Central Server Registration" (see above)
3. On LOCAL, add the following to local_settings.py:

`CENTRAL_SERVER_DOMAIN = "127.0.0.1:8001"`  
`CENTRAL_SERVER_HOST   = "127.0.0.1:8001"`  
`SECURESYNC_PROTOCOL   = "http"`  

4. on LOCAL, run `python kalite/manage.py runserver 8008` to start the server.
5. Register the LOCAL server with the CENTRAL server
    1. Browse to LOCAL on url (http://localhost:8008/securesync/register/)
    2. Click the link to "log into the central server".  Either log in, or create an account and log in.
    3. Create an "organization" and "zone", if necessary (these are auto-created for all users except the central server admin)
    4. Click the link to "register this device in a zone".  
    5. Select your zone, and click the "register" button.
6. On LOCAL, run `python manage.py generaterealdata` to generate test data.
7. On LOCAL, run `python manage.py syncmodels` to begin the syncing process.  The output should confirm that syncing has occurred.


### Creating and Testing Interface Translations
Note: many questions about i18n with Django can be answered via the [Django i18n Docs](https://docs.djangoproject.com/en/dev/topics/i18n/translation/)

1. First, make sure you have the [GNU gettext toolset](https://www.gnu.org/software/gettext/) installed. If you have any trouble, try Googling "[How to install GNU gettext toolset for [insert-operating-system-here]](http://lmgtfy.com/?q=how+do+I+install+GNU+gettext+toolset+on+Mac)"

2. Next, navigate to the project root directory (e.g. ```[local-path-to-ka-lite]/ka-lite/```)

3. Run the ```makemessages``` command to generate po files for the languages you want. Read the docs linked above for more info on how this process works. Example: ```python kalite/manage.py makemessages -l en``` to generate po files for English. This example will create a ```django.po``` file in the ```locale/en/LC_MESSAGES``` directory.

4. Run the ```makemessages``` command again to generate po files for javascript. Example: ```python kalite/manage.py makemessages -d djangojs -l en```. This example will create a ```djangojs.po``` file in the ```locale/en/LC_MESSAGES``` directory.

5. Inspect the two files you have generated. You should see something like:


    #: kalite/central/views.py:85
    msgid "Account administration"
    msgstr ""


    **Explanation**: each msgid string is a string in the KA Lite codebase. Each msgstr is where the translation for this language goes. Since this is an English po file and KA Lite is in English, no translation is necessary, but for testing, pick a string to translate into something else. 


6. Find ```msgid "Admin"``` and translate it to something fun: e.g. ```msgstr "I'm in Hawaii lol"```

7. Now that we have updated our translations, we need to compile the po files into a mo file so that it can be rendered by Django. To do that, we use the ```compilemessages``` command. Example: ```python kalite/manage.py compilemessages -l en```. This command compiles each po file in the ```en``` language directory and if you've been following along, should have created two new files: ```django.mo``` and ```djangojs.mo```. 

8. Now, restart your local server and check out your translations! Note: Not seeing your translations? It *could* be a caching problem! Try opening in a different browser, clearing your cache, or turning caching off. 

####Common Error Messages 
- Error: This script should be run from the Django SVN tree or your project or app tree. If you did indeed run it from the SVN checkout or your project or application, maybe you are just missing the conf/locale (in the django tree) or locale (for project and application) directory? It is not created automatically, you have to create it by hand if you want to enable i18n for your project or application. **Solution**: You need to create an empty ```locale``` directory in the project root ```path-to-kalite/ka-lite/locale/```. After creating, try running ```makemessages``` again. 
- python: can't open file 'manage.py': [Errno 2] No such file or directory. **Solution**: ensure that when you are running manage.py commands from the project root, you specify where to find manage.py, e.g. python kalite/manage.py [command]



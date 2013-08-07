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

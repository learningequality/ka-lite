Setting up KA Lite testing servers
===


### Testing central server
1. Create file `kalite/local_settings.py`
2. Add the following to local_settings.py:

`DEBUG=True`  
`TEMPLATE_DEBUG=True`  
`CENTRAL_SERVER=True`

3. Run `kalite/manage.py runserver 8001, then exit`
4. Run `kalite/manage.py syncdb --migrate`
5. Run `kalite/manage.py runserver 8001`


### Testing Central Server Registration
0. Follow the steps above for "Testing Central Server" 
1. Enable sending email via http:
    1. Install httplib2 python module from (https://code.google.com/p/httplib2/downloads/list)
    2. Register for an account at (http://postmarkapp.com)
    3. At (http://postmarkapp.com), add a signature email for test email address (that you have control of)
    4. At (http://postmarkapp.com), go to servers->credentials and copy the API key
    5. Add the following line to kalite/local_settings.py

`POSTMARK_API_KEY = "[your api key]"`  

4. Add the following lines to kalite/local_settings.py:

`CENTRAL_SERVER_DOMAIN = "127.0.0.1:8001"`  
`CENTRAL_SERVER_HOST   = "127.0.0.1:8001"`  
`CENTRAL_FROM_EMAIL    = "[your 'signature' email address]"`  
`CENTRAL_ADMIN_EMAIL   = "[your 'signature' email address]"`  
`CENTRAL_CONTACT_EMAIL = "[your 'signature' email address]"`  


### Testing securesync completely locally
1. Set up one repository running KA lite local server (default).  Call this "LOCAL" below.
2. Set up one repository running KA lite "central".  Call this "CENTRAL" below.
    1. Create second repository (git clone...)
    2. Set up "Testing Central Server" (see above)
    3. Set up "Testing Central Server Registration" (see above)
3. On LOCAL, add the following to local_settings.py:

`CENTRAL_SERVER_DOMAIN = "127.0.0.1:8001"`  
`CENTRAL_SERVER_HOST   = "127.0.0.1:8001"`  
`SECURESYNC_PROTOCOL   = "http"`  

4. Browse to LOCAL on url (http://localhost:8008)
5. Browse to CENTRAL on url (http://127.0.0.1:8001)

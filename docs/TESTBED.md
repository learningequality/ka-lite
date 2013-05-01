Setting up KA Lite testing servers
===


### Testing central server
1. create file `kalite/local_settings.py`
2. add `DEBUG=True, TEMPLATE_DEBUG=True, CENTRAL_SERVER=True` to local_settings.py
3. run `kalite/manage.py runserver 8001, then exit`
4. run `kalite/manage.py migrate`
5. run `kalite/manage.py runserver 8001`


### Testing central server registration
1. run `kalite/manage.py schemamigration registration --initialize`
2. run `kalite/manage.py migration registration`
3. enable sending email via http:
  a. install httplib2 python module from (https://code.google.com/p/httplib2/downloads/list)
  b. register for an account at (http://postmarkapp.com)
  c. at (http://postmarkapp.com), add a signature email for test email address (that you have control of)
  d. at (http://postmarkapp.com), go to servers->credentials and copy the API key
  e. add the following line to kalite/local_settings.py
`POSTMARK_API_KEY = "[your api key]"`


### Testing securesync completely locally
1. set up one repository running KA lite local server (default).  Call this "LOCAL" below.
2. set up one repository running KA lite "central".  Call this "CENTRAL" below.
  a. create second repository (git clone...)
  b. set up "testing central server" (see above)
3. on LOCAL, add the following to local_settings.py:
`CENTRAL_SERVER_DOMAIN = "127.0.0.1:8001"
CENTRAL_SERVER_HOST   = "127.0.0.1:8001"
SECURESYNC_PROTOCOL   = "http"`
4. browse to LOCAL on url (http://localhost:8011)
5. browse to CENTRAL on url (http://127.0.0.1:8001)

## Setting up a test central server

As testers, we should virtually never test against our central server, to avoid exposing any unknown bugs that might corrupt data, and to avoid reporting incorrect statistics to partners.

Below are guidelines for what central server to use when, and how to set them up.

### Local (test) central server

### Development central server

```
CENTRAL_SERVER_HOST="kalite.learningequality.org:7007"
SECURESYNC_PROTOCOL="http"
```

Since we're so late in the release cycle, using the development central server is best (`kalite.learningequality.org:7007`).  

Later, after we ship 0.11.1 and begin 0.12, the development central server will point to 0.11.1, so you'll need to install your own local test central server to test.

The reason: the development central server needs to be up, running and essentially bug free, as people who are deploying with alpha version of new features are using it at their central server.  But it will always lead the *actual* central server in terms of when it gets updated with the latest release.

### True central server
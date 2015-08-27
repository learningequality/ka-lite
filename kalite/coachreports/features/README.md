What is this for?
========================
This directory is for BDD integration tests of new features (and maybe one day old features, too).
This is NOT for regression tests, nor for unit tests. Every test here will fire up an instance of
the server and a browser, which is slow and expensive, so don't write tests here when you can get
by without a server and a browser.

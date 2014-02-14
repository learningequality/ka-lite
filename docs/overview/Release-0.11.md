### Release Status ###

_**Target release date**_: Mid-February, 2014 (Central server: January 31, 2014)

_**Status**_: In active development

_**Outstanding issues**_: [found here](https://github.com/learningequality/ka-lite/issues?milestone=8&state=open)

### Goals ###

Augment KA Lite with translations, dubbed videos, and other internationalization of the content.

### High-level Plan ###

* Implement "language packs", with special "language pack" updates
* Implement, a basic command-line tool for downloading dubbed videos.
* Implement the "language-switching toolbar", allowing single users to use a specific translation
* Implement methods for administrators to set device-wide translation.

### Release criteria ###

* Cross-version syncing (push and pull from/to 0.9.2, 0.10.0, 0.10.3, 0.11.1)
* Unit tests (central and distributed server) work in release mode.
* Language pack version changes work and trigger distributed server "update" links
* Language packs work for previous releases (0.10.3)
* Language pack updates reload the server
* Language pack updates invalidate the cache
* Language pack updates regenerate the relevant django javascript file
* [**done**] Language packs are composed of all appropriate parts, across providers
* Test performance with the current topic tree calculations and two language packs installed.
* Functional testing for language packs, language-switching toolbar
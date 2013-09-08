[Khan Academy](http://www.khanacademy.org/)'s core mission is to "provide a free world-class education for anyone anywhere", and as [70% of the world's population is without access to the internet](http://en.wikipedia.org/wiki/Global_Internet_usage), primarily in the developing world, providing an alternative delivery mechanism for Khan Academy content is key to fulfilling this mission.

[KA Lite](http://kalite.learningequality.org/) is a lightweight [Django](https://www.djangoproject.com/) web app for serving core Khan Academy content (videos and exercises) from a local server, with points and progress-tracking, without needing internet connectivity. Primary use cases include:
* Mobile school "vans", which transport a server and multiple laptops/tablets between a number of schools (or orphanages, community centers, etc) in remote communities on a rotating basis, and syncing up with a central database (to download new content and upload analytics) when in an area with internet connectivity.
* For servers/computer labs located in remote schools, which could be slowly syncing with a central server over a cell/satellite network or via USB keys.
* In correctional facilities and other environments where providing educational materials is of value, but users cannot be given general internet access.

To read more about the motivation behind this project, read ["Introducing KA Lite, an offline version of Khan Academy"](http://jamiealexandre.com/blog/2012/12/12/ka-lite-offline-khan-academy/).

To install KA Lite on Linux, OSX, or Windows, view the [installation guide](http://kalitewiki.learningequality.org/installation).

Bug reports should be filed on the [GitHub issue tracker](https://github.com/learningequality/ka-lite/issues).

If you'd like to contribute, please check out the [development wiki](http://kalitewiki.learningequality.org/development/coding/getting-started).

Official website: http://kalite.learningequality.org/

---

The KA Lite sourcecode itself is open-source [MIT licensed](http://opensource.org/licenses/MIT), and the other included software and content is licensed as described in the [LICENSE](https://raw.github.com/learningequality/ka-lite/master/LICENSE) file. Please note that KA Lite is not officially affiliated with, nor maintained by, Khan Academy, but rather makes use of Khan Academy's open API and Creative Commons content, which may only be used for non-commercial purposes.

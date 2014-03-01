[Khan Academy](http://www.khanacademy.org/)'s core mission is to "provide a free world-class education for anyone anywhere", and as [65% of the world's population is without access to the internet](http://en.wikipedia.org/wiki/Global_Internet_usage), primarily in the developing world, providing an alternative delivery mechanism for Khan Academy content is key to fulfilling this mission. ([read more about the project motivation and beginnings](http://jamiealexandre.com/blog/2012/12/12/ka-lite-offline-khan-academy/))

[KA Lite](http://kalite.learningequality.org/) (http://kalite.learningequality.org/) is a lightweight [Django](https://www.djangoproject.com/) web app for serving core Khan Academy content (videos and exercises) from a local server, with points and progress-tracking, without needing internet connectivity. If connectivity is available at any time, however, data will be shared to a central data repository.  

#### Primary use cases include:
* **Servers/computer labs located in remote schools**, which could be completely offline or could be sharing data over a cell/satellite network.
* **Correctional facilities** and other environments where providing educational materials is of value, but users cannot be given general internet access.
* **Mobile school "vans"**, which transport a server and multiple laptops/tablets between a number of schools (or orphanages, community centers, etc) on a rotating basis, sharing data via the central repository (to download new content and upload analytics) when in an area with internet connectivity.

#### Primary ways to interact with the project include:
* **Install KA Lite** on Linux, OSX, or Windows by visiting our [installation guide](http://kalitewiki.learningequality.org/installation).
* **Report bugs** or request new features through the [GitHub issue tracker](https://github.com/learningequality/ka-lite/issues).
* **Contribute to the software development** by visiting our [development wiki](http://kalitewiki.learningequality.org/development/coding/getting-started).

---

The KA Lite source code itself is open-source [MIT licensed](http://opensource.org/licenses/MIT), and the other included software and content is licensed as described in the [LICENSE](https://raw.github.com/learningequality/ka-lite/master/LICENSE) file. Please note that KA Lite is not officially affiliated with, nor maintained by, Khan Academy, but rather makes use of Khan Academy's open API and Creative Commons content, which may only be used for non-commercial purposes.

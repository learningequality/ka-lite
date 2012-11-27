[Khan Academy](http://www.khanacademy.org/)'s core mission is to "provide a free world-class education for anyone anywhere", and as [70% of the world's population is without access to the internet](http://en.wikipedia.org/wiki/Global_Internet_usage), primarily in the developing world, providing an alternative delivery mechanism for Khan Academy content is key to fulfilling this mission.

KA Lite is a lightweight Django web app for serving core Khan Academy content (videos and exercises) from a local server, without needing internet connectivity. Primary use cases include:
* Mobile school "vans", which transport a server and multiple laptops/tablets between a number of schools (or orphanages, community centers, etc) in remote communities on a rotating basis, and syncing up with a central database (to download new content and upload analytics) when in an area with internet connectivity.
* For servers/computer labs located in remote schools, which could be slowly syncing with a central server over a cell/satellite network or via USB keys.
* In correctional facilities and other environments where providing educational materials is of value, but users cannot be given general internet access.

To install KA Lite on Linux or Windows, view the [installation guide](https://github.com/jamalex/ka-lite/blob/master/INSTALL.md).

If you'd like to contribute, please check out the [provisional development guidelines](https://github.com/jamalex/ka-lite/blob/master/docs/DEVELOPMENT.md).
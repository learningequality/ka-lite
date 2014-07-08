### Release Status ###

_**Target release date**_: End of April, 2014

_**Status**_: In active development

_**Outstanding issues**_: [found here](https://github.com/learningequality/ka-lite/issues?labels=&milestone=29&page=1&state=open)

### Goals ###

Prepare this project for community-building

### High-level Plan ###

Required:
* Add docstrings to all functions.
* Document code structure and high-level architecture and designs.  
* Refactor code and clean code structure and architecture.
* Identify, prioritize, and make automated tests a first class citizen in the development workflow.

Also needed:
* Add high-priority admin functions, to expose all admin features to user-base.
* Add central server-side analytic tools for data collection
* Add central server-side tools for deployment management and contact

### Release criteria and status ###

#### Documentation #####
* Team must have decided on the central repository for documentation. 
* All public functions (i.e. functions without a leading underscore) must have docstrings giving a description both for a high level and for each parameter (if any).
* Updated documentation on installation and contribution.
* Automated tests all pass 100%.
* Build server that runs all tests for each commit. (Aron: very essential for release hygiene, and confidence in code).
* Documentation and discussion on the release process.
  - Purpose of each branch (master, develop, release-*)
  - When and where to communicate development status (monthly dev reports, snapshots, betas/alphas, releases)
  - General release timeline template, with a clear demarcation between feature development and bugfixing.
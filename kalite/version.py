# THIS IS USED BY settings.py.  NEVER import settings.py here; hard-codes only!
# this is actually 0.12.2, but we need to update language pack version fallbacks before changing here
VERSION = "0.12.0"
VERSION_INFO = {

    "0.12.2": {
        "release_date": "2014/07/16",
        "git_commit": "ca13eb4",
        "new_features": {
            "all": [],
            "students": [],
            "coaches": [],
            "admins": ["'register' management command for registering from command line"],
        },
        "bugs_fixed": {
            "all": [],
            "students": [],
            "coaches": [],
            "admins": ["deleted models should now be synced properly",
                       "syncing no longer fails for duplicate names for users, groups, and facilities",
                       "added --verbose option to syncmodels command to facilitate debugging and error reporting"],
        },
    },

    "0.12.1": {
        "release_date": "2014/07/01",
        "git_commit": "3aaf4ea",
        "new_features": {
            "all": [],
            "students": [],
            "coaches": [],
            "admins": [],
        },
        "bugs_fixed": {
            "all": [],
            "students": [],
            "coaches": [],
            "admins": ["bugs in data sync fixed"],
        },
    },

    "0.12.0": {
        "release_date": "2014/06/30",
        "git_commit": "4f69360",
        "new_features": {
            "all": [],
            "students": [],
            "coaches": ["transfer students between groups"],
            "admins": ["Delete language", "Delete groups", "Delete students"],
        },
        "bugs_fixed": {
            "all": ["tweaks to the i18n framework"],
            "students": [],
            "coaches": [],
            "admins": [],
        },
    },

    "0.11.2": {
        "release_date": "2014/03/31",
        "git_commit": "abc123abc123abc123abc123",
        "new_features": {
            "all": [],
            "students": [],
            "coaches": [],
            "admins": [],
        },
        "bugs_fixed": {
            "all": [],
            "students": [],
            "coaches": [],
            "admins": [],
        },
    },

    "0.11.1": {
        "release_date": "2014/03/12",
        "git_commit": "a0a3a1e12ba08e0d6bf7f08739df1a8401da4bd3",
        "new_features": {
            "all": [],
            "students": ["translated interface", "dubbed video support"],
            "coaches": [],
            "admins": ["language pack downloads and updates", "dubbed video downloads"],
        },
        "bugs_fixed": {
            "all": [],
            "students": [],
            "coaches": [],
            "admins": [],
        },
    },

    "0.11.0": {
        "release_date": "2013/09/03",
        "git_commit": "29eb96e136d702b5d128b6bbb1b5c347457d080f",
        "new_features": {
            "all": [],
            "students": [],
            "coaches": [],
            "admins": ["automated registration", "download and install via zip"],
        },
        "bugs_fixed": {
            "all": [],
            "students": [],
            "coaches": [],
            "admins": [],
        },
    },

    "0.10.3": {
        "release_date": "2014/01/06",
        "git_commit": "6e56d05e6f53661aea433d72ce7bddacacddc4b8",
        "new_features": {
            "all": [],
            "students": [
                "Better performance (faster save times and login times)",
                "Integration with latest exercises",
            ],
            "coaches": [],
            "admins": [
                "Easier updates for subtitles",
            ],
        },
        "bugs_fixed": {
            "all": [],
            "students": [],
            "coaches": [],
            "admins": [],
        },
    },

    "0.10.2": {
        "release_date": "2013/10/08",
        "git_commit": "5831abb8d2ee0815416a17885790679c4672bf97",
        "new_features": {
            "all": [],
            "students": ["Import your KA progress into KA Lite"],
            "coaches": [],
            "admins": ["Now start KA Lite by double-clicking the start script"],
        },
        "bugs_fixed": {
            "all": [],
            "students": [],
            "coaches": [],
            "admins": [],
        },
    },

    "0.10.1": {
        "release_date": "2013/09/16",
        "git_commit": "f048c11289059f36af0bd1c368f9e0fb354b49b5",
        "new_features": {
            "all": ["we have a new (online) website"],
            "students": [],
            "coaches": [],
            "admins": [],
        },
        "bugs_fixed": {
            "all": ["better performance"],
            "students": [],
            "coaches": [],
            "admins": [],
        },
    },

    "0.10.0": {
        "release_date": "2013/08/26",
        "git_commit": "d375134f2f9f1e0cc3cc1bed73227dcecf1061f3",
        "new_features": {
            "all": [],
            "students": ["summary of progress", "video available indicators"],
            "coaches": ["extended coach reports", "online coach reports"],
            "admins": ["online usage reports", "synchronization reports"],
        },
        "bugs_fixed": {
            "all": [],
            "students": [],
            "coaches": [],
            "admins": [],
        },
    },

    "0.9.2": {
        "release_date": "2013/02/09",
        "git_commit": "7c326329b7ae1b6000d1c636cf8ca920a8cc8daa",
        "new_features": {
            "all": [],
            "students": [],
            "coaches": [],
            "admins": [],
        },
        "bugs_fixed": {
            "all": [],
            "students": [],
            "coaches": [],
            "admins": [],
        },
    },
}

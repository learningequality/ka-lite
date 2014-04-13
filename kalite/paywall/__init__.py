class AccessLevelExceeded(Exception):
    def __init__(self, *args, **kwargs):
        assert 'access_level' in kwargs, "Must specify access_level as a keyword argument."

        self.access_level = kwargs["access_level"]
        del kwargs["access_level"]
        super(AccessLevelExceeded, self).__init__(*args, **kwargs)

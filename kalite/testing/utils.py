class FuzzyInt(int):
    """
    Use to test range of query numbers.

    Example:
        self.assertNumQueries(FuzzyInt(1, 2)):
    """

    def __new__(cls, lowest, highest):
        obj = super(FuzzyInt, cls).__new__(cls, highest)
        obj.lowest = lowest
        obj.highest = highest
        return obj

    def __eq__(self, other):
        return other >= self.lowest and other <= self.highest

    def __repr__(self):
        return "[%d..%d]" % (self.lowest, self.highest)

    def __str__(self):
        return self.__repr__()

    def __unicode__(self):
        return self.__repr__()

    def __format__(self, formatstr):
        return self.__repr__()

    def __add__(self, x):
        val = super(FuzzyInt, self).__add__(x)
        self.lowest += x
        self.highest += x
        return self

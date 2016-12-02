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
        super(FuzzyInt, self).__add__(x)
        self.lowest += x
        self.highest += x
        return self

def switch_to_active_element(browser):
    """
    Compatibility change for Selenium 2.x and 3.x
    """
    # Deprecated as of Selenium 3.x, should change to
    # browser.switch_to.active_element() 
    element = browser.switch_to_active_element()
    # Selenium 3.x
    if isinstance(element, dict):
        element = element['value']
    return element

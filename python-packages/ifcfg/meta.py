"""Ifcfg core meta functionality.  Barrowed from http://slumber.in/."""

class Meta(object):
    """
    Model that acts as a container class for a meta attributes for a larger
    class. It stuffs any kwarg it gets in it's init as an attribute of itself.

    """

    def __init__(self, **kw):
        self._merge(kw)

    def _merge(self, dict_obj):
        for key, value in dict_obj.items():
            setattr(self, key, value)
            
class MetaMixin(object):
    """
    Mixin that provides the Meta class support to add settings to instances
    of slumber objects. Meta settings cannot start with a _.

    """

    def __init__(self, *args, **kw):
        # Get a List of all the Classes we in our MRO, find any attribute named
        #     Meta on them, and then merge them together in order of MRO
        metas = reversed([x.Meta for x in self.__class__.mro() \
                                  if hasattr(x, "Meta")])
        final_meta = {}

        # Merge the Meta classes into one dict
        for meta in metas:
            final_meta.update(dict([x for x in list(meta.__dict__.items()) \
                                       if not x[0].startswith("_")]))

        # Update the final Meta with any kw passed in
        for key in list(final_meta.keys()):
            if key in kw:
                final_meta[key] = kw.pop(key)

        self._meta = Meta(**final_meta)

        # FIX ME: object.__init__() doesn't take params without exception
        super(MetaMixin, self).__init__()
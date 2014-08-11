from . import models


def dynamic_settings(viewfn):

    def new_view_fn(request, *args, **kwargs):
        ds = models.DynamicSettings()
        viewfn(request, ds, *args, **kwargs)

    return new_view_fn

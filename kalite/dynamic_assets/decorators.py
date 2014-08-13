from .decorators import load_dynamic_settings


def dynamic_settings(viewfn):

    def new_view_fn(request, *args, **kwargs):
        ds = load_dynamic_settings()
        viewfn(request, ds, *args, **kwargs)

    return new_view_fn

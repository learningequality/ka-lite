from .utils import load_dynamic_settings


def dynamic_settings(viewfn, **otherinfo):

    def new_view_fn(request, *args, **kwargs):
        ds = load_dynamic_settings(request=request, **otherinfo)
        return viewfn(request, ds, *args, **kwargs)

    return new_view_fn

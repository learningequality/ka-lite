from annoying.decorators import render_to

from kalite.dynamic_assets.decorators import dynamic_settings


@dynamic_settings
@render_to('dynamic_assets/dynamic.css', mimetype='text/css')
def dynamic_css(request, ds):
    return {
        'ds': ds,
    }


@dynamic_settings
@render_to('dynamic_assets/dynamic.js', mimetype='text/javascript')
def dynamic_js(request, ds):
    return {
        'ds': ds,
    }

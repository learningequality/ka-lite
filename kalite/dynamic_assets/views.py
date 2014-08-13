from annoying.decorators import render_to

from kalite.dynamic_assets.decorators import dynamic_settings


@dynamic_settings
@render_to('dynamic_assets/dynamic.css', mimetype='text/css')
def dynamic_css(request, ds):
    return {
        'turn_off_motivational_features': ds.distributed.turn_off_motivational_features
    }


@dynamic_settings
@render_to('dynamic_assets/dynamic.js', mimetype='text/javascript')
def dynamic_js(request, ds):
    return {
        'fixed_block_exercises': ds.distributed.fixed_block_exercises
    }

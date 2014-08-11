from annoying.decorators import render_to

from django.conf import settings

# TODO (jamie): merge dynamic_css into dynamic_js
@render_to('dynamic_assets/dynamic.css', mimetype='text/css')
def dynamic_css(request):
    return {
        'turn_off_motivational_features': settings.TURN_OFF_MOTIVATIONAL_FEATURES,
    }

@render_to('dynamic_assets/dynamic.js', mimetype='text/javascript')
def dynamic_js(request):
    return {
        'fixed_block_exercises': settings.FIXED_BLOCK_EXERCISES,
    }

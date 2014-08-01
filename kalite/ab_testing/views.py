from annoying.decorators import render_to

from django.conf import settings


@render_to('ab_testing/css/ab_testing.css', mimetype='text/css')
def ab_testing_css(request):
    return {
        'turn_off_motivational_features': settings.TURN_OFF_MOTIVATIONAL_FEATURES,
    }


@render_to('ab_testing/js/ab_testing.js', mimetype='text/javascript')
def ab_testing_js(request):
    return {
        'fixed_block_exercises': settings.FIXED_BLOCK_EXERCISES,
        'quiz_repeats': settings.QUIZ_REPEATS,
    }

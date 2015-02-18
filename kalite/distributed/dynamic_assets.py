from django.conf import settings

from kalite.dynamic_assets import DynamicSettingsBase, fields

class DynamicSettings(DynamicSettingsBase):
    fixed_block_exercises = fields.IntegerField(default=getattr(settings, "FIXED_BLOCK_EXERCISES", 0), minimum=0, maximum=10)
    quiz_repeats = fields.IntegerField(default=getattr(settings, "QUIZ_REPEATS", 0), minimum=1, maximum=10)
    turn_off_motivational_features = fields.BooleanField(default=getattr(settings, "TURN_OFF_MOTIVATIONAL_FEATURES", False))
    turn_off_points_for_noncurrent_unit = fields.BooleanField(default=False)
    turn_off_points_for_videos = fields.BooleanField(default=False)
    turn_off_points_for_exercises = fields.BooleanField(default=False)
    front_page_welcome_message = fields.CharField(default="")
    streak_correct_needed = fields.IntegerField(default=getattr(settings, "STREAK_CORRECT_NEEDED", 8), minimum=5, maximum=10)
    points_per_video = fields.IntegerField(default=getattr(settings, "POINTS_PER_VIDEO", 750), minimum=0, maximum=5000)

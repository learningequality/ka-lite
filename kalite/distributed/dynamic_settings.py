from django.conf import settings

from kalite.dynamic_assets import models

models.DynamicSettings(namespace='distributed',
                       schema={
                           'turn_off_motivational_features': models.BoolField(),
                           'fixed_block_exercises': models.IntField(),
                       },
                       source={
                           'turn_off_motivational_features': settings.TURN_OFF_MOTIVATIONAL_FEATURES,
                           'fixed_block_exercises': settings.FIXED_BLOCK_EXERCISES,
                       }
)

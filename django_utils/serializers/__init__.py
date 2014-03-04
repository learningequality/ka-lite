from django.core.serializers import *
BUILTIN_SERIALIZERS["versioned-json"]   = "utils.django_utils.serializers.versioned_json"
BUILTIN_SERIALIZERS["versioned-python"] = "utils.django_utils.serializers.versioned_python"


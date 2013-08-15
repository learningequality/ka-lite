from django.core.serializers import *
BUILTIN_SERIALIZERS["versioned-json"]   = "shared.serializers.versioned_json"
BUILTIN_SERIALIZERS["versioned-python"] = "shared.serializers.versioned_python"


import json
import re 
import os

from kalite.settings import DATA_PATH


def get_language_name(lang_code, native=False):
    """Return full English or native language name from ISO 639-1 language code; raise exception if it isn't hardcoded yet"""
    # Open lookup dictionary 
    lang_lookup_filename = "languagelookup.json"
    lang_lookup_path = os.path.join(DATA_PATH, lang_lookup_filename)
    LANGUAGE_LOOKUP = json.loads(open(lang_lookup_path).read())

    # Convert code if neccessary 
    lang_code = convert_language_code_format(lang_code)

    language_entry = LANGUAGE_LOOKUP.get(lang_code)    
    if not language_entry:
       raise Exception("We don't have language code '%s' saved in our lookup dictionary (location: %s). Please manually add it before re-running this command." % (lang_code, lang_lookup_path))

    if not native:
        language_name = language_entry["name"]
    else:
        language_name = language_entry["native_name"]

    return language_name


def convert_language_code_format(lang_code, for_crowdin=False):
    """
    Return language code for lookup in local dictionary. 

    Note: For language codes with localizations, Django requires the format xx_XX (e.g. Spanish from Spain = es_ES)  
    not: xx-xx, xx-XX, xx_xx.
    """
    lang_code = lang_code.lower()
    code_parts = re.split('-|_', lang_code)    
    if len(code_parts) >  1:
        assert len(code_parts) == 2
        code_parts[1] = code_parts[1].upper()
        if not for_crowdin:
            lang_code = "_".join(code_parts)
        else:
            lang_code = "-".join(code_parts)

    return lang_code

import hashlib
import os

from django.conf import settings
from django.template import Library

from fle_utils.config.models import Settings

if 'django.contrib.staticfiles' in settings.INSTALLED_APPS:
    from django.contrib.staticfiles.templatetags.staticfiles import static as static_lib
else:
    from django.templatetags.static import static as static_lib

from kalite import version

CACHE_VARS = ['BUILD_HASH_CACHE']

# Add this as key to `fle_utils.config.models.Settings`
BUILD_HASH = 'BUILD_HASH'
BUILD_HASH_CACHE = None

register = Library()


@register.simple_tag
def static_with_build(path, with_build=True):
    """
    We need a way for the client browser to load the newly updated static
        files because some browsers cache the static files and does not
        load them up automatically when we release new versions but with
        the same name.

    REF: https://github.com/learningequality/ka-lite/issues/1161

    One way is to add a Get paramater to the static file's path so it becomes
        unique and the browser invalidates it's cached version.

    We re-use django's `{% static <path> %}` template tag to add build version
        to the filenames of static files.

    REF: https://www.quora.com/What-are-the-best-practices-for-versioning-CSS-and-JS-files

    Option 1: Use the `fle_utils.config.models.Settings`
        Pros: It works and more flexible.
        Cons: Requires us to update the BUILD_ID key at admin page.

    Option 2: Use the BUILD as Get parameter.
        Pros: It works.
        Cons: We need to maintain the `kalite/version.py` hard-coded values
            every time we make a release.

    Option 3: Use the SHA hash of the file's bytes as querystring.
        Pros: It works and more reliable.
        Cons: Requires us to open the static files to generate the hash.
                TODO(cpauya): Benchmark this!
                TODO(cpauya): Inefficient!  This is called everytime the static file is used.

    We try all options which does not throw exception.
    """
    global BUILD_HASH_CACHE

    new_path = static_lib(path)
    if with_build:
        build_id = ''

        # try fle_utils`s Settings
        try:
            if BUILD_HASH_CACHE:
                build_id = BUILD_HASH_CACHE
            else:
                build_id = BUILD_HASH_CACHE = Settings.get(BUILD_HASH, '')
        except Exception:
            pass

        # try the BUILD data from `version.py`
        if not build_id:
            try:
                build_id = BUILD_HASH_CACHE = version.VERSION_INFO[version.VERSION]["git_commit"][0:8]
            except:
                pass

        # attempt to use hash
        if not build_id:
            try:
                # REF: http://stackoverflow.com/questions/16874598/how-do-i-calculate-the-md5-checksum-of-a-file-in-python
                file_path = os.path.realpath(os.path.join(settings.STATIC_ROOT, path))
                with open(file_path, 'rb') as file_to_check:
                    # REF: http://stackoverflow.com/questions/1131220/get-md5-hash-of-big-files-in-python
                    filehash = hashlib.sha256()
                    while True:
                        data = file_to_check.read(8192)
                        if not data:
                            break
                        filehash.update(data)
                    build_id = filehash.hexdigest()
            except Exception:
                pass

        if build_id:
            new_path = '%s?%s' % (new_path, build_id,)
    return new_path


@register.simple_tag
def static(path, without_build=False):
    """
    We use the same name as the `staticfiles` app so we don't have to modify
        the templates that are already using it.

    If we need to include the build/hash as a Get paramater, we provide the
        `with_build` argument.
    """
    return static_with_build(path, not without_build)

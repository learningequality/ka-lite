import os
import re

from django.core.management.base import NoArgsCommand

from kalite.settings import USER_DATA_ROOT
from os import walk

class Command(NoArgsCommand):
    """
    Pre-process html files in sphinx-docs.
    At the moment, this just means making static file references (css, js) use an absolute href.
    """

    def handle_noargs(*args, **kwargs):
        expr = re.compile(r'(href|src)="(\.\./)*(_static|_images)/')
        repl = r'\1="/static/\3/'
        docs_path = os.path.join(USER_DATA_ROOT, "sphinx-docs", "_build", "html")
        for dirpath, dirnames, filenames in walk(docs_path):
            for filename in filenames:
                if ".html" in filename:
                    with open(os.path.join(dirpath, filename), "r+") as f:
                        preprocess = f.read()
                        postprocess = expr.sub(repl, preprocess)
                        f.seek(0)
                        f.write(postprocess)

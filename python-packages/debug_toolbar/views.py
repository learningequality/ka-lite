"""
Helper views for the debug toolbar. These are dynamically installed when the
debug toolbar is displayed, and typically can do Bad Things, so hooking up these
views in any other way is generally not advised.
"""

import os
import django.views.static
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.utils.hashcompat import sha_constructor

from debug_toolbar.utils.compat.db import connections


class InvalidSQLError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def debug_media(request, path):
    root = getattr(settings, 'DEBUG_TOOLBAR_MEDIA_ROOT', None)
    if root is None:
        parent = os.path.abspath(os.path.dirname(__file__))
        root = os.path.join(parent, 'media', 'debug_toolbar')
    return django.views.static.serve(request, path, root)


def sql_select(request):
    """
    Returns the output of the SQL SELECT statement.

    Expected GET variables:
        sql: urlencoded sql with positional arguments
        params: JSON encoded parameter values
        duration: time for SQL to execute passed in from toolbar just for redisplay
        hash: the hash of (secret + sql + params) for tamper checking
    """
    from debug_toolbar.panels.sql import reformat_sql
    sql = request.GET.get('sql', '')
    params = request.GET.get('params', '')
    alias = request.GET.get('alias', 'default')
    hash = sha_constructor(settings.SECRET_KEY + sql + params).hexdigest()
    if hash != request.GET.get('hash', ''):
        return HttpResponseBadRequest('Tamper alert')  # SQL Tampering alert
    if sql.lower().strip().startswith('select'):
        params = simplejson.loads(params)
        cursor = connections[alias].cursor()
        cursor.execute(sql, params)
        headers = [d[0] for d in cursor.description]
        result = cursor.fetchall()
        cursor.close()
        context = {
            'result': result,
            'sql': reformat_sql(cursor.db.ops.last_executed_query(cursor, sql, params)),
            'duration': request.GET.get('duration', 0.0),
            'headers': headers,
            'alias': alias,
        }
        return render_to_response('debug_toolbar/panels/sql_select.html', context)
    raise InvalidSQLError("Only 'select' queries are allowed.")


def sql_explain(request):
    """
    Returns the output of the SQL EXPLAIN on the given query.

    Expected GET variables:
        sql: urlencoded sql with positional arguments
        params: JSON encoded parameter values
        duration: time for SQL to execute passed in from toolbar just for redisplay
        hash: the hash of (secret + sql + params) for tamper checking
    """
    from debug_toolbar.panels.sql import reformat_sql
    sql = request.GET.get('sql', '')
    params = request.GET.get('params', '')
    alias = request.GET.get('alias', 'default')
    hash = sha_constructor(settings.SECRET_KEY + sql + params).hexdigest()
    if hash != request.GET.get('hash', ''):
        return HttpResponseBadRequest('Tamper alert')  # SQL Tampering alert
    if sql.lower().strip().startswith('select'):
        params = simplejson.loads(params)
        cursor = connections[alias].cursor()

        conn = connections[alias].connection
        engine = conn.__class__.__module__.split('.', 1)[0]

        if engine == "sqlite3":
            # SQLite's EXPLAIN dumps the low-level opcodes generated for a query;
            # EXPLAIN QUERY PLAN dumps a more human-readable summary
            # See http://www.sqlite.org/lang_explain.html for details
            cursor.execute("EXPLAIN QUERY PLAN %s" % (sql,), params)
        else:
            cursor.execute("EXPLAIN %s" % (sql,), params)

        headers = [d[0] for d in cursor.description]
        result = cursor.fetchall()
        cursor.close()
        context = {
            'result': result,
            'sql': reformat_sql(cursor.db.ops.last_executed_query(cursor, sql, params)),
            'duration': request.GET.get('duration', 0.0),
            'headers': headers,
            'alias': alias,
        }
        return render_to_response('debug_toolbar/panels/sql_explain.html', context)
    raise InvalidSQLError("Only 'select' queries are allowed.")


def sql_profile(request):
    """
    Returns the output of running the SQL and getting the profiling statistics.

    Expected GET variables:
        sql: urlencoded sql with positional arguments
        params: JSON encoded parameter values
        duration: time for SQL to execute passed in from toolbar just for redisplay
        hash: the hash of (secret + sql + params) for tamper checking
    """
    from debug_toolbar.panels.sql import reformat_sql
    sql = request.GET.get('sql', '')
    params = request.GET.get('params', '')
    alias = request.GET.get('alias', 'default')
    hash = sha_constructor(settings.SECRET_KEY + sql + params).hexdigest()
    if hash != request.GET.get('hash', ''):
        return HttpResponseBadRequest('Tamper alert')  # SQL Tampering alert
    if sql.lower().strip().startswith('select'):
        params = simplejson.loads(params)
        cursor = connections[alias].cursor()
        result = None
        headers = None
        result_error = None
        try:
            cursor.execute("SET PROFILING=1")  # Enable profiling
            cursor.execute(sql, params)  # Execute SELECT
            cursor.execute("SET PROFILING=0")  # Disable profiling
            # The Query ID should always be 1 here but I'll subselect to get the last one just in case...
            cursor.execute("SELECT * FROM information_schema.profiling WHERE query_id=(SELECT query_id FROM information_schema.profiling ORDER BY query_id DESC LIMIT 1)")
            headers = [d[0] for d in cursor.description]
            result = cursor.fetchall()
        except:
            result_error = "Profiling is either not available or not supported by your database."
        cursor.close()
        context = {
            'result': result,
            'result_error': result_error,
            'sql': reformat_sql(cursor.db.ops.last_executed_query(cursor, sql, params)),
            'duration': request.GET.get('duration', 0.0),
            'headers': headers,
            'alias': alias,
        }
        return render_to_response('debug_toolbar/panels/sql_profile.html', context)
    raise InvalidSQLError("Only 'select' queries are allowed.")


def template_source(request):
    """
    Return the source of a template, syntax-highlighted by Pygments if
    it's available.
    """
    from django.template import TemplateDoesNotExist
    from django.utils.safestring import mark_safe
    from django.conf import settings

    template_name = request.GET.get('template', None)
    if template_name is None:
        return HttpResponseBadRequest('"template" key is required')

    try:  # Django 1.2 ...
        from django.template.loader import find_template_loader, make_origin
        loaders = []
        for loader_name in settings.TEMPLATE_LOADERS:
            loader = find_template_loader(loader_name)
            if loader is not None:
                loaders.append(loader)
        for loader in loaders:
            try:
                source, display_name = loader.load_template_source(template_name)
                origin = make_origin(display_name, loader, template_name, settings.TEMPLATE_DIRS)
                break
            except TemplateDoesNotExist:
                source = "Template Does Not Exist: %s" % (template_name,)
    except (ImportError, AttributeError):  # Django 1.1 ...
        from django.template.loader import find_template_source
        source, origin = find_template_source(template_name)

    try:
        from pygments import highlight
        from pygments.lexers import HtmlDjangoLexer
        from pygments.formatters import HtmlFormatter

        source = highlight(source, HtmlDjangoLexer(), HtmlFormatter())
        source = mark_safe(source)
        source.pygmentized = True
    except ImportError:
        pass

    return render_to_response('debug_toolbar/panels/template_source.html', {
        'source': source,
        'template_name': template_name
    })

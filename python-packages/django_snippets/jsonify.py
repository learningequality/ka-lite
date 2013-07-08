from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.utils import simplejson
from django.template import Library

register = Library()

def jsonify(object):
    if isinstance(object, QuerySet):
        return serialize('json', object)
    return simplejson.dumps(object)

register.filter('jsonify', jsonify)

{% load my_filters %}
var ds = {{ ds.to_json|jsonify }};

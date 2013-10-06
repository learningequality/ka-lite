$(document).ready(function() {
    var results = [];
    $.getJSON("/api/flat_topic_tree", function(categories) {
	for (var category_name in categories) { // category is either Video, Exercise or Topic
	    var category = categories[category_name];
	    for (var node_name in category) {
		node = category[node_name];
		results.push(node.title);
	    }
	}
    });
    $("#search").autocomplete({source: results});
});

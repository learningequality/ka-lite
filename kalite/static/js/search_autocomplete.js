var results = null;
var timeout_length = 1000 * 20; // 20 seconds

function isLocalStorageAvailable() {
    var testString = gettext("hello peeps");  // ;) fun for translators
    try {
        localStorage[testString] = testString;
        return true;
    } catch(e) {
        return false;
    }
}

function fetchTopicTree() {
    $.ajax({
        url: "/api/flat_topic_tree",
        cache: true,
        dataType: "json",
        timeout: timeout_length,
        success: function(categories) {
            results = [];
            for (var category_name in categories) { // category is either Video, Exercise or Topic
                var category = categories[category_name];
                for (var node_name in category) {
                    node = category[node_name];
                    results.push(node.title);
                }
            }
            if (isLocalStorageAvailable()) {
                localStorage.setItem("flat_topic_tree", JSON.stringify(results)); // we can only store strings in localStorage
            }
        }
    });
}

$(document).ready(function() {

    $("#search").focus(function() {
        if (isLocalStorageAvailable()) {
            results = JSON.parse(localStorage.getItem("flat_topic_tree")); // coerce string back to JSON
        }

        if (results === null) {
	    fetchTopicTree();
        }
    });

    $("#search").autocomplete({
        minLength: 3,
        source: function(request, response) {
            var results_filtered = $.ui.autocomplete.filter(results, request.term); // do some filtering here already
            response(results_filtered.slice(0, 15));
        }
    });
});

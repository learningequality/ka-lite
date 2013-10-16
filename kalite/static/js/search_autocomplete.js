$(document).ready(function() {
    var results = [];
    
    $.ajax({ 
        url: "/api/flat_topic_tree", 
        cache: true,
        dataType: "json",
        success: function(categories) {
            for (var category_name in categories) { // category is either Video, Exercise or Topic
                var category = categories[category_name];
                for (var node_name in category) {
                    node = category[node_name];
                    results.push(node.title);
                }
            }
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

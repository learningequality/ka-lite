var nodes = null;   // store info about each topic tree node (persists to local storage)
var titles = [];    // keep an array (local memory only) around for fast filtering
var timeout_length = 1000 * 20; // 20 seconds

function isLocalStorageAvailable(item_index) {
    // Pass in no arg: test whether localStorage exists.
    // Pass in an arg: test if that item is in localStorage 
    //    (returns false if item doesn't exist, or if localStorage is not available)
    try {
        return (item_index in localStorage || (!item_index && localStorage));
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
            nodes = {};
            for (var category_name in categories) { // category is either Video, Exercise or Topic
                var category = categories[category_name];
                for (var node_name in category) {
                    node = category[node_name];
                    title = node.title;

                    if (title in nodes) {
                        continue;  // avoid duplicates
                    }

                    nodes[node.title] = {
                        title: node.title,
                        type: category_name.toLowerCase(),
                        path: node.path
                    };
                    titles.push(node.title);
                }
            }
            if (isLocalStorageAvailable()) {
                // we can only store strings in localStorage
                localStorage.setItem("flat_topic_tree_v2", JSON.stringify(nodes));
            }
        }
    });
}

$(document).ready(function() {

    $("#search").focus(function() {
        if (nodes !== null) {
            // No need to reload
            return;
        } else if (isLocalStorageAvailable("flat_topic_tree_v2")) {
            // Get from local storage
            //console.log("LocalStore cache hit.")
            nodes = JSON.parse(localStorage.getItem("flat_topic_tree_v2")); // coerce string back to JSON
            for (title in nodes) {
                titles.push(title);
            }
        } else {
            // Get from distributed server
            //console.log("LocalStore cache miss.")
            fetchTopicTree();
        }
    });

    $("#search").autocomplete({
        minLength: 3,
        html: true,  // extension allows html-based labels
        source: function(request, response) {
            clear_message("id_search_error");

            // Executed when we're requested to give a list of results
            var titles_filtered = $.ui.autocomplete.filter(titles, request.term).slice(0, 15);

            // From the filtered titles, produce labels (html) and values (for doing stuff)
            var results = [];
            for (idx in titles_filtered) {
                var node = nodes[titles_filtered[idx]];
                var label = "<li class='autocomplete " + node.type + "'>" + node.title + "</li>";
                results.push({
                    label: label,
                    value: node.title
                });
            }
            response(results);
        },
        select: function( event, ui ) {
            // When they click a specific item, just go there (if we recognize it)
            var title = ui.item.value;
            if (nodes && title in nodes && nodes[title]) {
                window.location.href = nodes[title].path;
            } else {
                show_message("error", "Unexpected error: no search data found for selected item.  Please select another item.", "id_search_error");
            }
        }

    });
    
    
});

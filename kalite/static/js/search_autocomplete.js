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
                    if (!(category_name in nodes)) {
                        // Store nodes by category
                        nodes[category_name] = {};
                    }
                    nodes[category_name][node.title] = {
                        title: node.title,
                        type: category_name.toLowerCase(),
                        path: node.path,
                        available: node.available,
                    };
                }
            }
            if (isLocalStorageAvailable()) {
                // we can only store strings in localStorage
                var node_types = [];
                for (node_type in nodes) {
                    node_types = node_types.concat(node_type);
                    var item_name = "nodes_" + node_type + "_v1";
                    localStorage.setItem(item_name, JSON.stringify(nodes[node_type]));
                }
                localStorage.setItem("node_types", JSON.stringify(node_types));
            }

            // But for now, for search purposes, flatten
            flattenNodes();
        }
    });
}

function flattenNodes() {
    // now take that structured object, and reduce.
    var flattened_nodes = {};
    for (node_type in nodes) {
        $.extend(flattened_nodes, nodes[node_type]);
    }
    nodes = flattened_nodes;
    for (title in nodes) {
        titles.push(title);
    }
}

$(document).ready(function() {

    $("#search").focus(function() {
        if (nodes !== null) {
            // No need to reload
            return;

        } else if (isLocalStorageAvailable("node_types")) {
            //console.log("LocalStore cache hit.")
            // Get from local storage, grouped by type
            var node_types = JSON.parse(localStorage.getItem("node_types"));
            nodes = {};
            for (idx in node_types) {
                var node_type = node_types[idx];
                var item_name = "nodes_" + node_type + "_v1";
                nodes[node_type] = JSON.parse(localStorage.getItem(item_name)); // coerce string back to JSON
            }

            // After getting by type, flatten
            flattenNodes();

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

            // sort the titles again, since ordering was lost when we did autocomplete.filter
            var node_type_ordering = ["video", "exercise", "topic"] // custom ordering, with the last in the array appearing first
            titles_filtered.sort(function(title1, title2) {
                var node1 = nodes[title1];
                var node2 = nodes[title2];
                // we use the ordering of types found in node_types
                var compvalue = node_type_ordering.indexOf(node2.type) - node_type_ordering.indexOf(node1.type);
                return compvalue;
            });

            // From the filtered titles, produce labels (html) and values (for doing stuff)
            var results = [];
            var is_admin = window.userModel.get("is_admin");
            for (idx in titles_filtered) {
                var node = nodes[titles_filtered[idx]];

                // exclude videos that aren't available
                if (!is_admin && node.type == "video" && !node.available) {
                    continue;
                }

                var label = "<li class='autocomplete " + node.type + " " + (node.available ? "" : "un") + "available'>" + gettext(node.title) + "</li>";
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
                show_message("error", gettext("Unexpected error: no search data found for selected item. Please select another item."), "id_search_error");
            }
        }

    });

    $("#search-button").click(function() {
        $("#search-box").submit();
    });

});

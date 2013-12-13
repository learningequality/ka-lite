var _nodes = null;   // store info about each topic tree node (persists to local storage)
var _titles = [];    // keep an array (local memory only) around for fast filtering
var _timeout_length = 1000 * 20; // 20 seconds
var _version = "3"; // increment this when you're invalidating old storage

function prefixed_key(base_key) {
    return "kalite_search_" + base_key;
}

function ls_key(node_type, lang) {
    // make them collide by language
    return prefixed_key("nodes_" + node_type + "_" + "_v" + _version);
}

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

function fetchTopicTree(lang) {
    $.ajax({
        url: "/api/flat_topic_tree/" + lang,
        cache: true,
        dataType: "json",
        timeout: _timeout_length,
        error: function(resp) {
            handleFailedAPI(resp, gettext("Error getting search data"));
        },
        success: function(categories) {
            //console.log("got the remote topic tree for  " + lang);

            _nodes = {};
            for (var category_name in categories) { // category is either Video, Exercise or Topic
                var category = categories[category_name];
                for (var node_name in category) {
                    node = category[node_name];
                    title = node.title;

                    if (title in _nodes) {
                        continue;  // avoid duplicates
                    }
                    if (!(category_name in _nodes)) {
                        // Store nodes by category
                        _nodes[category_name] = {};
                    }
                    _nodes[category_name][node.title] = {
                        title: node.title,
                        type: category_name.toLowerCase(),
                        path: node.path,
                        available: node.available,
                    };
                }
            }
            if (isLocalStorageAvailable()) {
                //console.log("Caching to local store");
                // we can only store strings in localStorage
                localStorage.setItem(prefixed_key("language"), lang);
                var node_types = [];
                for (node_type in _nodes) {
                    node_types = node_types.concat(node_type);
                    //console.log("Saving " + ls_key(node_type, lang));
                    localStorage.setItem(ls_key(node_type, lang), JSON.stringify(_nodes[node_type]));
                }
                localStorage.setItem(prefixed_key("node_types"), JSON.stringify(node_types));
            }

            // But for now, for search purposes, flatten
            flattenNodes();
        }
    });
}

function flattenNodes() {
    // now take that structured object, and reduce.
    var flattened_nodes = {};
    for (node_type in _nodes) {
        $.extend(flattened_nodes, _nodes[node_type]);
    }
    _nodes = flattened_nodes;
    for (title in _nodes) {
        _titles.push(title);
    }
}

function fetchLocalOrRemote() {
    lang = window.userModel.get("current_language");

    if (_nodes !== null) {
        // No need to reload
        return;

    } else if (isLocalStorageAvailable(prefixed_key("language")) && localStorage.getItem(prefixed_key("language")) == lang) {
        //console.log("LocalStore cache hit.")
        // Get from local storage, grouped by type
        var node_types = JSON.parse(localStorage.getItem("node_types"));
        _nodes = {};
        for (idx in node_types) {
            var node_type = node_types[idx];
            var item_name = ls_key(node_type, lang);
            _nodes[node_type] = JSON.parse(localStorage.getItem(item_name)); // coerce string back to JSON
        }

        // After getting by type, flatten
        flattenNodes();

    } else {
        //console.log(ls_key("Topic", lang));
        //console.log("Need to fetch..." + lang);
        $("#search").focus(null);  // disable re-fetching
        // Get from distributed server
        fetchTopicTree(lang);
    }
}


$(document).ready(function() {

    $("#search").focus(fetchLocalOrRemote);

    $("#search").autocomplete({
        minLength: 3,
        html: true,  // extension allows html-based labels
        source: function(request, response) {
            clear_message("id_search_error");

            // Executed when we're requested to give a list of results
            var titles_filtered = $.ui.autocomplete.filter(_titles, request.term).slice(0, 15);

            // sort the titles again, since ordering was lost when we did autocomplete.filter
            var node_type_ordering = ["video", "exercise", "topic"] // custom ordering, with the last in the array appearing first
            titles_filtered.sort(function(title1, title2) {
                var node1 = _nodes[title1];
                var node2 = _nodes[title2];
                // we use the ordering of types found in node_types
                var compvalue = node_type_ordering.indexOf(node2.type) - node_type_ordering.indexOf(node1.type);
                return compvalue;
            });

            // From the filtered titles, produce labels (html) and values (for doing stuff)
            var results = [];
            var is_admin = window.userModel.get("is_admin");
            for (idx in titles_filtered) {
                var node = _nodes[titles_filtered[idx]];

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
            if (_nodes && title in _nodes && _nodes[title]) {
                window.location.href = _nodes[title].path;
            } else {
                show_message("error", gettext("Unexpected error: no search data found for selected item. Please select another item."), "id_search_error");
            }
        }

    });

    $("#search-button").click(function() {
        $("#search-box").submit();
    });

});

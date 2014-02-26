var _nodes = null;   // store info about each topic tree node (persists to local storage)
var _titles = [];    // keep an array (local memory only) around for fast filtering
var _timeout_length = 1000 * 20; // 20 seconds
var _version = "7"; // increment this when you're invalidating old storage

function prefixed_key(base_key) {
    // Cross-app key (prefix with an app-specific prefix
    return "kalite_search_" + base_key;
}

function ls_key(node_type, lang) {
    // make them collide by language
    return prefixed_key("nodes_" + node_type + "_" + "_v" + _version);
}

function fetchTopicTree(lang, force_reparse) {
    var abc = $.ajax({
        url: SEARCH_TOPICS_URL,  // already has language information embedded in it
        cache: true,
        dataType: "json",
        timeout: _timeout_length,
        ifModified:true,
        error: function(resp) {
            handleFailedAPI(resp, gettext("Error getting search data"));
        },
        success: function(categories, textStatus, xhr) {
            if (xhr.status == 304  && force_reparse !== true) {
                console.log(sprintf("got the remote topic tree for %s and it is the same as before; not re-parsing.", lang));
            } else {
                console.log(sprintf("got the remote topic tree for %s and it changed; re-parsing.", lang));

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

                // But for now, for search purposes, flatten
                flattenNodes();
            }
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
    $("#search").focus(null);  // disable re-fetching
    fetchTopicTree(CURRENT_LANGUAGE, _nodes == null); // only parse the json if _nodes == null (or if something changed)
}


$(document).ready(function() {

    $("#search").focus(fetchLocalOrRemote);

    $("#search").autocomplete({
        minLength: 3,
        html: true,  // extension allows html-based labels
        source: function(request, response) {
            clear_message("id_search_error");

            // Executed when we're requested to give a list of results
            var titles_filtered = $.ui.autocomplete.filter(_titles, request.term);

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
            response(results.slice(0, 15)); // slice after filtering, see #1563
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

var _nodes = null;   // store info about each topic tree node (persists to local storage)
var _titles = {};    // keep an array (local memory only) around for fast filtering
var _keywords = {}; // keep a map of keywords to node titles for filtering on keywords
var _timeout_length = 1000 * 20; // 20 seconds
var _version = "7"; // increment this when you're invalidating old storage

function fetchTopicTree(lang, force_reparse) {
    doRequest(SEARCH_TOPICS_URL, null, {  // already has language information embedded in it
        cache: true,
        dataType: "json",
        timeout: _timeout_length,
        ifModified: true
    }).success(function(categories, textStatus, xhr) {
        if (xhr.status == 304  && force_reparse !== true) {
            console.log(sprintf("got the remote topic tree for %s and it is the same as before; not re-parsing.", lang));
        } else {
            console.log(sprintf("got the remote topic tree for %s and it wasn't cached; re-parsing.", lang));

            _nodes = categories;

            // But for now, for search purposes, flatten
            flattenNodes();
        }
    });
}

function flattenNodes() {
    // now take that structured object, and reduce.
    var flattened_nodes = {};
    for (var node_type in _nodes) {
        $.extend(flattened_nodes, _nodes[node_type]);
    }
    _nodes = flattened_nodes;
    for (var id in _nodes) {
        if(!_.has(_titles, _nodes[id]["title"])){
            _titles[_nodes[id]["title"]] = id;
            if (_nodes[id]["keywords"]!==undefined){
                for (var i = 0; i < _nodes[id]["keywords"].length; i++){
                    if (_keywords[_nodes[id]["keywords"][i]]===undefined){
                        _keywords[_nodes[id]["keywords"][i]] = [];
                    }
                    if($.inArray(id, _keywords[_nodes[id]["keywords"][i]]) == -1) {
                        _keywords[_nodes[id]["keywords"][i]].push(id);
                    }
                }
            }
        }
    }
}

function fetchLocalOrRemote() {
    $("#search").focus(null);  // disable re-fetching
    fetchTopicTree(CURRENT_LANGUAGE, _nodes === null); // only parse the json if _nodes == null (or if something changed)
}


$(document).ready(function() {

    $("#search").focus(fetchLocalOrRemote);

    $("#search").autocomplete({
        autoFocus: true,
        minLength: 3,
        html: true,  // extension allows html-based labels
        source: function(request, response) {
            clear_messages();

            // Executed when we're requested to give a list of results
            var titles_filtered = $.ui.autocomplete.filter(_.keys(_titles), request.term);

            titles_filtered = _.values(_.pick(_titles, titles_filtered));

            var keywords_filtered = $.ui.autocomplete.filter(_.keys(_keywords), request.term);

            keywords_filtered = _.flatten(_.values(_.pick(_keywords, keywords_filtered)));

            var ids_filtered = _.union(titles_filtered, keywords_filtered);

            // sort the titles again, since ordering was lost when we did autocomplete.filter
            var node_type_ordering = ["video", "exercise", "content", "topic"]; // custom ordering, with the last in the array appearing first
            ids_filtered.sort(function(id1, id2) {
                var node1 = _nodes[id1];
                var node2 = _nodes[id2];
                // we use the ordering of types found in node_types
                var compvalue = node_type_ordering.indexOf(node2.kind.toLowerCase()) - node_type_ordering.indexOf(node1.kind.toLowerCase());
                return compvalue;
            });

            // From the filtered titles, produce labels (html) and values (for doing stuff)
            var results = [];

            var is_admin = window.statusModel.get("is_admin");
            for (var i = 0; i < ids_filtered.length; i++) {
                var node = _nodes[ids_filtered[i]];

                // exclude videos that aren't available
                if (!is_admin && node.kind.toLowerCase() == "video" && !node.available) {
                    continue;
                }

                var label = "<span class='autocomplete icon-" + node.kind.toLowerCase() + " " + (node.available ? "" : "un") + "available'>" + " " + gettext(node.title) + "</span>&nbsp;";
                results.push({
                    label: label,
                    value: ids_filtered[i]
                });
            }
            response(results.slice(0, 15)); // slice after filtering, see #1563
        },
        select: function( event, ui ) {
            // When they click a specific item, just go there (if we recognize it)
            var id = ui.item.value;
            if (_nodes && id in _nodes && _nodes[id]) {
                if ("channel_router" in window) {
                    window.channel_router.navigate(_nodes[id].path, {trigger: true});
                } else {
                    window.location.href = "/learn/" + _nodes[id].path;
                }
            } else {
                show_message("error", gettext("Unexpected error: no search data found for selected item. Please select another item."));
            }
        }

    });

    $("#search-button").click(function() {
        $("#search-box").submit();
    });

});

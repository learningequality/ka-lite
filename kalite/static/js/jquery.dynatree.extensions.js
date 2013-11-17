// Extensions to the JQuery dynatree package, allowing for generic call-back registration
//   and to interface easily with getting/setting selected paths.

// open and close the topic tree, and call `display_selected_topics` when closed
window.toggle_tree_callbacks = [];
window.last_paths = [];
function toggle_tree(force_callbacks) {
    // Toggle, and do callbacks when tree closes.
    var window_will_close = window.showing_tree;   // when tree closes

    if (get_topic_paths_from_tree().length == 0) {
        // When nothing's selected, make sure it stays open
        window.showing_tree = true;
        $("#content_tree_toggle").toggle(true);
        $("#content_tree").slideDown();
        if (window_will_close || force_callbacks) {
            do_callbacks();
        }
        return;
    }

    window.showing_tree = !window.showing_tree;
    $("#content_tree_toggle").toggle();
    $("#content_tree").slideToggle();
    if (window_will_close) {
        do_callbacks();
    }
}

function do_callbacks(force) {
    var cur_paths = get_topic_paths_from_tree();

    // Determine if we should call the callbacks
    var trigger_callbacks = force;
    if (!force) {
        for (pi in cur_paths) {
            if (window.last_paths.indexOf(cur_paths[pi]) != -1) {
                continue;
            }
            trigger_callbacks = true;
        }
    }
    
    // Build a display string
    var topics = ""
    for (pi in cur_paths) {
        if (pi > 0) {
            topics += ", ";
        }
        parts = cur_paths[pi].split("/");
        if (parts.length > 0) {
            topics += parts[parts.length-2]; // trailing slash leaves an empty at the end
        }
    }
    // Show linked topics (to reopen the tree if clicked) if some are selected,
    //   or a non-clickable "None" if none are selected.
    $("#topic_paths").text(topics != "" ? topics : "");
    $("#topic_paths_note").text(topics == "" ? ("[" + gettext("None; Please select now") + "]") : "");

    if (trigger_callbacks) {
        for (cbi in window.toggle_tree_callbacks) {
            window.toggle_tree_callbacks[cbi](cur_paths);
        }
    }
    window.last_paths = cur_paths;
    
}

function get_topic_paths_from_tree() {
    var paths = [];
    $.each($("#content_tree").dynatree("getSelectedNodes"), function(ind, node) {
        if (!node.parent.parent || !node.parent.bSelected) {
            paths.push(node.data.key);
        }
    });
    return paths;
}

function set_topic_paths_in_tree(dynatree, paths) {

    var cur_paths = get_topic_paths_from_tree();
    for (pi in paths) {
        dynatree.selectKey(paths[pi]);
    }
    do_callbacks()
}
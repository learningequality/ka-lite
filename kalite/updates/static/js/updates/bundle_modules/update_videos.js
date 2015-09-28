var api = require("utils/api");
var $ = require("base/jQuery");
require("jquery.fancytree/dist/jquery.fancytree");
var messages = require("utils/messages");
var base = require("updates/base");
var connectivity = require("utils/connectivity");
var sprintf = require("sprintf-js").sprintf;
var get_params = require("utils/get_params");

require("../../../css/updates/update_videos.less");

// Callback functions

var lastKey = null;
var nErrors = 0;
var videos_downloading = false;
var numVideos = null;
var downloading_node = null;

function video_start_callback(progress_log, resp) {
    lastKey = null;
    nErrors = 0;
    videos_downloading = false;
}

function video_reset_callback() {
    lastKey = null;
    nErrors = 0;
    videos_downloading = false;
}

function video_check_callback(progress_log, resp) {
    // When video status is checked
    videos_downloading = (progress_log !== null) && (progress_log.process_name !== null);

    if (progress_log) { // check succeeded
        // Determine what changed, and what to update
        var currentKey = progress_log.stage_name;

        // update key
        var keyCompleted = null;
        if (currentKey != lastKey) {
            keyCompleted = lastKey;
        } else if (progress_log.stage_percent == 1.0) {
            keyCompleted = currentKey;
        }

        var status = progress_log.stage_status;

        if (keyCompleted) {
            if (!status) {
                setNodeClass(keyCompleted, "complete");
            } else if (status == "error") {
                // update # errors
                nErrors++;
            }

            if (progress_log.process_percent == 1.0) {
            // 100% done with the set of videos.  Display based on the total

                // 100% done with ALL videos.
                $(".progress-section, #cancel-download").hide();
                $("#download-videos").removeAttr("disabled");
                base.updatesReset(progress_log.process_name);
                //update fancytree to reflect the current status of the videos
                $.each(downloading_node, function(ind, node) {
                    updateNodeCompleteness(node, "complete");
                });
                return;

            } else if (lastKey != currentKey) {
                setNodeClass(currentKey, "partial");
            }

        } else if (progress_log.completed) {
            // Completed without 100% done means the videos were cancelled.
            $("#retry-video-download").hide();
            $("#cancel-download").hide();
            $("#download-videos").removeAttr("disabled");
        } else {
            // Everything's good for now!
            setNodeClass(currentKey, "partial");
            $("#retry-video-download").hide();
            $("#cancel-download").show();
            $("#download-videos").removeAttr("disabled");
        }

        lastKey = currentKey;

    } else { // check failed.
        $("#download-videos").removeAttr("disabled");
    }
}

var video_callbacks = {
    start: video_start_callback,
    check: video_check_callback,
    reset: video_reset_callback
};

var tree;


$(function() {

    api.doRequest(window.Urls.get_annotated_topic_tree(), {})
        .success(function(treeData) {
            $("#content_tree").html("");

            if (treeData === null) {
                messages.show_message("warning", gettext("Apologies, but there are no videos available for this language."));
            } else {

                $("#content_tree").fancytree({
                    autoCollapse: true,
                    aria: true, // Enable WAI-ARIA support.
                    checkbox: true, // Show checkboxes.
                    debugLevel: 0, // 0:quiet, 1:normal, 2:debug
                    selectMode: 3,
                    source: [treeData],
                    click: function(event, data) {
                        if (data.targetType === "checkbox"){
                            return true;
                        }else{
                            if(data.node.hasChildren()){
                                data.node.toggleExpanded();
                            }else{
                                data.node.toggleSelected();
                            }
                            return false;
                        }
                    },
                    dblclick: function(event, data) {
                        data.node.toggleSelected();
                        return false;
                    },
                    select: function(event, node) {

                        var newVideoMetadata = getSelectedIncompleteMetadata();
                        var oldVideoMetadata = getSelectedStartedMetadata();
                        var newVideoCount    = newVideoMetadata.length;
                        var oldVideoCount    = oldVideoMetadata.length;
                        var newVideoSize     = _(newVideoMetadata).reduce(function(memo, meta) {
                            // Reduce to compute sum
                            return memo + meta.size;
                        }, 0);
                        var oldVideoSize     = _(oldVideoMetadata).reduce(function(memo, meta) {
                            return memo + meta.size;
                        }, 0);

                        $("#download-legend-unselected").toggle((newVideoCount + oldVideoCount) === 0);

                        if (newVideoCount === 0) {
                            $("#download-videos").hide();
                        } else {
                            $("#download-videos-text").text(sprintf(gettext("Download %(vid_count)d new selected video(s)") + " (%(vid_size).1f %(vid_size_units)s)", {
                                vid_count: newVideoCount,
                                vid_size: (newVideoSize < Math.pow(2, 10)) ? newVideoSize : newVideoSize / Math.pow(2, 10),
                                vid_size_units: (newVideoSize < Math.pow(2, 10)) ? "MB" : "GB"
                            }));
                            $("#download-videos").toggle($("#download-videos").attr("disabled") === undefined); // only show if we're not currently downloading
                        }
                        if (oldVideoCount === 0) {
                            $("#delete-videos").hide();
                        } else {
                            $("#delete-videos-text").text(sprintf(gettext("Delete %(vid_count)d selected video(s)") + " (%(vid_size).1f %(vid_size_units)s)", {
                                vid_count: oldVideoCount,
                                vid_size: (oldVideoSize < Math.pow(2, 10)) ? oldVideoSize : oldVideoSize / Math.pow(2, 10),
                                vid_size_units: (oldVideoSize < Math.pow(2, 10)) ? "MB" : "GB"
                            }));
                            $("#delete-videos").show();
                        }
                    },
                    init: function(event, data) {
                        tree = data.tree;
                        connectivity.with_online_status("server", function(server_is_online) {
                            // We assume the distributed server is offline; if it's online, then we enable buttons that only work with internet.
                            // Best to assume offline, as online check returns much faster than offline check.
                            if(server_is_online){
                                $(".enable-when-server-online").removeAttr("disabled");
                                base.updatesStart("videodownload", 5000, video_callbacks);
                            } else {
                                messages.show_message("error", gettext("Could not connect to the central server; videos cannot be downloaded at this time."));
                            }
                        });
                    }
                });
            }
        });

    $("#download-videos").click(function() {
        messages.clear_messages();

        // Prep
        // Get all videos to download
        var youtube_ids = getSelectedIncompleteMetadata("youtube_id");
        numVideos = youtube_ids.length;

        // Do the request
        api.doRequest(window.Urls.start_video_download(), {youtube_ids: youtube_ids})
            .success(function() {
                base.updatesStart("videodownload", 2000, video_callbacks);
            })
            .fail(function(resp) {
                $("#download-videos").removeAttr("disabled");
            });

        //keep a copy of the selected node
        downloading_node = tree.getSelectedNodes();
        // Update the UI
        unselectAllNodes();
        $("#cancel-download").show();
        $("#download-videos").attr("disabled", "disabled");

        // Send event.  NOTE: DO NOT WRAP STRINGS ON THIS CALL!!
        ga_track("send", "event", "update", "click-download-videos", "Download Videos", youtube_ids.length);
    });

    // Delete existing videos
    $("#delete-videos").click(function() {
        messages.clear_messages();

        $("#modal_dialog").dialog({
            title: gettext("Are you sure you want to delete?"),
            resizable: true,
            draggable: true,
            height: 200,
            modal: true,
            buttons: [{
                id: "input_yes",
                text: gettext("Yes"),
                click: function() {
                    // This function can only get called when
                    //   no downloads are in progress.
                    // Prep
                    // Get all videos marked for download

                    //keep a copy of the selected node
                    downloading_node = tree.getSelectedNodes();

                    var youtube_ids = getSelectedStartedMetadata("youtube_id");
                    // Do the request
                    api.doRequest(window.Urls.delete_videos(), {youtube_ids: youtube_ids})
                        .success(function() {
                            //update fancytree to reflect the current status of the videos
                            $.each(downloading_node, function(ind, node) {
                                updateNodeCompleteness(node, "unstarted");
                            });

                            $.each(youtube_ids, function(ind, id) {
                                setNodeClass(id, "unstarted");
                            });
                        })
                        .fail(function(resp) {
                            $(".progress-waiting").hide();
                        });
                        // Update the UI
                        unselectAllNodes();

                        // Send event.  NOTE: DO NOT WRAP STRINGS ON THIS CALL!!
                        ga_track("send", "event", "update", "click-delete-videos", "Delete Videos", youtube_ids.length);

                        $(this).dialog("close");
                    }
                },
                {
                    id: "input_cancel",
                    text: gettext("No"),
                    click: function() {
                        $(this).dialog("close");
                }
            }]

        });
        $("button.ui-dialog-titlebar-close").hide();
        $("#modal_dialog").text(gettext("Deleting the downloaded video(s) will lead to permanent loss of data"));

    });

    // Cancel current downloads
    $("#cancel-download").click(function() {
        messages.clear_messages();

        // Prep

        // Do the request
        api.doRequest(window.Urls.cancel_video_download())
            .success(function() {
                // Reset ALL of the progress tracking
                base.updatesReset();

                // Update the UI
                $("#download-videos").removeAttr("disabled");
                $("#cancel-download").hide();
            });

        // Update the UI

        // Send event.  NOTE: DO NOT WRAP STRINGS ON THIS CALL!!
        ga_track("send", "event", "update", "click-cancel-downloads", "Cancel Downloads");
    });

    // Retry video download
    $("#retry-video-download").click(function() {
        // Prep

        // Do the request
        api.doRequest(window.Urls.start_video_download(), {});

        // Update the UI
        $(this).attr("disabled", "disabled");

        // Send event.  NOTE: DO NOT WRAP STRINGS ON THIS CALL!!
        ga_track("send", "event", "update", "click-retry-download", "Retry Download");
    });


    if ($("#download_language_selector option").length > 1) {
        show_language_selector();
    }

    $("#download_language_selector").change(function() {
         var lang_code = $("#download_language_selector option:selected")[0].value;
         window.location.href = get_params.setGetParam(window.location.href, "lang", lang_code);
    });
    // end onload functions
});

function show_language_selector() {
    $("#download_language_selector").show();
    $("#language_choice_titlebar a").hide();
}

/* script functions for doing stuff with the topic tree*/
function unselectAllNodes() {
    $.each(tree.getSelectedNodes(), function(ind, node) {
        node.setSelected(false);
    });
}

function getSelectedVideos(vid_type) {
    var avoid_type = null;
    switch (vid_type) {
        case "started": avoid_type = "unstarted"; break;
        case "incomplete": avoid_type ="complete"; break;
        default: assert(false, sprintf("Unknown vid type: %s", vid_type)); break;
    }
    var arr = tree.getSelectedNodes();
    var vids = _.uniq($.grep(arr, function(node) {
        return node.extraClasses != avoid_type && node.children === null;
    }));
    return vids;
}


function getSelectedIncompleteVideos() {
    return getSelectedVideos("incomplete");
}

function getSelectedStartedVideos() {
    return getSelectedVideos("started");
}

function getSelectedMetadata(vid_type, data_type) {
    var videos = _.uniq(getSelectedVideos(vid_type), function(node) {
        return node.key;
    });
    var metadata = $.map(videos, function(node) {
        switch (data_type) {
            case null:
            case undefined: return node.data;
            case "youtube_id": return node.key;
            default: assert(false, sprintf("Unknown data type: %s", data_type)); break;
        }
    });
    return metadata;
}
function getSelectedIncompleteMetadata(data_type) {
    return getSelectedMetadata("incomplete", data_type);
}

function getSelectedStartedMetadata(data_type) {
    return getSelectedMetadata("started", data_type);
}

function withNodes(nodeKey, callback, currentNode) {
    if (!currentNode) {
        currentNode = tree.rootNode.children[0];
    }
    $.each(currentNode.children || [], function(ind, child) {
        if (child.data.key == nodeKey) {
            callback(child);
        }
        withNodes(nodeKey, callback, child);
    });
}

function setNodeClass(nodeKey, className) {
    withNodes(nodeKey, function(node) {
        // $(node.span).removeClass("unstarted partial complete").extraClasses(className);  no idea why run this here?
        node.extraClasses = className;
        if (node.parent) {
            updateNodeClass(node.parent);
        }
    });
}

function updateNodeClass(node) {
    if (node.children) {
        var complete = true;
        var unstarted = true;
        for (var i = 0; i < node.children.length; i++) {
            var child = node.children[i];
            if (child.extraClasses != "complete") {
                complete = false;
            }
            if (child.extraClasses != "unstarted") {
                unstarted = false;
            }
        }
        if (complete) {
            setNodeClass(node.data.key, "complete");
        } else if (unstarted) {
            setNodeClass(node.data.key, "unstarted");
        } else {
            setNodeClass(node.data.key, "partial");
        }
    }
}

function updateNodeCompleteness(node, tobe_class){
    //update the selected node
    node.extraClasses = tobe_class;
    node.renderStatus();
    //1. update the selected node's ancestors
    if (node.parent) {
        recurParentNode(node.parent, tobe_class);
    }
    //2. update the selected node's children
    if (node.children) {
        recurChildNode(node, tobe_class);
    }
}

function recurParentNode(node, tobe_class) {
    var completeness = false;
    for (var i = 0; i < node.children.length; i++) {
        var child = node.children[i];
        if (child.extraClasses != tobe_class){
            completeness = true;
            break;
        }
    }
    if (completeness) {
        node.extraClasses = "partial";
        node.renderStatus();
    } else {
        node.extraClasses = tobe_class;
        node.renderStatus();
    }
    if (node.parent) {
        recurParentNode(node.parent, tobe_class);
    }
}

function recurChildNode(node, tobe_class) {
    for (var i = 0; i < node.children.length; i++) {
        var child = node.children[i];
        child.extraClasses = tobe_class;
        child.renderStatus();
        if(child.children){
            recurChildNode(child, tobe_class);
        }
    }
}

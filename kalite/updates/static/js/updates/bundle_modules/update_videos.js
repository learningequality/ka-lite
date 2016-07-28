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
            if (!status && (status !== "error")) {
                setNodeClass(tree.getNodeByKey(keyCompleted), "complete");
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

            }

        } else if (progress_log.completed) {
            // Completed without 100% done means the videos were cancelled.
            $("#cancel-download").hide();
            $("#download-videos").removeAttr("disabled");
        } else {
            // Everything's good for now!
            setNodeClass(tree.getNodeByKey(currentKey), "partial");
            $("#cancel-download").show();
        }

        lastKey = currentKey;
    }
}

var tree;
var lang_code;

var video_callbacks = {
    start: video_start_callback,
    check: video_check_callback,
    reset: video_reset_callback
};

var scan_callbacks = {
    start: function() {},
    check: function(progress_log, resp) {
        if (progress_log.completed) {
            base.updatesReset(progress_log.process_name);
            messages.show_message("success", progress_log.notes);
            tree.reload();
            tree.options.select();
            $("#scan-videos").removeAttr("disabled");
        }
    }
};


$(function() {
    lang_code = $("#download_language_selector option:selected")[0].value;

    $("#content_tree").html("");

    $("#content_tree").fancytree({
        autoCollapse: true,
        aria: true, // Enable WAI-ARIA support.
        checkbox: true, // Show checkboxes.
        debugLevel: 0, // 0:quiet, 1:normal, 2:debug
        selectMode: 3,
        clickFolderMode: 2,
        source: {
            url: window.Urls.get_update_topic_tree(),
            data: { parent: "root", lang: lang_code},
            cache: false
        },
        postProcess: function(event, data) {
            data.response = _.map(data.response, function(node) {
                if (node.files_complete === 0 || node.files_complete === null || typeof node.files_complete === "undefined") {
                    node["extraClasses"] = "unstarted";
                } else if (node.files_complete < node.total_files) {
                    node["extraClasses"] = "partial";
                } else {
                    node["extraClasses"] = "complete";
                }
                if (node.kind == "Topic") {
                    node["lazy"] = true;
                    node["folder"] = true;
                }
                node["key"] = node.youtube_id || node.id;
            });
        },
        lazyLoad: function(event, data){
            var node = data.node;
            data.result = {
              url: window.Urls.get_update_topic_tree(),
              data:{ parent: node.key, lang: lang_code},
              cache: false
            };
        },
        loadChildren: function(event, data) {
            // Apply parent's state to new child nodes:
            data.node.fixSelection3AfterClick();
        },
        select: function(event, node) {
            // only allow selection if we're not currently downloading
            if (!videos_downloading) {

                var videoMetadata = tree.getSelectedNodes(true);
                var newVideoCount    = _.reduce(videoMetadata, function(memo, meta) {
                    return memo + (meta.data.total_files - meta.data.files_complete);
                }, 0);
                var oldVideoCount    = _.reduce(videoMetadata, function(memo, meta) {
                    return memo + meta.data.files_complete;
                }, 0);
                var newVideoSize     = _(videoMetadata).reduce(function(memo, meta) {
                    // Reduce to compute sum
                    return memo + meta.data.remote_size;
                }, 0);
                var oldVideoSize     = _(videoMetadata).reduce(function(memo, meta) {
                    return memo + meta.data.size_on_disk;
                }, 0);

                if (newVideoCount === 0) {
                    $("#download-videos").attr("disabled", "disabled");
                    $("#download-videos-text").text(gettext("Please select videos to download (below)"));
                } else {
                    $("#download-videos-text").text(sprintf(gettext("Download %(vid_count)d new selected video(s)") + " (%(vid_size).1f %(vid_size_units)s)", {
                        vid_count: newVideoCount,
                        vid_size: (newVideoSize < Math.pow(2, 30)) ? newVideoSize / Math.pow(2, 20) : newVideoSize / Math.pow(2, 30),
                        vid_size_units: (newVideoSize < Math.pow(2, 30)) ? "MB" : "GB"
                    }));
                    $("#download-videos").removeAttr("disabled");
                }
                if (oldVideoCount === 0) {
                    $("#delete-videos").attr("disabled", "disabled");
                    $("#delete-videos-text").text(gettext("Please select videos to delete (below)"));
                } else {
                    $("#delete-videos-text").text(sprintf(gettext("Delete %(vid_count)d selected video(s)") + " (%(vid_size).1f %(vid_size_units)s)", {
                        vid_count: oldVideoCount,
                        vid_size: (oldVideoSize < Math.pow(2, 30)) ? oldVideoSize / Math.pow(2, 20) : oldVideoSize / Math.pow(2, 30),
                        vid_size_units: (oldVideoSize < Math.pow(2, 30)) ? "MB" : "GB"
                    }));
                    $("#delete-videos").removeAttr("disabled");
                }
            } else {
                return false;
            }
        },
        init: function(event, data) {
            tree = data.tree;
            connectivity.with_online_status("server", function(server_is_online) {
                // We assume the distributed server is offline; if it's online, then we enable buttons that only work with internet.
                // Best to assume offline, as online check returns much faster than offline check.
                if(server_is_online){
                    base.updatesStart("videodownload", 5000, video_callbacks);
                } else {
                    messages.show_message("error", gettext("Could not connect to the central server; videos cannot be downloaded at this time."));
                }
            });
        }
    });

    $("#download-videos").click(function() {
        messages.clear_messages();
        $("#download-videos").attr("disabled", "disabled");

        // Prep
        // Get all videos to download
        var paths = _.map(tree.getSelectedNodes(true), function(node) { return node.data.path; });

        // Do the request
        api.doRequest(window.Urls.start_video_download(), {paths: paths, lang: lang_code})
            .success(function() {
                base.updatesStart("videodownload", 2000, video_callbacks);
            })
            .fail(function(resp) {
                $("#download-videos").removeAttr("disabled");
            });

        //keep a copy of the selected node
        downloading_node = tree.getSelectedNodes();
        var number_of_videos = _.reduce(tree.getSelectedNodes(true), function(memo, meta) {
            return memo + (meta.data.total_files - meta.data.files_complete);
        }, 0);
        // Update the UI
        unselectAllNodes();
        $("#cancel-download").show();

        // Send event.  NOTE: DO NOT WRAP STRINGS ON THIS CALL!!
        ga_track("send", "event", "update", "click-download-videos", "Download Videos", number_of_videos);
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
                    downloading_node = tree.getSelectedNodes(true);

                    var paths = _.map(tree.getSelectedNodes(true), function(node) { return node.data.path; });
                    // Do the request
                    api.doRequest(window.Urls.delete_videos(), {paths: paths, lang: lang_code})
                        .success(function() {
                            //update fancytree to reflect the current status of the videos
                            $.each(downloading_node, function(ind, node) {
                                updateNodeCompleteness(node, "unstarted");
                            });

                        })
                        .fail(function(resp) {
                            $(".progress-waiting").hide();
                        });
                        // Update the UI
                        unselectAllNodes();

                        // Send event.  NOTE: DO NOT WRAP STRINGS ON THIS CALL!!
                        ga_track("send", "event", "update", "click-delete-videos", "Delete Videos", _.reduce(downloading_node, function(memo, meta) {
                            return memo + meta.data.files_complete;
                        }, 0));

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

    if ($("#download_language_selector option").length > 1) {
        show_language_selector();
    }

    $("#download_language_selector").change(function() {
        lang_code = $("#download_language_selector option:selected")[0].value;
         window.location.href = get_params.setGetParam(window.location.href, "lang", lang_code);
    });

    // Cancel current downloads
    $("#scan-videos").click(function() {
        messages.clear_messages();

        // Prep
        $("#scan-videos").attr("disabled", "disabled");
        
        // Add warning for user.
        messages.show_message("warning", gettext("Scanning for videos and updating your database - this can take several minutes, depending on how many videos that are found. Please be patient and stay on this page. Once completed, results will be shown on this page."));

        // Do the request
        api.doRequest(window.Urls.video_scan(), {lang: lang_code})
            .success(function() {
                base.updatesStart("videoscan", 2000, scan_callbacks);

                // Update the UI
                $("#download-videos").attr("disabled", "disabled");
                $("#delete-videos").attr("disabled", "disabled");
            });

        // Update the UI

        // Send event.  NOTE: DO NOT WRAP STRINGS ON THIS CALL!!
        ga_track("send", "event", "update", "click-cancel-downloads", "Cancel Downloads");
    });
    // end onload functions
});

function show_language_selector() {
    $("#download_language_selector").show();
    $("#language_choice_titlebar a").hide();
}

/* script functions for doing stuff with the topic tree*/
function unselectAllNodes() {
    $.each(tree.getSelectedNodes(true), function(ind, node) {
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
    var arr = tree.getSelectedNodes(true);
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

function setNodeClass(node, className) {
    if (node !== null) {
        if (node.extraClasses != className) {
            node.extraClasses = className;
            if (node.parent !== null) {
                updateNodeClass(node.parent);
            }
        }
    }
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
            setNodeClass(node, "complete");
        } else if (unstarted) {
            setNodeClass(node, "unstarted");
        } else {
            setNodeClass(node, "partial");
        }
    }
}

function updateNodeCompleteness(node, tobe_class){
    //update the selected node
    node.extraClasses = tobe_class;
    if (tobe_class == "unstarted") {
        // Node has been deleted, set its data to no files complete, and no size.
        node.data.size_on_disk = 0;
        node.data.files_complete = 0;
    }
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

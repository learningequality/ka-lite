// Callback functions

var lastKey = null;
var nErrors = 0;
var videos_downloading = false;
var numVideos = null;

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
    videos_downloading = (progress_log != null) && (progress_log.process_name != null);

    if (progress_log) { // check succeeded
        // Determine what changed, and what to update
        var currentKey = progress_log.stage_name;

        // update key
        var keyCompleted = null;
        if (currentKey != lastKey) {
            keyCompleted = lastKey;
        } else if (progress_log.stage_percent == 1) {
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

            if (progress_log.process_percent == 1.) {
            // 100% done with the set of videos.  Display based on the total

                // 100% done with ALL videos.
                $(".progress-section, #cancel-download").hide();
                $("#download-videos").removeAttr("disabled");
                updatesReset(progress_log.process_name);
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

function initDynatree(treeData) {
    if ($.isEmptyObject(treeData)) {
        $("#content_tree h2").html(gettext("Apologies, but there are no videos available for this language."));
    }

    $('#content_tree').dynatree('getRoot').addChild(treeData);
    $('#content_tree h4').hide();
}

function downloadVideos() {
    clear_messages();

    var youtube_ids = getSelectedIncompleteMetadata("youtube_id");
    numVideos = youtube_ids.length;

    doRequest(URL_START_VIDEO_DOWNLOADS, { youtube_ids: youtube_ids })
        .success(function() {
            updatesStart("videodownload", 5000, video_callbacks);
        })
        .fail(function(resp) {
            $("#download-videos").removeAttr("disabled");
        });

    unselectAllNodes();
    $("#cancel-download").show();
    $("#download-videos").attr("disabled", "disabled");
}

function displayDeleteVideosDialog() {
    clear_messages();

    $("#modal_dialog").dialog(modalDialogAttrs);
    $("button.ui-dialog-titlebar-close").hide();
    $("#modal_dialog").text(gettext("Deleting the downloaded video(s) will lead to permanent loss of data"));
}

function cancelDownload() {
    clear_messages();

    doRequest(URL_CANCEL_VIDEO_DOWNLOADS)
        .success(function() {
            // Reset ALL of the progress tracking
            updatesReset();

            // Update the UI
            $("#download-videos").removeAttr("disabled");
            $("#cancel-download").hide();
        });
}

function retryVideoDownload() {
    doRequest(URL_START_VIDEO_DOWNLOADS, {});

    // Update the UI
    $(this).attr("disabled", "disabled");
}

$(function() {

    $("#content_tree").dynatree(dynatreeAttrs);

    doRequest(URL_GET_ANNOTATED_TOPIC_TREE, {})
        .success(initDynatree);

    $("#download-videos").click(function() {
        downloadVideos();

        // NOTE: DO NOT WRAP STRINGS ON THIS CALL!!
        ga_track("send", "event", "update", "click-download-videos", "Download Videos", youtube_ids.length);
    });

    $("#delete-videos").click(displayDeleteVideosDialog);

    $("#cancel-download").click(function() {
        cancelDownload();
        ga_track("send", "event", "update", "click-cancel-downloads", "Cancel Downloads");
    });

    $("#retry-video-download").click(function() {
        retryVideoDownload();
        ga_track("send", "event", "update", "click-retry-download", "Retry Download");
    });


    if ($("#download_language_selector option").length > 1) {
        $("#language_choice_titlebar a").attr("onclick", "show_language_selector();");
    }

    $("#download_language_selector").change(function() {
         var lang_code = $("#download_language_selector option:selected")[0].value;
         window.location.href = setGetParam(window.location.href, "lang", lang_code);
    });
});

function show_language_selector() {
    $("#download_language_selector").show();
    $("#language_choice_titlebar a").hide();
}

/* script functions for doing stuff with the topic tree*/
function unselectAllNodes() {
    $.each($("#content_tree").dynatree("getSelectedNodes"), function(ind, node) {
        node.select(false);
    });
}

function getSelectedVideos(vid_type) {
    var avoid_type = null;
    switch (vid_type) {
        case "started": avoid_type = "unstarted"; break;
        case "incomplete": avoid_type ="complete"; break;
        default: assert(false, sprintf("Unknown vid type: %s", vid_type)); break;
    }

    var arr = $("#content_tree").dynatree("getSelectedNodes");
    var vids = _.uniq($.grep(arr, function(node) {
        return node.data.addClass != avoid_type && node.childList == null;
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
        return node.data.key;
    });
    var metadata = $.map(videos, function(node) {
        switch (data_type) {
            case null:
            case undefined: return node.data;
            case "youtube_id": return node.data.key;
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
        currentNode = $("#content_tree").dynatree("getTree").tnRoot.childList[0];
    }
    $.each(currentNode.childList || [], function(ind, child) {
        if (child.data.key == nodeKey) {
            callback(child);
        }
        withNodes(nodeKey, callback, child);
    });
}

function setNodeClass(nodeKey, className) {
    withNodes(nodeKey, function(node) {
        $(node.span).removeClass("unstarted partial complete").addClass(className);
        node.data.addClass = className;
        if (node.parent) {
            updateNodeClass(node.parent);
        }
    });
}

function updateNodeClass(node) {
    if (node.childList) {
        var complete = true;
        var unstarted = true;
        for (var i = 0; i < node.childList.length; i++) {
            var child = node.childList[i];
            if (child.data.addClass != "complete") {
                complete = false;
            }
            if (child.data.addClass != "unstarted") {
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

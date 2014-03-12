// Callback functions

var lastKey = null;
var nErrors = 0
var videos_downloading = false;

function video_start_callback(progress_log, resp) {
    if (!progress_log) {
        //handleFailedAPI(resp, "Error starting updates process");
    }
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
        } else if (progress_log.stage_percent == 1.) {
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

                if (nErrors != 0) {
                    // Redisplay the download message as a warning.
                    show_message("warning", get_message("id_videodownload"), "id_videodownload");
                    // could show the retry button, but we'd have to store which videos
                    //   went poorly.
                }

                // 100% done with ALL videos.
                $(".progress-section, #cancel-download").hide();
                $("#download-videos").removeAttr("disabled");
                updatesReset(progress_log.process_name);
                if ($(".subtitle-section:visible").length == 0) {
                    $("#cancel-download").hide();
                }
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
        handleFailedAPI(resp, gettext("Error downloading videos"), "id_video_download");
        clearInterval(window.download_subtitle_check_interval);
        $("#download-videos").removeAttr("disabled");
    }
}

var video_callbacks = {
    start: video_start_callback,
    check: video_check_callback,
    reset: video_reset_callback
};


/*
 depends on the following definitions:
var URL_GET_ANNOTATED_TOPIC_TREE = "{% url get_annotated_topic_tree %}";
var URL_START_VIDEO_DOWNLOADS = "{% url start_video_download %}";
var URL_DELETE_VIDEOS = "{% url delete_videos %}";
var URL_CANCEL_VIDEO_DOWNLOADS = "{% url cancel_video_download %}";
*/


$(function() {

    setTimeout(function() {
        doRequest(URL_GET_ANNOTATED_TOPIC_TREE, {}).success(function(treeData) {

            if ($.isEmptyObject(treeData)) {
                $("#content_tree h2").html(gettext("Apologies, but there are no videos available for this language."));
            }

            $("#content_tree").dynatree({
                imagePath:"../images/",
                checkbox: true,
                selectMode: 3,
                children: treeData,
                debugLevel: 0,
                onSelect: function(select, node) {

                    var newVideoMetadata = getSelectedIncompleteMetadata();
                    var oldVideoMetadata = getSelectedStartedMetadata()
                    var newVideoCount    = newVideoMetadata.length;
                    var oldVideoCount    = oldVideoMetadata.length;
                    var newVideoSize     = _(newVideoMetadata).reduce(function(memo, meta) {
                        // Reduce to compute sum
                        return memo + meta.size;
                    }, 0);
                    var oldVideoSize     = _(oldVideoMetadata).reduce(function(memo, meta) {
                        return memo + meta.size;
                    }, 0);

                    $("#download-legend-unselected").toggle((newVideoCount + oldVideoCount) == 0);
                    $("#help-info").toggle((newVideoCount + oldVideoCount) == 0);

                    if (newVideoCount == 0) {
                        $("#download-videos").hide();
                    } else {
                        $("#download-videos-text").text(sprintf(gettext("Download %(vid_count)d new selected video(s)") + " (%(vid_size).1f %(vid_size_units)s)", {
                            vid_count: newVideoCount,
                            vid_size: (newVideoSize < Math.pow(2, 10)) ? newVideoSize : newVideoSize / Math.pow(2, 10),
                            vid_size_units: (newVideoSize < Math.pow(2, 10)) ? "MB" : "GB"
                        }));
                        $("#download-videos").toggle($("#download-videos").attr("disabled") === undefined); // only show if we're not currently downloading
                    }
                    if (oldVideoCount == 0) {
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
                onDblClick: function(node, event) {
                    node.toggleSelect();
                },
                onKeydown: function(node, event) {
                    if( event.which == 32 ) {
                        node.toggleSelect();
                        return false;
                    }
                },
                onPostInit: function() {
                    updatesStart("videodownload", 5000, video_callbacks);
                }
            });
        });
    }, 200);

    $("#download-videos").click(function() {
        // Prep
        // Get all videos to download
        var youtube_ids = getSelectedIncompleteMetadata("youtube_id");
        var numVideos = youtube_ids.length;

        // Do the request
        doRequest(URL_START_VIDEO_DOWNLOADS, {youtube_ids: youtube_ids})
            .success(function() {
                updatesStart("videodownload", 5000, video_callbacks);
                show_message(
                    "success",
                    sprintf(gettext("Download of %(num)d video(s) starting soon!"), {num: numVideos}),
                    "id_videodownload"
                );
            })
            .fail(function(resp) {
                handleFailedAPI(resp, gettext("Error starting video download"), "id_video_download");
                $("#download-videos").removeAttr("disabled");
            });

        // Update the UI
        unselectAllNodes();
        $("#cancel-download").show();
        $("#download-videos").attr("disabled", "disabled");

        // Send event.  NOTE: DO NOT WRAP STRINGS ON THIS CALL!!
        ga_track("send", "event", "update", "click-download-videos", "Download Videos", youtube_ids.length);
    });

    // Delete existing videos
    $("#delete-videos").click(function() {
        // This function can only get called when
        //   no downloads are in progress.

        // Prep
        // Get all videos marked for download
        var youtube_ids = getSelectedStartedMetadata("youtube_id");

        // Do the request
        doRequest(URL_DELETE_VIDEOS, {youtube_ids: youtube_ids})
            .success(function() {
                handleSuccessAPI("id_video_download");
                $.each(youtube_ids, function(ind, id) {
                    setNodeClass(id, "unstarted");
                });
            })
            .fail(function(resp) {
                handleFailedAPI(resp, gettext("Error deleting videos"), "id_video_download");
                $(".progress-waiting").hide();
            });

        // Update the UI
        unselectAllNodes();

        // Send event.  NOTE: DO NOT WRAP STRINGS ON THIS CALL!!
        ga_track("send", "event", "update", "click-delete-videos", "Delete Videos", youtube_ids.length);
    });

    // Cancel current downloads
    $("#cancel-download").click(function() {
        // Prep

        // Do the request
        doRequest(URL_CANCEL_VIDEO_DOWNLOADS)
            .success(function() {
                handleSuccessAPI("id_video_download");
                // Reset ALL of the progress tracking
                updatesReset()

                // Update the UI
                $("#download-videos").removeAttr("disabled");
                $("#cancel-download").hide();
            })
            .fail(function(resp) {
                handleFailedAPI(resp, gettext("Error canceling downloads"), "id_video_download");
            });

        // Update the UI

        // Send event.  NOTE: DO NOT WRAP STRINGS ON THIS CALL!!
        ga_track("send", "event", "update", "click-cancel-downloads", "Cancel Downloads");
    });

    // Retry video download
    $("#retry-video-download").click(function() {
        // Prep

        // Do the request
        doRequest(URL_START_VIDEO_DOWNLOADS, {})
            .success(function(resp) {
                handleSuccessAPI("id_video_download");
            })
            .fail(function(resp) {
                handleFailedAPI(resp, gettext("Error restarting downloads"), "id_video_download");
            });

        // Update the UI
        $(this).attr("disabled", "disabled");

        // Send event.  NOTE: DO NOT WRAP STRINGS ON THIS CALL!!
        ga_track("send", "event", "update", "click-retry-download", "Retry Download");
    });


    if ($("#download_language_selector option").length > 1) {
        $("#toggle_language_dropdown").attr("href", "javascript:show_language_selector()");
    }

    $("#download_language_selector").change(function() {
         var lang_code = $("#download_language_selector option:selected")[0].value;
         window.location.href = setGetParam(window.location.href, "lang", lang_code);
    });
    // end onload functions
});

function show_language_selector() {
    $("#download_language_selector").show();
    $("#toggle_language_dropdown").hide()
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

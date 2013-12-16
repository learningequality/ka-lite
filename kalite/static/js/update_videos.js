// Callback functions

var lastKey = null;
var nErrors = 0

function video_start_callback(progress_log, resp) {
    if (!progress_log) {
        //handleFailedAPI(resp, "Error starting updates process");
    }
    lastKey = null;
    nErrors = 0;
}

function video_check_callback(progress_log, resp) {
    // When video status is checked
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
                    set_message("warning", get_message("id_videodownload"), "id_videodownload");
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
    check: video_check_callback
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
            $("#content_tree").dynatree({
                imagePath:"../images/",
                checkbox: true,
                selectMode: 3,
                children: treeData,
                debugLevel: 0,
                onSelect: function(select, node) {

                    var newVideoCount = getSelectedIncompleteYoutubeIDs().length;
                    var oldVideoCount = getSelectedStartedYoutubeIDs().length;

                    $("#download-videos").hide();
                    $("#delete-videos").hide();
                    $("#download-legend-unselected").toggle((newVideoCount + oldVideoCount) == 0);
                    $("#help-info").toggle((newVideoCount + oldVideoCount) == 0);

                    if (newVideoCount > 0) {
                        $(".new-video-count").text(newVideoCount);
                        $("#download-videos").show();
                    }
                    if (oldVideoCount > 0) {
                        $(".old-video-count").text(oldVideoCount);
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
        var youtube_ids = getSelectedIncompleteYoutubeIDs();
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
        var youtube_ids = getSelectedStartedYoutubeIDs();

        // Do the request
        doRequest(URL_DELETE_VIDEOS, {youtube_ids: youtube_ids})
            .success(function() {
                handleSuccessAPI("id_video_download");
                $.each(youtube_ids, function(ind, id) {
                    setNodeClass(id, "unstarted");
                });
            })
            .fail(function(resp) {
                handleFailedAPI(resp, gettext("Error downloading subtitles"), "id_video_download");
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

    // end onload functions
});

/* script functions for doing stuff with the topic tree*/
function unselectAllNodes() {
    $.each($("#content_tree").dynatree("getSelectedNodes"), function(ind, node) {
        node.select(false);
    });
}

function getSelectedIncompleteVideos() {
    var arr = $("#content_tree").dynatree("getSelectedNodes");
    return _.uniq($.grep(arr, function(node) {
        return node.data.addClass != "complete" && node.childList == null;
    }));
}

function getSelectedStartedVideos() {
    var arr = $("#content_tree").dynatree("getSelectedNodes");
    return _.uniq($.grep(arr, function(node) {
        return node.data.addClass != "unstarted" && node.childList == null;
    }));
}

function getSelectedIncompleteYoutubeIDs() {
    var videos = getSelectedIncompleteVideos();
    var youtube_ids = _.uniq($.map(videos, function(node) {
        return node.data.key;
    }));
    return youtube_ids;
}

function getSelectedStartedYoutubeIDs() {
    var videos = getSelectedStartedVideos();
    var youtube_ids = _.uniq($.map(videos, function(node) {
        return node.data.key;
    }));
    return youtube_ids;
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

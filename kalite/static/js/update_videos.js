// Callback functions 

function video_start_callback(progress_log, resp) {
    if (!progress_log) {
        clear_messages()
        show_message("error", resp.status_code + resp.responseText);
    }
}

function video_check_callback(progress_log, resp) {
    // When video status is checked
    if (progress_log) { // check succeeded

        if (progress_log.stage_percent == 1.) {
            // 100% done with the video
            var currentKey = progress_log.stage_name;
            setNodeClass(currentKey, "complete");
            if (progress_log.process_percent == 1.) {
                // 100% done with ALL videos.
                $(".progress-section, #cancel-download").hide();
                updatesReset(progress_log.process_name);
                if ($(".subtitle-section:visible").length == 0) {
                    $("#cancel-download").hide();
                }
                return;
            }

        } else if (progress_log.completed) {
            // Completed without 100% done means there was a problem.
            $("#retry-video-download").show();
            $("#cancel-download").hide();
        } else {
            // Everything's good for now!
            $("#retry-video-download").hide();
            $("#cancel-download").show();
        }
        $("#cancel-download").show();
    } else { // check failed.
        switch (resp.status) {
            case 403:
                window.location.reload()  // Only happens if we were remotely logged out.
                break;
            default:
                show_message("error", "Error downloading videos: " + resp.responseText);
                clearInterval(window.download_subtitle_check_interval)
                break;
        }
    }
}

var video_callbacks = {
    start: video_start_callback,
    check: video_check_callback,
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
        with_online_status("server", function(server_is_online) {
            // We assume the distributed server is offline; if it's online, then we enable buttons that only work with internet.
            // Best to assume offline, as online check returns much faster than offline check.
            if(!server_is_online){
                show_message("error", "{% trans 'The server does not have internet access; new content cannot be downloaded at this time.' %}", "id_offline_message");
            } else {
                $(".enable-when-server-online").removeAttr("disabled");
                clear_message("id_offline_message")
            }
        });

        doRequest(URL_GET_ANNOTATED_TOPIC_TREE, {}).success(function(treeData) {
            $("#content_tree").dynatree({
                imagePath:"../images/",
                checkbox: true,
                selectMode: 3,
                children: treeData,
                debugLevel: 0,
                onSelect: function(select, node) {
                
                    var newVideoCount = findSelectedIncompleteVideos().length;
                    var oldVideoCount = findSelectedStartedVideos().length;
                    
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
        var videos = findSelectedIncompleteVideos();
        var video_queue = $.map(videos, function(node) {
            return node.data.key;
        });
        updatesStart("videodownload", 5000, video_callbacks)

        // Do the request
        doRequest(URL_START_VIDEO_DOWNLOADS, {youtube_ids: video_queue})
            .success(function() {
                updatesStart("videodownload", 5000, video_callbacks)
            })
            .fail(function(response) {
                handleFailedAPI(resp, "Error starting video download");
            });

        // Update the UI
        unselectAllNodes();
        $("#cancel-download").show();
        //$(".progress-section").hide();

        // Send event
        ga_track("send", "event", "update", "click-download-videos", "Download Videos", videos.length);
    });

    // Delete existing videos
    $("#delete-videos").click(function() {
        // This function can only get called when
        //   no downloads are in progress.

        // Prep
        // Get all videos marked for download
        var videos = findSelectedStartedVideos();
        var video_queue = $.map(videos, function(node) {
            return node.data.key;
        });

        // Do the request
        doRequest(URL_DELETE_VIDEOS, {youtube_ids: video_queue})
            .success(function() {
                $.each(video_queue, function(ind, id) {
                    setNodeClass(id, "unstarted");
                });
            })
            .fail(function(resp) {
                handleFailedAPI(resp, "Error downloading subtitles");
                $(".progress-waiting").hide();
            });

        // Update the UI
        unselectAllNodes();

        // Send event
        ga_track("send", "event", "update", "click-delete-videos", "Delete Videos", videos.length);
    });

    // Cancel current downloads
    $("#cancel-download").click(function() {
        // Prep

        // Do the request
        doRequest(URL_CANCEL_VIDEO_DOWNLOADS)
            .success(function() {
                // Reset ALL of the progress tracking
                updatesReset()

                // Update the UI
                $("#cancel-download").hide();
            })
            .fail(function(resp) {
                handleFailedAPI(resp, "Error canceling downloads");
            });

        // Update the UI

        // Send event
        ga_track("send", "event", "update", "click-cancel-downloads", "Cancel Downloads");
    });

    // Retry video download
    $("#retry-video-download").click(function() {
        // Prep

        // Do the request
        doRequest(URL_START_VIDEO_DOWNLOADS, {})
            .fail(function(resp) {
                handleFailedAPI(resp, "Error restarting downloads");
            });

        // Update the UI
        $(this).attr("disabled", "disabled");

        // Send event
        ga_track("send", "event", "update", "click-retry-download", "Retry Download");
    });

    // end onload functions
});


function handleFailedAPI(resp, error_text, error_id) {
    if (error_id === undefined) {
        error_id = "id_video_download";  // ID of message element
    }

    switch (resp.status) {
        case 403:
            show_message("error", error_text + ": " + "You are not authorized to complete the request.  Please <a href='{% url login %}' target='_blank'>login</a> as an administrator, then retry.", error_id)
            break;
        default:
            //communicate_api_failure(resp)
            messages = $.parseJSON(resp.responseText);
            if (messages && !("error" in messages)) {
                // this should be an assert--should never happen
                show_message("error", error_text + ": " + "Uninterpretable message received.", error_id);
            } else {
                show_message("error", error_text + ": " + messages["error"], error_id);
            }
            break;
    }
}

/* script functions for doing stuff with the topic tree*/    
function unselectAllNodes() {
    $.each($("#content_tree").dynatree("getSelectedNodes"), function(ind, node) {
        node.select(false);
    });
}

function findSelectedIncompleteVideos() {
    var arr = $("#content_tree").dynatree("getSelectedNodes");
    return $.grep(arr, function(node) { 
        return node.data.addClass != "complete" && node.childList == null;
    });
}

function findSelectedStartedVideos() {
    var arr = $("#content_tree").dynatree("getSelectedNodes");
    return $.grep(arr, function(node) { 
        return node.data.addClass != "unstarted" && node.childList == null;
    });
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

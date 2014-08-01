var VideosView = Backbone.View.extend({
    initialize: function() {
        this.render();
        doRequest(URL_GET_ANNOTATED_TOPIC_TREE, {})
            .success(this.setDynatreeAttrs.bind(this));
        $('#content_tree h4').hide();

        if ($("#download_language_selector option").length > 1) {
            $("#language_choice_titlebar a").attr("onclick", "show_language_selector();");
        }

        $("#download_language_selector").change(function() {
            var lang_code = $("#download_language_selector option:selected")[0].value;
            window.location.href = setGetParam(window.location.href, "lang", lang_code);
        });
    },

    lastKey: null,

    nErrors: 0,

    videosDownloading: false,

    numVideos: null,

    render: function() {
        var template = _.template($('#videos_view_template').html());
        this.$el.html(template);
    },

    events: {
        "click #download-videos": "downloadVideos",
        "click #delete-videos": "displayDeleteVideosDialog",
        "click #cancel-download": "cancelDownload",
        "click #retry-video-download": "retryVideoDownload"
    },

    onDownloadVideosClick: function() {
        this.downloadVideos();
    },

    downloadVideos: function() {
        clear_messages();

        var youtube_ids = this.getSelectedIncompleteMetadata("youtube_id");
        this.numVideos = youtube_ids.length;

        doRequest(URL_START_VIDEO_DOWNLOADS, { youtube_ids: youtube_ids })
            .success(function() {
                updatesStart("videodownload", 5000, this.videoCallbacks);
            })
            .fail(function(resp) {
                $("#download-videos").removeAttr("disabled");
            });
        ga_track("send", "event", "update", "click-download-videos", "Download Videos", youtube_ids.length);

        unselectAllNodes();
        $("#cancel-download").show();
        $("#download-videos").attr("disabled", "disabled");
    },

    getSelectedMetadata: function(vid_type, data_type) {
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
    },

    getSelectedIncompleteMetadata: function(data_type) {
        return this.getSelectedMetadata("incomplete", data_type);
    },

    getSelectedStartedMetadata: function(data_type) {
        return this.getSelectedMetadata("started", data_type);
    },

    videoCallbacks: {
        start: this.videoStartCallback,
        check: this.videoCheckCallback,
        reset: this.videoResetCallback
    },

    videoStartCallback: function(progress_log, resp) {
        this.lastKey = null;
        this.nErrors = 0;
        this.videosDownloading = false;
    },

    videoResetCallback: function() {
        this.lastKey = null;
        this.nErrors = 0;
        this.videosDownloading = false;
    },

    videoCheckCallback: function(progress_log, resp) {
        // When video status is checked
        this.videosDownloading = (progress_log != null) && (progress_log.process_name != null);

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
                    this.setNodeClass(keyCompleted, "complete");
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
                    this.setNodeClass(currentKey, "partial");
                }

            } else if (progress_log.completed) {
                // Completed without 100% done means the videos were cancelled.
                $("#retry-video-download").hide();
                $("#cancel-download").hide();
                $("#download-videos").removeAttr("disabled");
            } else {
                // Everything's good for now!
                this.setNodeClass(currentKey, "partial");
                $("#retry-video-download").hide();
                $("#cancel-download").show();
                $("#download-videos").removeAttr("disabled");
            }

            lastKey = currentKey;

        } else { // check failed.
            $("#download-videos").removeAttr("disabled");
        }
    },

    setNodeClass: function(nodeKey, className) {
        var _this = this;
        this.withNodes(nodeKey, function(node) {
            $(node.span).removeClass("unstarted partial complete").addClass(className);
            node.data.addClass = className;
            if (node.parent) {
                _this.updateNodeClass(node.parent);
            }
        });
    },

    updateNodeClass: function(node) {
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
                this.setNodeClass(node.data.key, "complete");
            } else if (unstarted) {
                this.setNodeClass(node.data.key, "unstarted");
            } else {
                this.setNodeClass(node.data.key, "partial");
            }
        }
    },

    cancelDownload: function() {
        clear_messages();

        doRequest(URL_CANCEL_VIDEO_DOWNLOADS)
            .success(function() {
                // Reset ALL of the progress tracking
                updatesReset();

                // Update the UI
                $("#download-videos").removeAttr("disabled");
                $("#cancel-download").hide();
            });
        ga_track("send", "event", "update", "click-cancel-downloads", "Cancel Downloads");
    },

    displayDeleteVideosDialog: function() {
        clear_messages();

        this.setModalDialogAttrs();
        $("button.ui-dialog-titlebar-close").hide();
        $("#modal_dialog").text(gettext("Deleting the downloaded video(s) will lead to permanent loss of data"));
    },

    retryVideoDownload: function() {
        doRequest(URL_START_VIDEO_DOWNLOADS, {});
        $(this).attr("disabled", "disabled");
        ga_track("send", "event", "update", "click-retry-download", "Retry Download");
    },

    setDynatreeAttrs: function(treeData) {
        var _this = this;
        var attrs = {
            imagePath:"../images/",
            checkbox: true,
            selectMode: 3,
            children: treeData,
            debugLevel: 0,
            onSelect: function(select, node) {

                var newVideoMetadata = _this.getSelectedIncompleteMetadata();
                var oldVideoMetadata = _this.getSelectedStartedMetadata();
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
                with_online_status("server", function(server_is_online) {
                    // We assume the distributed server is offline; if it's online, then we enable buttons that only work with internet.
                    // Best to assume offline, as online check returns much faster than offline check.
                    if(server_is_online){
                        $(".enable-when-server-online").removeAttr("disabled");
                        updatesStart("videodownload", 5000, this.videoCallbacks);
                    } else {
                        show_message("error", gettext("The server does not have internet access; videos cannot be downloaded at this time."));
                    }
                });
            }
        }
        $('#content_tree').dynatree(attrs);
    },

    unselectAllNodes: function() {
        $.each($("#content_tree").dynatree("getSelectedNodes"), function(ind, node) {
            node.select(false);
        });
    },

    withNodes: function(nodeKey, callback, currentNode) {
        var _this = this;
        if (!currentNode) {
            currentNode = $("#content_tree").dynatree("getTree").tnRoot.childList[0];
        }
        $.each(currentNode.childList || [], function(ind, child) {
            if (child.data.key == nodeKey) {
                callback(child);
            }
            _this.withNodes(nodeKey, callback, child);
        });
    },

    setModalDialogAttrs: function() {
        var _this = this;
        var attrs = {
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

                    var youtube_ids = _this.getSelectedStartedMetadata("youtube_id");
                    // Do the request
                    doRequest(URL_DELETE_VIDEOS, {youtube_ids: youtube_ids})
                        .success(function() {
                            $.each(youtube_ids, function(ind, id) {
                                _this.setNodeClass(id, "unstarted");
                            });
                        })
                        .fail(function(resp) {
                            $(".progress-waiting").hide();
                        });
                        // Update the UI
                        _this.unselectAllNodes();

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

        }
        $("#modal_dialog").dialog(attrs);
    }

});

$(function() {
    new VideosView({ el: $("#videos_container") });
});

function show_language_selector() {
    $("#download_language_selector").show();
    $("#language_choice_titlebar a").hide();
}

/* script functions for doing stuff with the topic tree*/

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





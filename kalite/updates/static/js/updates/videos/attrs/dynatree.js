var dynatreeAttrs = {
    imagePath:"../images/",
    checkbox: true,
    selectMode: 3,
    debugLevel: 0,
    onSelect: function(select, node) {

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
                updatesStart("videodownload", 5000, video_callbacks);
            } else {
                show_message("error", gettext("The server does not have internet access; videos cannot be downloaded at this time."));
            }
        });
    }
};

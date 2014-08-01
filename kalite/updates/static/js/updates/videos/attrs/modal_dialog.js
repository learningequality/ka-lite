var modalDialogAttrs = {
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

            var youtube_ids = getSelectedStartedMetadata("youtube_id");
            // Do the request
            doRequest(URL_DELETE_VIDEOS, {youtube_ids: youtube_ids})
                .success(function() {
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

}

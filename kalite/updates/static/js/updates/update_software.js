
// Callback functions

function software_start_callback(progress_log, resp) {
    if (!progress_log) {
        clear_messages();
        show_message("error", resp.status_code + resp.responseText);
    }
}

function software_check_callback(progress_log, resp) {
    // When video status is checked
    if (progress_log) { // check succeeded

        if (progress_log.stage_percent == 1.) {
            // 100% done with the video
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
            window.location.reload();  // Only happens if we were remotely logged out.
            break;
        default:
            show_message("error", "Error downloading videos: " + resp.responseText);
            clearInterval(window.download_subtitle_check_interval);
            break;
        }
    }
}

var software_callbacks = {
    start: software_start_callback,
    check: software_check_callback
};

function version_callback(data) {
    // Check to see if the remote software matches the local software version.
    //   If not, alert the user!
    var current_version = "{{ software_version }}";
    var remote_version = data.version;
    if (! remote_version ) {
        show_message("error", "Remote version information unavailable.", "id_message_update");
    } else if (current_version != remote_version) {
        $("#update_info").show();  // show the related div
        $("#internet_update").show();

        version_info = data["version_info"];

        //alert("update available! " + current_version + " < " + remote_version);
        $("#remote_version").text(remote_version);
        $("#remote_release_date").text(version_info[remote_version].release_date);

        // Update feature list
        //$("#new_features").text("");
        for (version in version_info) {  // loop through all features of all uninstalled versions
            if (! version_info[version]["new_features"]) {
                $("#new_features").append("<li>(None)</li>");
            } else {
                for (fi in version_info[version]["new_features"]) {
                    $("#new_features").append("<li>" + version_info[version]["new_features"][fi] + "</li>");
                }
            }
            if (! version_info[version]["bugs_fixed"]) {
                $("#bugs_fixed").append("<li>(None)</li>");
            } else {
                for (fi in version_info[version]["bugs_fixed"]) {
                    $("#bugs_fixed").append("<li>" + version_info[version]["bugs_fixed"][fi] + "</li>");
                }
            }
        }
    }
}

function download_urls_callback(data) {
    locale = "en";//{{ current_locale }}"
    $("#software_available").append("<option value='" + data[locale].url + "'>" + locale + " (" + data[locale].size + "MB)</option>");
}

$(function() {
    updatesStart("update", 1000, software_callbacks);

    setTimeout(function() {
        get_server_status({path: "{% url get_server_info %}"}, ["online"], function(status){
            // We assume the distributed server is offline.
            //   if it's online, then we show all tools only usable when online.
            //
            // Best to assume offline, as online check returns much faster than offline check.
            if(false && (!status || !status["online"])){
                show_message("error", gettext("Your installation is offline, and therefore cannot access updates."), " id_offline_message");
            } else {
                $("#software_available").removeAttr("disabled");
                $("#download-update-kalite").removeAttr("disabled");
                $("#upload-update-kalite").removeAttr("disabled");
                clear_message("id_offline_message");
            }
        });

    }, 200);

    $("#download-update-kalite").click(function() {
        // Get all videos to download
        //updatesStart("update", 1000, software_callbacks)

        // Start the download and updating process
        doRequest("{% url start_update_kalite %}", { "url": $("#software_available option:selected")[0].value })
            .success(function() {
                updatesStart_callback("update");
            }).fail(function(response) {
                show_message("error", "Error starting update process (" + response.status + "): " + response.responseText);
            });

        // Update the UI to reflect that we're waiting to start
        $("#cancel-update").show();
    });
    // onload
});

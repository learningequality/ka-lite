$(function() {
    // if prefix is empty, gives an absolute (local) url. If prefix, then fully qualified url.
    var url = "http://" + central_server_url +  "/api/i18n/language_packs/available/";
    var request = $.ajax({
        url: url,
        dataType: "jsonp",
    }).success(function(languagePacks) {
	languagePacks.forEach(function(langdata, langindex) {
            var srtcount = langdata["subtitle_count"];
            var langcode = langdata["code"];
            if(langcode === defaultLanguage) {
                $('#language-packs').append('<option value="' + langcode + '" selected>' + langcode + ' (' + srtcount + ')</option>');
            }
            if (srtcount > 0) { // badass over here
                $('#language-packs').append('<option value="' + langcode + '">'+ langcode + ' (' + srtcount +')</option>');
            }
	});
    }).error(function() {
        console.log("404 from central server");
    });
});

// TODO: see where this fits in
$(function() {
    setTimeout(function() {
        get_server_status({path: server_info_url}, ["online"], function(status){
            // We assume the distributed server is offline.
            //   if it's online, then we show all tools only usable when online.
            //
            // Best to assume offline, as online check returns much faster than offline check.
            if(!status || !status["online"]){ // server offline
                show_message("error", "{% trans 'Distributed server is offline; cannot access video nor subtitle updates.' %}", " id_offline_message");
            } else { // server online
                $("#help-info").show();
                $("#download-videos").removeAttr("disabled");
                clear_message("id_offline_message");
            }
        });
    }, 200);
});

//
// Messy UI stuff incoming
//

// when we make a selection on the language pack select box, enable the 'Get Language' Button
// TODO: change so that if they already have a valid selection, activate button anyway
$(function() {
    $("#language-packs").change(function(event) {
        $("#download-subtitles").removeAttr("disabled");
    });
});

// start download process once button is clicked
$(function () {
    $("#download-subtitles").click(function(event) {
        var selected_lang = $("#language-packs").val();
        // tell server to start languagepackdownload job
        doRequest(start_languagepackdownload_url,
                  { lang: selected_lang }).success(function(progress, status, req) {
                      updatesStart("languagepackdownload",
                                  2000, // 2 seconds
                                  languagepack_callbacks);
                      show_message("success",
                                   ["Download for language ", selected_lang, " started."].join(" "),
                                  "id_progress_message");
                  }).error(function(progress, status, req) {
                      show_message("error",
                                   "An error occurred while contacting the server to start the download process: " + [status, req].join(" - "),
                                   "id_error_message");
                  });
    });
});

function languagepack_start_callback() {
    return "stub";
}

function languagepack_check_callback(progress, resp) {
    if (progress.stage_percent == 1.0) { // we're done!
        show_message("success",
                    "Language download complete!",
                    "id_complete_message");
    }
}

var languagepack_callbacks = {
    start: languagepack_start_callback,
    check: languagepack_check_callback
}

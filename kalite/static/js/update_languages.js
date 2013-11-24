// this function doesn't look good. One too many callbacks!
$(function() {
    // basic flow: check with central server what we can install
    // if that's successful, check with local server of what we have installed
    // then dont show languages in dropdown box if already installed
    var url = "http://" + CENTRAL_SERVER_HOST +  "/api/i18n/language_packs/available/";
    var request = $.ajax({
        url: url,
        dataType: "jsonp",
    }).success(function(languagePacks) {
        $.ajax({
            url: installed_languages_url,
            dataType: "json",
        }).success(function(installedlangs) {
            languagePacks.forEach(function(langdata, langindex) {
                var srtcount = langdata["subtitle_count"];
                var percent_translated = langdata["percent_translated"];
                var langcode = langdata["code"];

                // if language already intalled, dont show in dropdown box
                var installed_languages = installedlangs.map(function(elem) { return elem['code']; });
                if ($.inArray(langcode, installed_languages) === -1) { // lang not yet installed
                    if (percent_translated > 0) {
                        $('#language-packs').append('<option value="' + langcode + '">'+ gettext(langdata['name']) + ' (' + langcode + ')</option>');
                    }
                }
            });
        }).error(function(data, status, error) {
            handleFailedAPI(data, [status, error].join(" "), "id_error_message");
        });
    }).error(function(data, status, error) {
        handleFailedAPI(data, [status, error].join(" "), "id_error_message");
    });
});

function display_installed_languages() {
    $.ajax({
        url: installed_languages_url,
        datatype: "json",
    }).success(function(langs) {
        // start from scratch
        $("div.installed-languages").empty();
        langs.forEach(function(lang, index) {
            if (lang['name']) { // nonempty name
                $("div.installed-languages").append("<p>" + gettext(lang['name']) + ' ' + lang['code'] + ' - ' + lang['percent_translated'] + "% " + gettext("Translated") + " - " + lang['subtitle_count'] + " " + gettext("Subtitles available") + "</p>");
            }
        });
    });
}

$(function() {
    setInterval(display_installed_languages, 1500); // query every 1.5 seconds
});

$(display_installed_languages);

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
        doRequest(
            start_languagepackdownload_url,
            { lang: selected_lang }
        ).success(function(progress, status, req) {
            updatesStart(
                "languagepackdownload",
                2000, // 2 seconds
                languagepack_callbacks
            );
            show_message(
                "success",
                ["Download for language ", selected_lang, " started."].join(" "),  // TODO(bcipolli) @ruimalheiro add sprintf and gettext
                "id_progress_message"
            );
        }).error(function(progress, status, req) {
            handleFailedAPI(
                progress,
                gettext("An error occurred while contacting the server to start the download process") + ": " + [status, req].join(" - "),
                "id_error_message"
            );
        });
    });
});

function languagepack_check_callback(progress, resp) {
    if (progress.stage_percent == 1.0) { // we're done!
        show_message(
            "success",
            "Language download complete!",
            "id_complete_message"
        );
    }
}

var languagepack_callbacks = {
    check: languagepack_check_callback
};

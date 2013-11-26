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
                    if (percent_translated > 0 || srtcount > 0) {
                        $('#language-packs').append('<option id="option-' + langcode + '" value="' + langcode + '">'+ gettext(langdata['name']) + ' (' + langcode + '); ' + srtcount + " srts / " + percent_translated + '% translated)</option>');
                    }
                }
            });
        }).error(function(data, status, error) {
            handleFailedAPI(data, [status, error].join(" "), "id_languagepackdownload");
        });
    }).error(function(data, status, error) {
        handleFailedAPI(data, [status, error].join(" "), "id_languagepackdownload");
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
                if (!(lang['code'] === defaultLanguage)) {
                    var link_text = "(<a href='?set_default_language=" + lang["code"] + "'>" + gettext("set as default") + "</a>)";
                } else {
                    var link_text = "(Default)"
                }
                var lang_name = "<b>" + gettext(lang['name']) + "</b> (" + lang['code'] + ")";
                var lang_data = lang['subtitle_count'] + " " + gettext("Subtitles") + " / " + lang['percent_translated'] + "% " + gettext("Translated");
                $("div.installed-languages").append("<p>" + link_text + " " + lang_name + " - " + lang_data + "</p>");
            }
        });
    });
}

$(display_installed_languages);

//
// Messy UI stuff incoming
//

// when we make a selection on the language pack select box, enable the 'Get Language' Button
// TODO: change so that if they already have a valid selection, activate button anyway
$(function() {
    $("#language-packs").change(function(event) {
        $("#get-language-button").removeAttr("disabled");
    });
});

var language_downloading = null;

// start download process once button is clicked
$(function () {
    $("#get-language-button").click(function(event) {
        language_downloading = $("#language-packs").val();
        // tell server to start languagepackdownload job
        doRequest(
            start_languagepackdownload_url,
            { lang: language_downloading }
        ).success(function(progress, status, req) {
            updatesStart(
                "languagepackdownload",
                2000, // 2 seconds
                languagepack_callbacks
            );
            show_message(
                "success",
                ["Download for language ", language_downloading, " started."].join(" "),  // TODO(bcipolli) @ruimalheiro add sprintf and gettext
                "id_languagepackdownload"
            );
        }).error(function(progress, status, req) {
            handleFailedAPI(
                progress,
                gettext("An error occurred while contacting the server to start the download process") + ": " + [status, req].join(" - "),
                "id_languagepackdownload"
            );
        });
    });
});

function languagepack_start_callback(progress, resp) {
}

function languagepack_check_callback(progress, resp) {
}

function languagepack_reset_callback(progress, resp) {
    display_installed_languages();
    $("#option-" + language_downloading).remove();
}
var languagepack_callbacks = {
    start: languagepack_start_callback,
    check: languagepack_check_callback,
    reset: languagepack_reset_callback
};

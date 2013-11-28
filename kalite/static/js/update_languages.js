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
                        $('#language-packs').append(sprintf('<option id="option-%(code)s" value="%(code)s">%(name)s (%(code)s) %(subtitle_count)d srts / %(percent_translated)d %% translated</option>', langdata));
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
                var link_text;
                if (!(lang['code'] === defaultLanguage)) {
                    link_text = sprintf("<a href='?set_default_language=%(lang.code)s'>(%(link_text)s)</a>", { lang: lang, link_text: gettext("Set as default")});
                } else {
                    link_text = "(Default)";
                }
                var lang_name = sprintf("<b>%s</b> (%s)", lang['name'], lang['code']);
                var lang_data = sprintf(gettext("%d Subtitles / %d%% Translated"), lang['subtitle_count'], lang['percent_translated']);
                var lang_description = sprintf("<p>%s %s - %s</p>", link_text, lang_name, lang_data);
                $("div.installed-languages").append(lang_description);
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
                sprintf(gettext("Download for language %s started."), [language_downloading]),
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

function languagepack_reset_callback(progress, resp) {
    display_installed_languages();
    $("#option-" + language_downloading).remove();
}

var languagepack_callbacks = {
    reset: languagepack_reset_callback
};

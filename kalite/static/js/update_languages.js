var installable_languages = null;


// this function doesn't look good. One too many callbacks!
$(function() {
    // basic flow: check with central server what we can install
    // if that's successful, check with local server of what we have installed
    // then dont show languages in dropdown box if already installed
    var url = AVAILABLE_LANGUAGEPACK_URL;
    var request = $.ajax({
        url: url,
        dataType: "jsonp",
    }).success(function(languages) {
        installable_languages = languages;
        display_languages(languages);
    }).error(function(data, status, error) {
        installable_languages = [];
        display_languages([]);
        handleFailedAPI(data, [status, error].join(" "), "id_languagepackdownload");
    });
});

function display_languages(installables) {

    $.ajax({
        url: installed_languages_url,
        datatype: "json",
    }).success(function(installed) {

        //
        // show list of installed languages
        //
        $("div.installed-languages").empty();
        installed.forEach(function(lang, index) {
            if (lang['name']) { // nonempty name
                var link_text;
                if (!(lang['code'] === defaultLanguage)) {
                    link_text = sprintf("<a href='?set_default_language=%(lang.code)s'>(%(link_text)s)</a>", {
                        lang: lang,
                        link_text: gettext("Set as default")
                    });
                } else {
                    link_text = "(Default)";
                }
                var lang_name = sprintf("<b>%(name)s</b> (%(code)s)", lang);
                var lang_data = sprintf(gettext("%(subtitle_count)d Subtitles"), lang);
                var lang_description = sprintf("<div class='lang-link'>%s </div><div class='lang-name'>%s</div><div class='lang-data'> - %s</div>", link_text, lang_name, lang_data);

                // check if there's a new version of the languagepack, if so, add an "UPGRADE NOW!" option
                // NOTE: N^2 algorithm right here, but meh
                var matching_installable = installables.filter(function(installable_lang) { return lang.code === installable_lang.code; })[0];
                if (matching_installable) {
                    var upgradeable = matching_installable.language_pack_version > lang.language_pack_version;
                    if (upgradeable) {
                        //add upgrade link here
                        var subtitle_count_diff = matching_installable.subtitle_count - lang.subtitle_count;
                        lang_description += sprintf(
                            "<div class='upgrade-link'><a href='#' onclick='start_languagepack_download(\"%(lang.code)s\")'>%(upgrade_text)s</a> (+%(srt)d %(srt_text)s)</div>", {
                                lang: lang,
                                upgrade_text: gettext("Upgrade"),
                                srt: subtitle_count_diff,
                                srt_text: gettext("Subtitles")
                        });
                    }
                }
                lang_description += "<div class='clear'></div>";

                $("div.installed-languages").append(lang_description);
            }
        });

        //
        // show list of installable languages in the dropdown box
        //
        installables.forEach(function(langdata, langindex) {
            var srtcount = langdata["subtitle_count"];
            var langcode = langdata["code"];

            // if language already installed, dont show in dropdown box
            var installed_languages = installed.map(function(elem) { return elem['code']; });
            if ($.inArray(langcode, installed_languages) === -1) { // lang not yet installed
                if (srtcount > 0) {
                    $('#language-packs').append(sprintf('<option id="option-%(code)s" value="%(code)s">%(name)s (%(code)s) %(subtitle_count)d srts</option>', langdata));
                }
            }
        });
    });
}

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
        start_languagepack_download(language_downloading);
    });
});

function start_languagepack_download(lang_code) {
    // tell server to start languagepackdownload job
    doRequest(
        start_languagepackdownload_url,
        { lang: lang_code }
    ).success(function(progress, status, req) {
        updatesStart(
            "languagepackdownload",
            2000, // 2 seconds
            languagepack_callbacks
        );
        show_message(
            "success",
            sprintf(gettext("Download for language %s started."), [lang_code]),
            "id_languagepackdownload"
        );
    }).error(function(progress, status, req) {
        handleFailedAPI(
            progress,
            gettext("An error occurred while contacting the server to start the download process") + ": " + [status, req].join(" - "),
            "id_languagepackdownload"
        );
    });
}

function languagepack_reset_callback(progress, resp) {
    $.ajax({url: "/api/languagepacks/refresh", async: false});
    display_languages(installable_languages);
    $("#option-" + language_downloading).remove();
}

var languagepack_callbacks = {
    reset: languagepack_reset_callback
};

// Show the (locally) installed languages, while we wait for the central server
$(function() { display_languages([]); });

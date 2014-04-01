var installable_languages = [];
var installed_languages = [];
var downloading = false;

function get_available_languages() {
    doRequest(AVAILABLE_LANGUAGEPACK_URL, null, {
        cache: false,
        dataType: "jsonp"
    }).success(function(languages) {
        installable_languages = languages;
        display_languages();
    }).fail(function(data, status, error) {
        installable_languages = [];
        display_languages();
    });
}

function get_installed_languages() {
    doRequest(INSTALLED_LANGUAGES_URL, null, {
        cache: false,
        datatype: "json"
    }).success(function(installed) {
        installed_languages = installed;
        display_languages();
    }).fail(function(data, status, error) {
        installed_languages = [];
        display_languages();
    });
}

function display_languages() {
    //this will work regardless of download state; whatever finishes first
    // will run this function first.

    var installables = installable_languages;
    var installed = installed_languages;

    //
    // show list of installed languages
    //
    $("div.installed-languages").empty();
    installed.forEach(function(lang, index) {
        if (lang['name']) { // nonempty name
            var link_text;
            if (lang['code'] !== defaultLanguage) {
                link_text = sprintf("<a href='%(CHANGE_SERVER_LANGUAGE_URL)s'>(%(link_text)s)</a>", {
                    CHANGE_SERVER_LANGUAGE_URL: setGetParam(window.location.href, "set_server_language", lang.code),
                    link_text: gettext("Set as default")
                });
            } else {
                link_text = "(Default)";
            }
            var lang_name = sprintf("<b>%(name)s</b> (%(code)s)", lang);
            var lang_code = lang['code'];
            var lang_data = sprintf(gettext("%(subtitle_count)d Subtitles / %(percent_translated)d%% Translated"), lang);
            var lang_description = sprintf("<div class='lang-link'>%s </div><div class='lang-name'>%s</div><div class='lang-data'> - %s</div>", link_text, lang_name, lang_data);

            if ( lang_code != 'en')
                lang_description += sprintf("<div class='delete-language-button'> <button value='%s' type='button'>%s</button></div>", lang_code, sprintf(gettext('Delete %(name)s'), lang));
            else
                if (lang['subtitle_count'] > 0) {
                    lang_description += sprintf("<div class='delete-language-button'> <button value='%s' type='button'>%s</button></div>", lang_code, sprintf(gettext('Delete %(name)s Subtitles'), lang));
                }

            // check if there's a new version of the languagepack, if so, add an "UPGRADE NOW!" option
            // NOTE: N^2 algorithm right here, but meh
            if (installables.length > 0) {
                var matching_installable = installables.filter(function(installable_lang) { return lang.code === installable_lang.code; });
                if (matching_installable.length != 0) {
                    matching_installable = matching_installable[0];

                    var upgradeable = matching_installable.language_pack_version > lang.language_pack_version;
                    if (upgradeable) {
                        //add upgrade link here
                        var percent_translated_diff = matching_installable.percent_translated - lang.percent_translated;
                        var subtitle_count_diff = matching_installable.subtitle_count - lang.subtitle_count;
                        lang_description += sprintf(
                            "<div class='upgrade-link'><a href='#' onclick='start_languagepack_download(\"%(lang.code)s\")'>%(upgrade_text)s</a> (+%(translated)d%% %(translated_text)s / +%(srt)d %(srt_text)s / %(size)s)</div>", {
                                lang: lang,
                                upgrade_text: gettext("Upgrade"),
                                translated: percent_translated_diff,
                                translated_text: gettext("Translated"),
                                srt: subtitle_count_diff,
                                srt_text: gettext("Subtitles"),
                                size: sprintf("%5.2f MB", matching_installable.zip_size/1.0E6 || 0)
                        });
                    }
                }
            }
            lang_description += "<div class='clear'></div>";

            $("div.installed-languages").append(lang_description);
        }
    });

function delete_languagepack(lang_code) {
    doRequest(DELETE_LANGUAGEPACK_URL, {lang: lang_code})
        .success(function(resp) {
            get_installed_languages();
            display_languages(installables);
        });
}

$(function () {
    $(".delete-language-button").children('button').click(function(event) {
        var lang_code = $(this).val();
        ConfirmDialog(sprintf(gettext("'Are you sure you want to delete language pack '%(lang_code)s'"), {lang_code: lang_code}));

        function ConfirmDialog(message){
            $('<div></div>').appendTo('body')
                .html('<div><h6>'+message+'?</h6></div>')
                .dialog({
                    modal: true, title: gettext('Confirm Delete'), zIndex: 10000, autoOpen: true,
                    width: 'auto', resizable: false,
                    buttons: {
                    Yes: function () {
                        delete_languagepack(lang_code);
                        $(this).remove();
                    },
                    No: function () {
                        $(this).remove();
                    }
                }
            });
        };

        jQuery("button.ui-dialog-titlebar-close").hide();

    });
});

    //
    // show list of installable languages in the dropdown box
    //
    $('#language-packs').find('option').remove();
    $('#language-packs').append("<option value='' selected=''>--</option>");
    installables.forEach(function(langdata, langindex) {
        var srtcount = langdata["subtitle_count"];
        var percent_translated = langdata["percent_translated"];
        var langcode = langdata["code"];

        // if language already installed, dont show in dropdown box
        var installed_languages = installed.map(function(elem) { return elem['code']; });
        if ($.inArray(langcode, installed_languages) === -1) { // lang not yet installed
            if (percent_translated > 0 || srtcount > 0) {
                $('#language-packs').append(sprintf('<option id="option-%(code)s" value="%(code)s">%(name)s (%(code)s)</option>', langdata));
            }
        }
    });

    if (installables.length > 0) {
        $('#language-packs').change(); // trigger the 'Get Language' Button update
    }
}

//
// Messy UI stuff incoming
//


function start_languagepack_download(lang_code) {
    clear_messages();  // get rid of any lingering messages before starting download
    $("#get-language-button").prop("disabled", true);
    downloading = true;
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
    });
}

// when we make a selection on the language pack select box, enable the 'Get Language' Button
$(function() {
    $("#language-packs").change(function(event) {
        var lang_code = $("#language-packs").val();
        var found = false;

        var matching_installable = installable_languages.filter(function(installable_lang) { return lang_code === installable_lang.code; });
        var found = (matching_installable.length != 0);

        if( !downloading){
                $("#get-language-button").prop("disabled", !found);
        }
        if (found) {
            var langdata = matching_installable[0];
            // For each of the following, || 0 will return 0 if the quantity is undefined.
            $("#lp-num-srts").text(sprintf("%d", langdata["subtitle_count"] || 0));
            $("#lp-pct-trans").text(sprintf("%5.2f%%", langdata["percent_translated"] || 0));
            $("#lp-down-size").text(sprintf("%5.2f MB", langdata["zip_size"]/1.0E6 || 0));
            $("#lp-disk-size").text(sprintf("%5.2f MB", langdata["package_size"]/1.0E6 || 0));
            $("#lp-num-exers").text(sprintf("%d", langdata["num_exercises"] || 0));
        }
        $("#langpack-details").toggle(found);
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


function languagepack_reset_callback(progress, resp) {
    // This will get the latest list of installed languages, and refresh the display.
    get_installed_languages();
    downloading = false;
}

var languagepack_callbacks = {
    reset: languagepack_reset_callback
};


$(function() {
    // basic flow: check with central server what we can install
    // if that's successful, check with local server of what we have installed
    // then dont show languages in dropdown box if already installed
    get_available_languages();
    get_installed_languages();
});

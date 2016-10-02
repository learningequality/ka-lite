var api = require("utils/api");
var $ = require("base/jQuery");
var messages = require("utils/messages");
var base = require("updates/base");
var connectivity = require("utils/connectivity");
var sprintf = require("sprintf-js").sprintf;

var installable_languages = [];
var installed_languages = [];
var downloading = false;

function version_comparison(v1, v2) {
    /*
    compare two version strings and return 1 if the first is higher than the second,
    -1 if the first is lower than the second, and 0 if they are equal.

    :params v1, v2: Version strings expected format is either "N.N.N" or "N.N", where N is a positive integer.
    If both strings have the same format, they're compared using a lexical order.
    If one string is shorter than the other, then the other is truncated and then compared using lexical order.
    */
    var v1parts = v1.split('.'), v2parts = v2.split('.');
    var minLen = Math.min(v1parts.length, v2parts.length);
    var part1, part2;
    for(var i = 0; i < minLen; i++) {
        part1 = parseInt(v1parts[i], 10) || 0;
        part2 = parseInt(v2parts[i], 10) || 0;
        if (part1 > part2) return 1;
        if (part2 > part1) return -1;
    }
    return 0;
}

function get_available_languages() {
    return api.doRequest(window.sessionModel.get("AVAILABLE_LANGUAGEPACK_URL"), null, {
        cache: false
    }).success(function(languages) {
        installable_languages = languages;
        display_languages();
    }).fail(function(data, status, error) {
        installable_languages = [];
        display_languages();
    });
}

function get_installed_languages() {
    return api.doRequest(window.Urls.installed_language_packs(), null, {
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
    $("table.installed-languages").empty();
    installed.forEach(function(lang, index) {
        if (lang['name']) { // nonempty name
            var link_text;
            if (lang['code'] !== window.sessionModel.get("DEFAULT_LANGUAGE")) {
                link_text = sprintf("<span><a onclick='set_server_language(\"%(lang)s\")' class='set_server_language' value='%(lang)s' href='#'><button type='button' class='btn btn-default btn-sm'>%(link_text)s</button></a></span>", {
                    lang: lang.code,
                    link_text: gettext("Set as default")
                });
            } else {
                link_text = gettext("Default");
            }
            lang["subtitles"] = gettext("Subtitles");
            lang["translated"] = gettext("Translated");
            var lang_name_data = sprintf("<b>%(name)s</b><br>%(subtitle_count)d %(subtitles)s <br> %(percent_translated)d%% %(translated)s", lang);
            var lang_code = lang['code'];

            var lang_description = sprintf("<tr><td class='lang-name'>%s</td><td class='lang-link'>%s </td>", lang_name_data, link_text);



            // check if there's a new version of the languagepack, if so, add an "UPGRADE NOW!" option
            // NOTE: N^2 algorithm right here, but meh
            if (installables.length > 0) {
                var matching_installable = installables.filter(function(installable_lang) { return lang.code === installable_lang.code; });
                if (matching_installable.length !== 0) {
                    matching_installable = matching_installable[0];

                    var software_version_comparison = version_comparison(matching_installable.software_version, lang.software_version);
                    var upgradeable =
                        (software_version_comparison == 1) || // language pack is for a new KA Lite version
                        (software_version_comparison === 0 && (matching_installable.language_pack_version > lang.language_pack_version)); // same KA Lite version, new lang pack
                    if (upgradeable) {
                        //add upgrade link here
                        var percent_translated_diff = matching_installable.percent_translated - lang.percent_translated;
                        var subtitle_count_diff = matching_installable.subtitle_count - lang.subtitle_count;
                        lang_description += sprintf(
                            "<td class='upgrade-link'><a href='#' onclick='start_languagepack_download(\"%(lang.code)s\")'>%(upgrade_text)s</a> <br> +%(translated)d%% %(translated_text)s <br> +%(srt)d %(srt_text)s / %(size)s</td>", {
                                lang: lang,
                                upgrade_text: gettext("<button type='button' class='btn btn-info'>Upgrade</button>"),
                                translated: percent_translated_diff,
                                translated_text: gettext("Translated"),
                                srt: subtitle_count_diff,
                                srt_text: gettext("Subtitles"),
                                size: sprintf("%5.2f MB", matching_installable.zip_size/1.0E6 || 0)
                        });
                    }
                    else {
                        lang_description += sprintf("<td class='upgrade-link'>%(up_to_date_text)s</td>", {
                            up_to_date_text: gettext("Up to Date")
                        });
                    }
                }
            }

            lang_description += sprintf("<td class='delete-language-button'> <button class='btn btn-danger' value='%s' type='button'>%s</button></td>", lang_code, gettext('Delete'));

            lang_description += "<td class='clear'></td></tr>";

            $("table.installed-languages").append(lang_description);
        }
    });

function delete_languagepack(lang_code) {
    api.doRequest(window.Urls.delete_language_pack(), {lang: lang_code})
        .success(function(resp) {
            get_installed_languages();
            display_languages(installables);
        });
}

$(function () {
    $(".delete-language-button").children('button').click(function(event) {
        var lang_code = $(this).val();
        ConfirmDialog(sprintf(gettext("Are you sure you want to delete language pack '%(lang_code)s'"), {lang_code: lang_code}));

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
        }

        $("button.ui-dialog-titlebar-close").hide();

    });
});

function populate_installable_lang_pack_dd(){
    //
    // show list of installable languages in the dropdown box
    //
    var lp_ul = $('#language-packs-ul');
    lp_ul.find('li').remove();

    installables.forEach(function(langdata, langindex) {
        var srtcount = langdata["subtitle_count"];
        var percent_translated = langdata["percent_translated"];
        var langcode = langdata["code"];
        var langbeta = langdata["beta"];

        // if language already installed, dont show in dropdown box
        var installed_languages = installed.map(function(elem) { return elem['code']; });
        if ($.inArray(langcode, installed_languages) === -1) { // lang not yet installed
            if (percent_translated > 0 || srtcount > 0) {
                var li = $('<li></li>').attr('id', sprintf('option-%(code)s', langdata))
                                       .attr('role', 'presentation')
                                       .attr('value', sprintf('%(code)s', langdata))
                                       .click( {caller_value: sprintf('%(code)s', langdata)}, select_lang_pack )
                                       .append( $('<a></a>').attr('role','menu-item')
                                                            .html(sprintf('%(name)s', langdata))
                                       );
                if(langbeta && $("#beta-checkbox").is(':checked')){
                    li.find('a')
                      .append( $('<span></span>').text(gettext('beta'))
                                                 .attr('class', 'beta-text')
                      );
                    lp_ul.append(li);
                }else if(!langbeta){
                    lp_ul.append(li);
                }
            }
        }
    });
}

populate_installable_lang_pack_dd();

$('#beta-checkbox').click(function() {
     populate_installable_lang_pack_dd();
});

}

//
// Messy UI stuff incoming
//

var languagepack_callbacks = {
    reset: languagepack_reset_callback,
    completed: languagepack_complete_callback
};

function start_languagepack_download(lang_code) {
    messages.clear_messages();  // get rid of any lingering messages before starting download
    $("#get-language-button").prop("disabled", true);
    downloading = true;
    // tell server to start retrievecontentpack job
    api.doRequest(
        Urls.start_languagepack_download(),
        { lang: lang_code }
    ).success(function(progress, status, req) {
        base.updatesStart(
            "retrievecontentpack",
            2000, // 2 seconds
            languagepack_callbacks
        );
    });
}

window.start_languagepack_download = start_languagepack_download;

// when we make a selection on the language pack select box, enable the 'Get Language' Button
function select_lang_pack( event ) {
    var lang_code = event.data.caller_value;
    var found = false;
    var li = $(sprintf('#option-%s', lang_code));
    $('#language-packs-selection').html( li.html() )
                                  .append( $('<span></span>').attr('class', 'caret') );
    $('#language-packs').attr('value', li.attr('value'));

    var matching_installable = installable_languages.filter(function(installable_lang) { return lang_code === installable_lang.code; });
    found = (matching_installable.length !== 0);

    if(!downloading){
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
}

var language_downloading = null;

// start download process once button is clicked
$(function () {
    $("#get-language-button").click(function(event) {
        language_downloading = $("#language-packs").attr('value');
        start_languagepack_download(language_downloading);
    });
});

function languagepack_reset_callback(progress, resp) {
    // This will get the latest list of installed languages, and refresh the display.
    get_installed_languages();
    downloading = false;
}

function languagepack_complete_callback(progress_log) {
    // This is a no-op for now. Used to remind the user to restart the server, but that's not necessary anymore.
}

function set_server_language(lang) {
    api.doRequest(Urls.set_default_language(),
              {lang: lang}
             ).success(function() {
                 window.location.reload();
             });
}

window.set_server_language = set_server_language;

function update_server_status() {
    connectivity.with_online_status("server", function(server_is_online) {
        // We assume the distributed server is offline; if it's online, then we enable buttons that only work with internet.
        // Best to assume offline, as online check returns much faster than offline check.
        if(server_is_online){
            base.updatesStart("retrievecontentpack", 1000, languagepack_callbacks);
        } else {
            messages.clear_messages();
            messages.show_message("error", gettext("Could not connect to the central server; language packs cannot be downloaded at this time."));
        }
    });
}

$(function() {
    // basic flow: check with central server what we can install
    // if that's successful, check with local server of what we have installed
    // then dont show languages in dropdown box if already installed
    get_available_languages()
        .success( update_server_status )
        .fail( update_server_status );
    get_installed_languages()
        .success( update_server_status )
        .fail( update_server_status );

});

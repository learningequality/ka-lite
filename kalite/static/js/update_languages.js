var defaultLanguage;
function setup(server_info_url, central_server_url, default_language) {
    defaultLanguage = default_language;
    regularly_check_for_server(server_info_url);
    fetch_language_packs(central_server_url);
}

function fetch_language_packs(central_server_url) {
    // if prefix is empty, gives an absolute (local) url. If prefix, then fully qualified url.
    var url = "http://" + central_server_url +  "/api/i18n/language_packs/available/";
    var request = $.ajax({
        url: url,
        dataType: "jsonp",
    }).success(show_language_packs).error(function() {
    });
}

function regularly_check_for_server(server_info_url) {

    setTimeout(function() {
        get_server_status({path: server_info_url}, ["online"], function(status){
            // We assume the distributed server is offline.
            //   if it's online, then we show all tools only usable when online.
            //
            // Best to assume offline, as online check returns much faster than offline check.
            if(!status || !status["online"]){ // server offline
                show_message("error", "{% trans 'Distributed server is offline; cannot access video nor subtitle updates.' %}", " id_offline_message")
            } else { // server online
                $("#help-info").show();
                $("#download-videos").removeAttr("disabled");
                clear_message("id_offline_message");
            }
        });
    }, 200);
    // onload
}

function show_language_packs(languagePacks) {
    // gets the current number of subs per language
    $.each(languagePacks, function(langName, langData) {
        var langCode = langData["code"];
        var srtCount = langData["count"];
        // adds it to update page
        if(srtCount > 0){
            if(langCode === defaultLanguage) {
                $('#language-packs').append('<option value="' + langCode + '" selected>' + langName + ' (' + srtCount +' {% trans "total" %})</option>')
            } else {
                $('#language-packs').append('<option value="' + langCode + '">'+ langName + ' (' + srtCount +')</option>')
            }
        }
    });
}

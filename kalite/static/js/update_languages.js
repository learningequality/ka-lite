var defaultLanguage;
function setup(server_info_url, default_language) {
    defaultLanguage = default_language;
    regularly_check_for_server(server_info_url);
}

function regularly_check_for_server(server_info_url) {

    setTimeout(function() {
        get_server_status({path: server_info_url}, ["online"], function(status){
            // We assume the distributed server is offline.
            //   if it's online, then we show all tools only usable when online.
            //
            // Best to assume offline, as online check returns much faster than offline check.
            if(!status || !status["online"]){ // server is offline
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
    var defaultLanguage = defaultLanguage;
    $.each(languagePacks, function(langName, langData) {
        var langCode = langData["code"];
        var srtCount = langData["count"];
        // adds it to update page
        if(srtCount > 0){
            if(langCode === defaultLanguage) {
                $('#language').append('<option value="' + langCode + '" selected>' + langName + ' (' + srtCount +' {% trans "total" %})</option>')
            } else {
                $('#language').append('<option value="' + langCode + '">'+ langName + ' (' + srtCount +')</option>')
            }
        }
    });
}

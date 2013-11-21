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
    // onload
});

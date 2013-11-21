var defaultLanguage;
function setup(server_info_url, central_server_url, default_language) {
    defaultLanguage = default_language;
    regularly_check_for_server(server_info_url);
    fetch_language_packs(central_server_url);
}

// because concatenating strings is not fun, here's proper string interpolation
String.prototype.supplant = function (o) {
    return this.replace(/{([^{}]*)}/g,
        function (a, b) {
            var r = o[b];
            return typeof r === 'string' || typeof r === 'number' ? r : a;
        }
    );
};

function fetch_language_packs(central_server_url) {
    // if prefix is empty, gives an absolute (local) url. If prefix, then fully qualified url.
    var url = "http://" + central_server_url +  "/api/i18n/language_packs/available/";
    var request = $.ajax({
        url: url,
        dataType: "jsonp",
    }).success(function(languagePacks) {
	languagePacks.forEach(function(langdata, langindex) {
            var srtcount = langdata["subtitle_count"];
            var langcode = langdata["code"];
            console.log(langcode + " has " + srtcount);
            if (srtcount > 0) { // badass over here
                console.log("Appending #{language}".supplant({language: langcode}));
                if(langcode === defaultLanguage) {
                    $('#language-packs').append('<option value="' + langcode + '" selected>' + langcode + ' (' + srtcount + gettext('total') + ')</option>');
                } else {
                    $('#language-packs').append('<option value="' + langcode + '">'+ langcode + ' (' + srtcount +')</option>');
                }
            }
	});
    }).error(function() {
        console.log("404 from central server");
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

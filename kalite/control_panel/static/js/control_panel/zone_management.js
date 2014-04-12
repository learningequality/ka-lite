$(function () {
    $("#force-sync").click(function(){
        force_sync();
    })

    /*
    $(".zone-delete-link").click(function() {
        if (confirm(sprintf(gettext("Are you sure you want to delete sharing network '%(network_name)s'?"), {network_name: event.target.getAttribute("value")}))) {
            doRequest(DELETE_ZONE_URL);
        }
    });
    */

    $(".facility-delete-link").click(function(event) {
        if (confirm(gettext("Are you sure you want to delete this facility?"))) {
            var delete_facility_url = event.target.getAttribute("value");
            doRequest(delete_facility_url)
                .success(function() {
                    window.location.reload();
                });
        }
    });
})

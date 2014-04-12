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
})

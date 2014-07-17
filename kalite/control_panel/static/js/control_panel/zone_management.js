$(function () {
    $("#force-sync").click(function(){
        force_sync();
    });

    $(".facility-delete-link").click(function(event) {
        if (confirm(gettext("Are you sure you want to delete this facility?"))) {
            var delete_facility_url = event.target.parentNode.getAttribute("value");
            doRequest(delete_facility_url)
                .success(function() {
                    window.location.reload();
                });
        }
    });
});

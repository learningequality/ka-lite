$(function () {
    $("#form_data").hide()

    $("#upload_form").submit(function() {
    // Disable until we get to this stage of the IDOC deployment.
    /*
        // First press: show file entry
        if ($('#form_data').filter(":visible").length==0) {
            $('#form_data').show();
            return false;
        }
        // Second press: submit form (default)
    */
        return false;
    });

    $("#force-sync").click(function(){
        force_sync();
    })

    $(".zone-delete-link").click(function() {
        if (confirm(sprintf(gettext("Are you sure you want to delete sharing network '%(network_name)s'?"), {network_name: event.target.getAttribute("value")}))) {
            window.location.href = DELETE_ZONE_URL;
        }
    });
})

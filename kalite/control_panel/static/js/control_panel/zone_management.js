$(function () {
    $("#force-sync").click(function(){
        force_sync();
    });

    $(".facility-delete-link").click(function(event) {
        var facilityName = $.trim($(this).parent().prevAll().find('a.facility-name').text());
        var confirmDelete = prompt(sprintf(gettext("Are you sure you want to delete '%s'? You will lose all associated student, group, and teacher accounts. If you are sure, type the name of the facility into the box below and press OK."), facilityName));
        
        if (confirmDelete === null) {
            return false; // cancel
        }
        else if (confirmDelete === facilityName) {
            var delete_facility_url = event.target.parentNode.getAttribute("value");
            doRequest(delete_facility_url)
                .success(function() {
                    window.location.reload();
                });
        } else {
            show_message("warning", gettext("The facility has not been deleted. Did you spell the facility name correctly?"));
        }
    });
})

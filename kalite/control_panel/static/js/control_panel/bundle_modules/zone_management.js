var $ = require("base/jQuery");
var force_sync = require("utils/force_sync");
var api = require("utils/api");
var messages = require("utils/messages");
var sprintf = require("sprintf-js").sprintf;

$(function () {
    $("#force-sync").click(function(ev){
        ev.preventDefault();
        force_sync(window.ZONE_ID, window.DEVICE_ID);
    });

    $(".facility-delete-link").click(function(event) {
        var facilityName = $.trim($(this).parent().prevAll().find('a.facility-name').text());
        var confirmDelete = prompt(sprintf(gettext("Are you sure you want to delete '%s'? You will lose all associated learner, group, and coach accounts. If you are sure, type the name of the facility into the box below and press OK."), facilityName));
        
        if (confirmDelete === null) {
            return false; // cancel
        }
        else if (confirmDelete === facilityName) {
            var delete_facility_url = event.target.getAttribute("value");
            var data = {facility_id: null};
            // MUST: provide the data argument to make this a POST request
            api.doRequest(delete_facility_url, data)
                .success(function() {
                    window.location.reload();
                });
        } else {
            messages.show_message("warning", gettext("The facility has not been deleted. Did you spell the facility name correctly?"));
        }
    });
});

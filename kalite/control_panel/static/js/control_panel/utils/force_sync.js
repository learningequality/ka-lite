var api = require("utils/api");
var sprintf = require("sprintf-js").sprintf;
var messages = require("utils/messages");

module.exports = function force_sync(zone_id, device_id) {
    // Simple function that calls the API endpoint to force a data sync,
    //   then shows a message for success/failure
    api.doRequest(window.Urls.api_force_sync())
        .success(function() {
            var msg = gettext("Successfully launched data syncing job.") + " ";
            msg += sprintf(gettext("After syncing completes, visit the <a href='%(devman_url)s'>device management page</a> to view results."), {
                devman_url: Urls.device_management(zone_id, device_id)
            });
            messages.show_message("success", msg);
        });
};
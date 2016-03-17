var $ = require("../base/jQuery");
var content_rec_views = require("../contentrec/views");
var user = require("../user/views");

require("../../../css/distributed/homepage.less");

$(function() {
    if (ds.distributed.front_page_welcome_message) {
        show_message("success", ds.distributed.front_page_welcome_message);
    }
    var content_rec_load = function() {
        if (window.statusModel.is_student() && !window.hpwrapper) {
            window.hpwrapper = new content_rec_views.HomepageWrapper({
                el:"#content-area"
            });
        }
    };
    window.statusModel.listenTo(window.statusModel, "change", content_rec_load);

    window.statusModel.listenTo(window.statusModel, "change:has_superuser", function () {
        if (!window.statusModel.get("has_superuser")) { // "has_superuser" is true if an admin user exists.
            window.super_user_create_modal = new user.SuperUserCreateModalView();
        } else if ( typeof window.super_user_create_modal !== "undefined" ) {
            // super_user_create_modal might not be properly hidden yet if remove too fast 
            setTimeout(function () {window.super_user_create_modal.remove();}, 2000);
        }
    });
});
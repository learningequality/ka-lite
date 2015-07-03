var $ = require("../base/jQuery");
var content_rec_views = require("../contentrec/views");


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
    }
    window.statusModel.listenTo(window.statusModel, "change", content_rec_load);
});
var BaseView = require("base/baseview");

var ContentBaseView = BaseView.extend({
    initialize: function(options) {

        _.bindAll(this, "activate", "deactivate", "set_time_spent", "set_last_time", "set_progress", "update_progress", "content_specific_progress", "close");

        this.active = false;

        this.possible_points = ds.distributed.turn_off_points_for_videos ? 0 : ds.distributed.points_per_video;

        this.REQUIRED_PERCENT_FOR_FULL_POINTS = 0.95;

        this.data_model = options.data_model;
        this.log_model = options.log_model;
        this.listenTo(window.channel_router, "navigation", this.close);
    },

    activate: function () {
        this.active = true;
        this.set_last_time();
    },

    deactivate: function () {
        this.active = false;
    },

    set_time_spent: function() {
        var time_now = new Date().getTime();

        var time_engaged = Math.max(0, time_now - this.last_time);
        time_engaged = (isNaN(time_engaged) ? 0 : time_engaged)/1000;

        this.log_model.set({
            time_spent: this.log_model.get("time_spent") + time_engaged
        });

        this.last_time = time_now;
    },

    set_last_time: function() {
        this.last_time = new Date().getTime();
    },

    set_progress: function(progress) {
        if (progress - (this.log_model.get("completion_counter") || 0) > this.REQUIRED_PERCENT_FOR_FULL_POINTS) {
            this.log_model.set_complete();
            progress = 1;
        }
        this.log_model.set({
            points: Math.min(this.possible_points, Math.floor(this.possible_points * progress)),
            progress: progress
        });

    },

    update_progress: function() {
        if (!window.statusModel.get("is_logged_in") ) {
            return;
        }

        if (window.statusModel.get("is_django_user")) {
            return;
        }

        if (!this.active) {
            return;
        }

        this.set_time_spent();

        var progress = this.content_specific_progress.apply(this, arguments);

        this.set_progress(progress);
        this.log_model.save();
    },

    content_specific_progress: function() {
        return;
    },

    close: function() {
        if (window.statusModel.get("is_logged_in") && !window.statusModel.get("is_admin") ) {
            this.log_model.saveNow();
        }
        this.remove();
    }
});

module.exports = ContentBaseView;
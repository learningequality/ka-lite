// Handles the data export functionality of the control panel

// Collections

// Models 

// Views 
var StudentProgressView = Backbone.View.extend({
    // The containing view
    template: HB.template('student_progress/student_progress_container'),

    initialize: function() {
        // this.playlist_view = new PlaylistProgressView();

        this.render();
    },

    render: function() {
        console.log("Rendering the empty div!")
        this.$el.html(this.template());
    }
})

var NarrativeModel = Backbone.Model.extend({
    sync: function(method, model, options) {
        if (method === "read") {

            // Set "intro" attr. of the model, and call success callback.
            this.set("intro", [{"a#manage.admin-only": [{"step": 1}, {"text": "Welcome! This is the landing page for admins. If at any point you would like to navigate back to this page, click on this tab!"}]}, {"li.facility": [{"step": 2}, {"text": "Clicking on this tab will show you a quick overview of all facilities and devices"}]}, {"a.create-facility": [{"step": 3}, {"text": "To add new facilities, click here..."}]}, {"div.row:nth-child(3)": [{"step": 4}, {"text": "Information on your device status will be shown here"}]}, {"#not-registered": [{"step": 5}, {"text": "If you decide to register your device to our central club, click here!"}]}, {"unattached": [{"step": 6}, {"text": "Questions about anything on the page? Be sure to consult the user manual or FAQ for more detailed walk throughs!"}]}]});
            options.success();
        }
    }
});
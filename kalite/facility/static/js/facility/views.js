var BaseView = require("base/baseview");
var Handlebars = require("base/handlebars");

var UpdateVersionView = BaseView.extend({
    template: require("./hbtemplates/UpdateVersion.handlebars"),

    initialize: function() {
        _.bindAll(this, "render");
    },

    render: function() {
        this.$el.html(this.template());
        $("#content-container").append(this.el);
    }

});

var CreateDeviceAndUserView = BaseView.extend({
    template: require("./hbtemplates/CreateDeviceAndUser.handlebars"),

    initialize: function(options) {
        console.log("create device and users view initialized");
        _.bindAll(this, "render");
        this.csrf_token = options.data.split("csrftoken=");
        this.csrf_token = this.csrf_token[1];

/**
        this.model.username = "";
        this.model.password = "";
        this.model.password_confirm = "";
        this.model.device_desc = "";
        this.model.device_name = "";
**/
    },

    render: function(){
        this.$el.html(this.template());
        $('#content-container').append(this.el);    //is there a way to do this
                                                    //while referencing the config
                                                    //settings view?? 

        $('#create-user-form').append('<input type="hidden" ' +
                                      'name="csrfmiddlewaretoken" ' + 
                                      'value="' + this.csrf_token + '">');
    },

    events: {
        'change .user': 'on_user_attributes_change',
    },

    on_user_attributes_change: function() {
        console.log("CreateDeviceAndUserView: on_user_attributes_change");

        var username = $('input[name="username"]').val().length;
        var pw = $('input[name="password"]').val().length;
        var pw_confirm = $('input[name="password_confirm"]').val().length;

        // display device configuration form inputs if superuser fields filled
        if (username > 0 && pw > 0 && pw_confirm > 0) {
            $("#device-config").show();
        }
        //do we even need to set attributes for this model VV ?
        /**
        var form = $(this.el).find('#create-user-form');
        console.log("this is form:");
        console.log(form);

        // if all attributes are okay, set model, then show device prompts
        this.model.set({
            username: form.find('#username').val(),
            password: form.find('#password').val(),
            //device_name = form.find('#username').val();
            //device_desc = form.find('#username').val();
        }); **/
    },

    // pressing the "next" button should trigger on_complete
    on_complete: function() {
        console.log("CreateDeviceAndUserView: on_complete: make post request" +
            "to endpoint which creates the user and sets device info.");
    }
}); 

var ConfigSettingsView = BaseView.extend({
    el: '#content-container',

    initialize: function(options) {
        _.bindAll(this, "render");

        this.csrf_token = options.data.split("csrftoken=");
        this.csrf_token = this.csrf_token[1];

        // display option to update if available -- need to work on this, after
        if (need_update === "True") {
            console.log("you need update");
            this.updateVersionView = this.add_subview(UpdateVersionView);
            this.updateVersionView.render();
        }

        this.createDeviceAndUserView = this.add_subview(CreateDeviceAndUserView, options);
        this.dlAssessProgView = this.add_subview(DownloadAssessmentProgressView);
        
        // add listener for subview when complete
        this.render();
    },

    tester: function() {
        console.log("create device and user view was clicked, so this fires");
    },

    render: function() {
        // render the fist subview -- CreateDeviceAndUser
        //this.$el.append(this.createDeviceAndUserView.$el);

        this.createDeviceAndUserView.render();
    }
}); 


var DownloadAssessmentProgressView = BaseView.extend({
    template: require("./hbtemplates/test.handlebars"),

    initialize: function() {
        console.log("download assessment progress view initialized");
        _.bindAll(this, "render");
        //this.render();
    },

    events: {
        "click": function() {
            console.log("I was clicked, model is:" + this.model.urlRoot);
            $.ajax({
                url: "/securesync/api/dl_progress/",
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify({"progress": 0})
            });
            console.log("Fetching model after posting");
            this.model.fetch({
                success: function(model, response, options){
                    console.log("Fetch model success.");
                    console.log(response);
                    console.log("model fetched:");
                    console.log(model);
                },
                error: function(model, response, options){
                    console.log("UNABLE TO FETCH MODEL.");
                }
            });
            //fetch progress model every x seconds to update display
            /**setInterval(function() {
                console.log("fetching model...");
                this.model.fetch({
                    success: function(model, response, options){
                        console.log("Fetch model success.");
                    },
                    error: function(model, response, options){
                        console.log("UNABLE TO FETCH MODEL.");
                    }
                });
            }, 1000);
            **/ 
        }
    },

    render: function() {
        this.$el.html(this.template());
        $("#content-container").append(this.el);
    }
});


module.exports = {
    ConfigSettingsView: ConfigSettingsView,
    DownloadAssessmentProgressView: DownloadAssessmentProgressView,
    CreateDeviceAndUserView: CreateDeviceAndUserView
};

var BaseView = require("base/baseview");
var Handlebars = require("base/handlebars");
var DownloadAssessmentProgressModel = require("./models").DownloadAssessmentProgressModel;

require("../../css/facility/config_form.less");


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


var ConfigSettingsView = BaseView.extend({
    el: '#content-container',

    initialize: function(options) {
        _.bindAll(this, "render");

        // display option to update if available -- need to work on this, after
        if (need_update === "True") {
            console.log("you need update");
            this.updateVersionView = this.add_subview(UpdateVersionView);
            this.updateVersionView.render();
        }

        this.createDeviceAndUserView = this.add_subview(CreateDeviceAndUserView, options);

        var downloadProgressModel = new DownloadAssessmentProgressModel();
        this.dlAssessProgView = this.add_subview(DownloadAssessmentProgressView, 
                                                    { model: downloadProgressModel });
        
        // add listener for subview when complete
        this.listenTo(this.createDeviceAndUserView, 'complete', this.render);

        this.render(options);
    },

    render: function(options) {
        if (options){
            this.createDeviceAndUserView.render(options);
        }
        else {
            console.log("else render dl assess view");
            this.dlAssessProgView.render();
        }
    }
}); 


var CreateDeviceAndUserView = BaseView.extend({
    template: require("./hbtemplates/CreateDeviceAndUser.handlebars"),

    initialize: function(options) {
        _.bindAll(this, "render");

        this.options = options;
        this.csrf_token = options.csrftoken;
    },

    render: function(options){
        this.$el.html(this.template(options));
        $('#content-container').append(this.el);    //is there a way to do this
                                                    //while referencing the config
                                                    //settings view's "el"?? 

        $('#config-form').append('<input type="hidden" ' +
                                      'name="csrfmiddlewaretoken" ' + 
                                      'value="' + this.csrf_token + '">');
    },

    events: {
        'click #load-device-form': 'on_user_fields_submit',
        'click #submit': 'submit_form'
    },

    on_user_fields_submit: function() {
        var username = $('input[name="username"]').val();
        var pw = $('input[name="password"]').val();
        var pw_confirm = $('input[name="pw_confirm"]').val();

        // display device configuration form inputs once superuser fields filled,
        // and only if the password fields match
        if (username.length > 0 && pw.length > 0 && pw_confirm.length > 0) {
            if (pw !== pw_confirm) {
                $("#pw_error").show();
            }
            else {
                $("#pw_error").hide();
                $("#load-device-form").hide();
                $(".device-form").show();
            }
        }
    },

    submit_form: function(e) {

        // check if all form fields valid first before submitting form
        this.on_user_fields_submit();

        // do not submit form if passwords don't match
        if ( $("#pw_error").is(":visible") ) {
            return;
        }

        var options = {
            "username": $('input[name="username"]').val(),
            "pw": $('input[name="password"]').val(),
            "pw_confirm": $('input[name="pw_confirm"]').val(),
            "hostname":  $('input[name="hostname"]').val(),
            "host_descrip": $('input[name="decsription"]').val(),
        };

        var that = this;
        $.ajax({
            type: "POST",
            url: "/facility/config/",
            data: options,

            // hide form and signal to parent view this part is complete
            success: function(data){
                $('#config-form').empty();
                that.trigger("complete");
            }
        }); 

        // prevents the page from refreshing after POST
        e.preventDefault();
    }
}); 


var DownloadAssessmentProgressView = BaseView.extend({
    template: require("./hbtemplates/DownloadAssessment.handlebars"),

    initialize: function() {
        _.bindAll(this, "render");
        //this.render();
    },
    
    render: function() {
        this.$el.html(this.template());
        $("#content-container").append(this.el);
    },

    events: {
        'click #download': 'download' 
    },

    download: function() {
        console.log("download assessment button clicked");
        console.log(this.model.urlRoot);
        
        $.ajax({
            url: this.model.urlRoot,
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({"progress": 0})
        });
        console.log("Fetching model after posting");
        /*
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
});


module.exports = {
    ConfigSettingsView: ConfigSettingsView,
    DownloadAssessmentProgressView: DownloadAssessmentProgressView,
    CreateDeviceAndUserView: CreateDeviceAndUserView
};

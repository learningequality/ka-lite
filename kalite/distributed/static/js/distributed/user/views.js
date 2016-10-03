var ENTER_KEY = 13;

var Backbone = require("../base/backbone");
var $ = require("../base/jQuery");
var _ = require("underscore");
var BaseView = require("../base/baseview");
var Handlebars = require("../base/handlebars");
var AutoCompleteView = require("../search/views");
var api = require("../utils/api");
var get_params = require("../utils/get_params");
var sprintf = require("sprintf-js").sprintf;


var SuperUserCreateModalTemplate = require("./hbtemplates/superusercreatemodal.handlebars");
var SuperUserCreateModalView = BaseView.extend({
    events: {
        "click .create-btn": "create_superuser_click",
        "keypress #id_superusername": "key_user",
        "keypress #id_superpassword": "key_pass",
        "keypress #id_confirmsuperpassword": "key_confirm"
    },

    template: SuperUserCreateModalTemplate,

    initialize: function() {
        _.bindAll(this, "close_modal", "show_modal", "add_superuser_form");
        this.render();
        $("body").append(this.el);
    },

    render: function() {
        this.$el.html(this.template());
        var self = this;
        _.defer(self.add_superuser_form);
    },

    add_superuser_form: function() {
        this.show_modal();
        $.ajax({
            context: this,
            type: 'GET',
            url: 'api/django_user_form',
            dataType: 'json',
            success : function(e){
                if (e.Status == 'ShowModal'){
                    $('#superusercreate-container').html(e.data);
                    setTimeout(function () {this.$("#id_superusername").focus().select();}, 900);
                }
            },
            error : function(e){
                $('#superusercreate-container').html("<div class='alert alert-danger'>Cannot correctly load the admin creation form. " + e.status + " (" + e.statusText + ")</div>");
                console.log(e);
            }
        });
    },

    create_superuser_click: function() {
        $('#superusercreate-box').submit({param1: this}, function (e) {
            mContext = e.data.param1;
            e.preventDefault();
            $.ajax({
                context: mContext,
                type: 'post',
                url: 'api/django_user',
                dataType: 'json',
                data: $("#superusercreate-box").serialize(),
                success : function(e){
                    if (e.Status == 'Success') {
                        this.close_modal();
                        window.statusModel.set("has_superuser", true);
                    }else if (e.Status == 'Invalid'){
                        $('#superusercreate-container').html(e.data);
                        this.highlight_form();
                    }
                },
                error : function(e){
                    console.log(e);
                }
            });
        });
    },

    highlight_form: function(){
        if (this.$("#id_superpassword").val() == this.$("#id_confirmsuperpassword").val() && this.$("#id_confirmsuperpassword").val()){
            this.$("#id_confirmsuperpassword").css({ 'box-shadow': '0 0 5px 3px rgba(0,171,0,0.75) inset', 'border-color':'#03B3FF'});
        }else{
            this.$("#id_confirmsuperpassword").focus().css({ 'box-shadow': '0 0 5px 3px rgba(171,0,0,0.75) inset', 'border-color':'#a94442'});
        }
        if (this.$("#id_superpassword").val()){
            this.$("#id_superpassword").css({ 'box-shadow': '0 0 5px 3px rgba(0,171,0,0.75) inset', 'border-color':'#03B3FF'});
        }else{
            this.$("#id_superpassword").focus().css({ 'box-shadow': '0 0 5px 3px rgba(171,0,0,0.75) inset', 'border-color':'#a94442'});
        }
        if (this.$("#id_superusername").val()){
            this.$("#id_superusername").css({ 'box-shadow': '0 0 5px 3px rgba(0,171,0,0.75) inset', 'border-color':'#03B3FF'});
        }else{
            this.$("#id_superusername").focus().css({ 'box-shadow': '0 0 5px 3px rgba(171,0,0,0.75) inset', 'border-color':'#a94442'});
        }
    },

    close_modal: function() {
        $("#superUserCreateModal").modal('hide');
    },

    show_modal: function() {
        $("#superUserCreateModal").modal('show');
    },

    key_user: function(event) {
        if (event.which == ENTER_KEY) {
            event.preventDefault();
            this.$("#id_superpassword").focus().select();
        }
    },

    key_pass: function(event) {
        if (event.which == ENTER_KEY) {
            event.preventDefault();
            this.$("#id_confirmsuperpassword").focus().select();
        }
    },

    key_confirm: function(event) {
        if (event.which == ENTER_KEY) {
            event.preventDefault();
            this.$(".create-btn").focus().click();
        }
    }
});

// Separate out the modal behaviour from the login functionality
// This allows the LoginView to be embedded more flexibly across the site if needed
var LoginModalTemplate = require("./hbtemplates/loginmodal.handlebars");
var LoginModalView = BaseView.extend({
    template: LoginModalTemplate,

    initialize: function(options) {
        _.bindAll(this, "close_modal", "show_modal", "addLoginView");
        this.set_options(options);
        this.render();
        $("body").append(this.el);
    },

    render: function() {
        this.$el.html(this.template());
        // If we don't want for render to complete, often, the containing element for the login is missing
        _.defer(this.addLoginView);
    },

    addLoginView: function() {
        if (this.loginView) {
            // If loginView already exists rerender and set this.next on it so it has URL redirect info
            this.loginView.render();
            this.loginView.next = this.next;
        } else {
            // Otherwise create a new login view, and close the model when the login successfully completes
            this.loginView = new LoginView({model: this.model, el: "#login-container", next: this.next});
            this.listenTo(this.loginView, "login_success", this.close_modal);
        }
        if (this.start_open) {
            // If the start_open option is flagged, show the modal straight away.
            this.show_modal();
        }
    },

    close_modal: function() {
        $("#loginModal").modal('hide');
    },

    show_modal: function() {
        $("#loginModal").modal('show');
    },

    set_options: function(options) {
        this.start_open = options.start_open;
        this.next = options.next;
    }
});

var LoginTemplate = require("./hbtemplates/login.handlebars");
var LoginView = BaseView.extend({

    events: {
        "click .login-btn": "login_click",
        "click .password-btn": "toggle_password",
        "change #id_facility": "facility_change",
        "keypress #id_username": "key_user",
        "keypress #id_password": "key_pass"
    },

    template: LoginTemplate,

    initialize: function(options) {
        _.bindAll(this, "handle_login");
        this.next = options.next;
        this.facility = (this.model.get("facilities")[0] || {id:""}).id;
        this.admin = false;
        if (this.model.get("simplified_login")) {
            this.set_autocomplete();
        }
        this.render();
    },

    render: function() {
        this.render_data = {
            "simplified_login": this.model.get("simplified_login")
        };
        if (this.model.get("facilities").length > 1) {
            this.render_data["facilities"] = this.model.get("facilities");
        }
        this.$el.html(this.template(this.render_data));
    },

    login_click: function() {
        this.login();
    },

    login: function(username, password, facility) {
        this.$(".form-group").parent().removeClass("has-error");
        username = username || this.$("#id_username").val();
        password = password || this.$("#id_password").val();
        facility = facility || this.facility || this.$("#id_facility").val();
        if (!username) {
            this.$("#id_username-container").addClass("has-error");
        } else if (!password && (!this.model.get("simplified_login") || this.admin)) {
            this.$("#id_password-container").addClass("has-error");
        } else {
            this.model.login(username, password, facility, this.handle_login);
        }
    },

    handle_login: function(response) {
        if (response.status == 200) {
            this.trigger("login_success");
            if (location.href.indexOf("signup") > -1) {
                window.location = "/";
            }
            if (this.next) {
                window.location = this.next;
            } else if (response.redirect) {
                window.location = response.redirect;
            }
        } else {
            var error_data = JSON.parse(response.responseText);
            var message = error_data.messages.error;
            this.$("#id_" + error_data.error_highlight + "-container").addClass("has-error");
            this.$("#id_" + error_data.error_highlight).popover({
                content: message,
                placement: "auto bottom"
            });
            this.$("#id_" + error_data.error_highlight).popover("show");
            if (error_data.error_highlight == "password") {
                this.$("#id_" + error_data.error_highlight).val("");
            }
        }
    },

    toggle_password: function() {
        this.admin = !this.admin;
        if (this.admin) {
            this.$("#id_username").autocomplete("disable");
            this.$("#id_password-container").show();
        } else {
            this.$("#id_username").autocomplete("enable");
            this.$("#id_password-container").hide();
        }
        this.set_login_button_state();
    },

    facility_change: function(event) {
        this.facility = this.$("#id_facility").val();
        if (this.model.get("simplified_login")) {
            this.set_autocomplete();
        }
    },

    set_autocomplete: function() {
        // this initializes self.student_usernames for start_autocomplete
        var self = this;
        var data = {
            facility: this.facility,
            is_teacher: false
        };
        var setGetParamDict = require("utils/get_params").setGetParamDict;
        var url = setGetParamDict(window.sessionModel.get("USER_URL"), data);
        api.doRequest(url, null, {
            cache: true,
            dataType: "json",
            ifModified: true
        }).success(function(data, textStatus, xhr) {
            self.student_usernames = [];

            for (var i=0; i < data.objects.length; i++) {
                self.student_usernames.push(data.objects[i].username);
            }

            self.start_autocomplete();
        });
    },

    start_autocomplete: function() {
        var self = this;

        this.$("#id_username").autocomplete({
            autoFocus: true,
            minLength: 2,
            delay: 0,
            html: true,  // extension allows html-based labels
            appendTo: ".login",
            source: function(request, response) {
                var names = _.filter(self.student_usernames, function(username) {
                    return username.search(request.term) === 0;
                });
                return response(names.slice(0,10));
            },
            select: function(event, ui) {
                self.$("#id_username").val(ui.item.value);
                self.login(ui.item.value);
            }
        });
        // Cannot disable autocomplete before it has been enabled
        // So start this button off disabled and enable it when autocomplete
        // has finished loading.

        // Copy of method because when called by event below, does not receive
        // the view instance as 'this'
        function set_login_button_state(event) {
            if (self.admin || self.check_user_in_list()) {
                self.$(".login-btn").removeAttr("disabled");
            } else {
                self.$(".login-btn").attr("disabled", "disabled");
            }
        }
        set_login_button_state();
        this.$(".password-btn").removeAttr("disabled");
        this.$("#id_username").change(set_login_button_state);
    },

    key_user: function(event) {
        if (event.which == 13) {
            if (this.model.get("simplified_login") && !this.admin) {
                if (this.check_user_in_list()) {
                    this.login();
                }
            } else {
                this.$("#id_password").focus();
            }
        }
    },

    key_pass: function(event) {
        if (event.which == 13) {
            this.login();
        }
    },

    check_user_in_list: function() {
        return this.student_usernames.indexOf(this.$("#id_username").val()) > -1;
    },

    set_login_button_state: function(event) {
        if (this.admin || this.check_user_in_list()) {
            this.$(".login-btn").removeAttr("disabled");
        } else {
            this.$(".login-btn").attr("disabled", "disabled");
        }
    }
});


/**
 * View that wraps the point display in the top-right corner of the screen, updating itself when points change.
 */
var TotalPointView = Backbone.View.extend({

    initialize: function() {
        _.bindAll(this, "render");
        this.listenTo(this.model, "change:points", this.render);
        this.render();
    },

    render: function() {

        var points = this.model.get("points");
        var message = null;

        // only display the points if they are greater than zero, and the user is logged in
        if (!this.model.get("is_logged_in")) {
            return;
        }

        message = sprintf(gettext(" %(points)d points "), { points : points });

        this.$el.html(message);
        this.$el.show();
    }

});

var UsernameView = Backbone.View.extend({

    initialize: function() {
        _.bindAll(this, "render");
        this.listenTo(this.model, "change:username", this.render);
        this.render();
    },

    render: function() {

        var username_span = this.model.get("username");

        // only display the points if they are greater than zero, and the user is logged in
        if (!this.model.get("is_logged_in")) {
            return;
        }

        this.$el.html(username_span);
        this.$el.show();
    }

});

var UserView = BaseView.extend({

    events: {
        "click #nav_logout": "logout"
    },

    initialize: function() {
        _.bindAll(this, "render");

        this.model.loaded.then(this.render);

        this.listenTo(this.model, "change", this.render);

    },

    render: function() {

        if (this.model.get("is_logged_in")) {
            // create an instance of the total point view, which encapsulates the point display in the top right of the screen
            if (this.usernameView) {
                this.usernameView.render();
            } else {
                this.usernameView = new UsernameView({model: this.model, el: "#username"});
            }

            if (this.totalPointView) {
                this.totalPointView.render();
            } else {
                this.totalPointView = new TotalPointView({model: this.model, el: "#points"});
            }

            // For mobile (Bootstrap xs) view
            if (this.totalPointViewXs) {
                this.totalPointViewXs.render();
            } else {
                this.totalPointViewXs = new TotalPointView({model: this.model, el: "#points-xs"});
            }
        } else {
            // User is not logged in, so initialize the login modal
            var options = {};
            /* 
            *  Check the GET params to see if there is a 'next'
            *  This means that someone has tried to access an unauthorized page, but we want them to
            *  login before accessing this page
            */
            var next = get_params.getParamValue("next");
            // Check the GET params to see if a 'login' flag has been set
            // If this is the case, the modal should start open
            var login = get_params.getParamValue("login");
            if (login || this.login_start_open) {
                // Set an option for the modal to start open
                options.start_open = true;
            }
            if (next) {
                // Set the option for the URL redirect after login success
                options.next = next;
            }
            // If SuperUserCreateModalView get displayed, don't display loginModalView
            if (window.statusModel.get("has_superuser")){
                if (this.loginModalView) {
                    // If there is already a loginModalView for some reason, just set the above options on it
                    // and rerender
                    this.loginModalView.set_options(options);
                    if (this.login_start_open) {
                        this.loginModalView.show_modal();
                    }
                } else {
                    // Otherwise just start the modal view with these options, but add in the statusModel with it
                    options.model = this.model;
                    this.loginModalView = new LoginModalView(options);
                }
            }
        }
    },

    logout: function() {
        this.model.logout();
    }
});

/* This view toggles which navbar items are displayed to each type of user */ 
var ToggleNavbarTemplate = require("./hbtemplates/navigation.handlebars");
ToggleNavbarView = BaseView.extend ({

    template: ToggleNavbarTemplate,

    initialize: function() {

        _.bindAll(this, "render", "collapsed_nav");
        this.listenTo(this.model, "change:is_logged_in", this.render);
        $("topnav").append(this.template());
        $(window).on("resize", this.collapsed_nav);
    },

    render: function() {

        this.$el.html(this.template(this.model.attributes));
        
        this.userView = new UserView({ model: this.model, el: "#topnav" });
        $("#topnav").prepend(new AutoCompleteView().$el);

        // activates nav tab according to current page
        if ( this.model.pageType() == "teachPage" ) {
            this.$(".teach-tab").addClass("active");
        } else if ( this.model.pageType() == "learnPage" ) {
            this.$(".learn-tab").addClass("active");
        } else if ( this.model.pageType() == "managePage" ) {
            this.$(".manage-tab").addClass("active");   
        }

        this.collapsed_nav();
    },

    /*  This function addresses Bootstrap's limitation of having a dropdown menu in an already collapsed menu.
        Specifically, it ensures that the "user" dropdown menu is already expanded when the containing menu is collapsed
    */
    collapsed_nav: function() {
        if ( !this.model.get("is_logged_in") ) {
            return; // If not logged in, the needed elements won't exist.
        }
        var data_toggle = this.$("#user-name-a");
        var menu = this.$("#user-name");
        if ( $('body').innerWidth() <= 750 ) {
            data_toggle.removeAttr("data-toggle");
            menu.addClass("open");
        } else {
            data_toggle.attr("data-toggle", "dropdown");
            menu.removeClass("open");
        }
    }

});

module.exports = {
    "ToggleNavbarView": ToggleNavbarView,
    "SuperUserCreateModalView": SuperUserCreateModalView
};

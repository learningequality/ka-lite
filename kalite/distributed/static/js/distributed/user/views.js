// Separate out the modal behaviour from the login functionality
// This allows the LoginView to be embedded more flexibly across the site if needed

window.SuperUserCreateModalView = BaseView.extend({
    template: HB.template("user/superusercreatemodal"),

    initialize: function() {
        _.bindAll(this);
        this.render();
        $("body").append(this.el);
    },

    render: function() {
        this.$el.html(this.template());
        _.defer(this.addSuperUserForm);
    },

    addSuperUserForm: function() {
        this.show_modal();
        if (this.superuserView) {
            this.superuserView.render();
        } else {
            this.superuserView = new SuperUserCreateView({model: this.model, el: "#superusercreate-container"});
            this.listenTo(this.superuserView, "superusercreate_success", this.close_modal);
        }
    },

    close_modal: function() {
        $("#superUserCreateModal").modal('hide');
    },

    show_modal: function() {
        $("#superUserCreateModal").modal('show');
    }
});

window.SuperUserCreateView = BaseView.extend({

    events: {
        "click .create-btn": "create_superuser_click",
        "keypress #super_username": "key_user",
        "keypress #super_password": "key_pass",
        "keypress #super_email": "key_email"
    },

    template: HB.template("user/superusercreate"),

    initialize: function() {
        _.bindAll(this);
        this.admin = false;
        this.render();
    },

    render: function() {
        this.$el.html(this.template());
    },

    create_superuser_click: function() {
        if (this.validateForm()){
            $.ajax({
                context: this,
                url: 'create_superuser_from_browser/',
                type: 'POST',
                data: $("#superusercreate-box").serialize(),
                success: function(data, textStatus, xhr)
                {
                    this.trigger("superusercreate_success")
                },
            });
        }
    },

    validateForm: function(){
        var valid1, valid2, valid2, valid3 = false;
        if (this.$("#super_username").val()){
            this.$("#super_username").css({ 'borderColor': 'green', 'border-width': '3px'});
            valid1 = true;
        }else{
            this.$("#super_username").css({ 'borderColor': 'red', 'border-width': '3px'});
        }
        if (this.$("#super_password").val()){
            this.$("#super_password").css({ 'borderColor': 'green', 'border-width': '3px'});
            valid2 = true;
        }else{
            this.$("#super_password").css({ 'borderColor': 'red', 'border-width': '3px'});
        }
        if (this.validateEmail(this.$("#super_email").val())){
            this.$("#super_email").css({ 'borderColor': 'green', 'border-width': '3px'});
            valid3 = true;
        }else{
            this.$("#super_email").css({ 'borderColor': 'red', 'border-width': '3px'});
        }
        if (valid1 && valid2 && valid3){
            return true;
        }else{
            return false;
        }
    },

    validateEmail: function(email){
        var re = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
        return re.test(email);
    },

    key_user: function(event) {
        if (event.which == 13) {
            this.$("#super_password").focus().select();
        }
    },

    key_pass: function(event) {
        if (event.which == 13) {
            this.$("#super_email").focus().select();
        }
    },

    key_email: function(event) {
        if (event.which == 13) {
            this.create_superuser_click();
        }
    }
});

window.LoginModalView = BaseView.extend({
    template: HB.template("user/loginmodal"),

    initialize: function() {
        _.bindAll(this);
        this.render();
        $("body").append(this.el);
    },

    render: function() {
        this.$el.html(this.template());
        _.defer(this.addLoginView);
    },

    addLoginView: function() {
        if (this.loginView) {
            this.loginView.render();
        } else {
            this.loginView = new LoginView({model: this.model, el: "#login-container"});
            this.listenTo(this.loginView, "login_success", this.close_modal);
        }
        if (this.start_open) {
            this.show_modal();
        }
    },

    close_modal: function() {
        $("#loginModal").modal('hide');
    },

    show_modal: function() {
        $("#loginModal").modal('show');
    }
});

window.LoginView = BaseView.extend({

    events: {
        "click .login-btn": "login_click",
        "click .password-btn": "toggle_password",
        "change #id_facility": "facility_change",
        "keypress #id_username": "key_user",
        "keypress #id_password": "key_pass"
    },

    template: HB.template("user/login"),

    initialize: function() {
        _.bindAll(this);
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
        } else {
            var error_data = JSON.parse(response.responseText);
            var message = error_data.messages.error;
            this.$("#id_" + error_data.error_highlight + "-container").addClass("has-error");
            this.$("#id_" + error_data.error_highlight).popover({
                content: message,
                placement: "auto bottom",
                template: sprintf('<div id="id_%(popover_id)s-popover" class="popover alert alert-danger" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>',{popover_id: error_data.error_highlight})
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
        var url = setGetParamDict(window.sessionModel.get("USER_URL"), data);
        doRequest(url, null, {
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
        this.set_login_button_state();
        this.$(".password-btn").removeAttr("disabled");
        this.$("#id_username").on( "autocompletesearch", this.set_login_button_state);
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

    set_login_button_state: function() {
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
        _.bindAll(this);
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

        message = sprintf(gettext("Points: %(points)d "), { points : points });
        if (ds.store.show_store_link_once_points_earned) {
            message += " | <a href='/store/'>Store!</a>";
        }

        this.$el.html(message);
        this.$el.show();
    }

});

var UsernameView = Backbone.View.extend({

    initialize: function() {
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

window.UserView = BaseView.extend({

    events: {
        "click #nav_logout": "logout"
    },

    initialize: function() {
        _.bindAll(this);

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
            if (this.loginModalView) {
                this.loginModalView.render();
            } else {
                this.loginModalView = new LoginModalView({model: this.model});
            }
            if (window.location.search.search("login") > -1 || this.login_start_open) {
                this.loginModalView.start_open = true;
                delete this.login_start_open;
            }
        }
    },

    logout: function() {
        this.model.logout();
    }
});
// Separate out the modal behaviour from the login functionality
// This allows the LoginView to be embedded more flexibly across the site if needed

window.LoginModalView = Backbone.View.extend({
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
    },

    close_modal: function() {
        $("#loginModal").modal('hide');
    }
});

window.LoginView = Backbone.View.extend({

    events: {
        "click .login-btn": "login",
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

    login: function() {
        this.$("input").parent().removeClass("has-error");
        username = this.$("#id_username").val();
        password = this.$("#id_password").val();
        facility = this.facility || this.$("#id_facility").val();
        if (!username) {
            this.$("#id_username").parent().addClass("has-error");
        } else if (!password && (!this.model.get("simplified_login") || this.admin)) {
            this.$("#id_password").parent().addClass("has-error");
        } else {
            this.model.login(username, password, facility, this.handle_login);
        }
    },

    handle_login: function(response) {
        if (response.status == 200) {
            this.trigger("login_success");
        } else {
            var error_data = JSON.parse(response.responseText);
            this.$("#id_" + error_data.error_highlight).parent().addClass("has-error");
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
    },

    facility_change: function(event) {
        this.facility = this.$("#id_facility").val();
        if (this.model.get("simplified_login")) {
            this.set_autocomplete();
        }
    },

    set_autocomplete: function() {
        var self = this;
        var data = {
            facility: this.facility,
            is_teacher: false
        };
        var url = setGetParamDict(USER_URL, data);
        doRequest(url, null, {
            cache: true,
            dataType: "json",
            timeout: _timeout_length,
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
            }
        });
        // Cannot disable autocomplete before it has been enabled
        // So start this button off disabled and enable it when autocomplete
        // has finished loading.
        this.$(".password-btn").removeAttr("disabled");
    },

    key_user: function(event) {
        if (event.which == 13) {
            if (this.model.get("simplified_login") && !this.admin) {
                this.login();
            } else {
                this.$("#id_password").focus();
            }
        }
    },

    key_pass: function(event) {
        if (event.which == 13) {
            this.login();
        }
    }
});


/**
 * View that wraps the point display in the top-right corner of the screen, updating itself when points change.
 */
var TotalPointView = Backbone.View.extend({

    initialize: function() {
        _.bindAll(this);
        this.model.bind("change:points", this.render);
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

window.UserView = Backbone.View.extend({

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
        }
    },

    logout: function() {
        this.model.logout();
    }
});
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
                this.loginModalView = new LoginModalView({model: this.model})
            }
        }
    },

    logout: function() {
        this.model.logout();
    }
});

// Separate out the modal behaviour from the login functionality
// This allows the LoginView to be embedded more flexibly across the site if needed

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
            this.loginView.render()
        } else {
            this.loginView = new LoginView({model: this.model, el: "#login-container"})
            this.listenTo(this.loginView, "login_success", this.close_modal);
        }
    },

    close_modal: function() {
        $("#loginModal").modal('hide');
    }
})

window.LoginView = BaseView.extend({

    events: {
        "click .login-btn": "login"
    },

    template: HB.template("user/login"),

    initialize: function() {
        _.bindAll(this);
        this.render();
    },

    render: function() {
        this.render_data = {
            "simplified_login": this.model.get("simplified_login")
        };
        if (this.model.get("facilities").length > 1) {
            this.render_data["facilities"] = this.model.get("facilities");
        } else {
            this.facility = this.model.get("facilities")[0].id || "";
        }
        this.$el.html(this.template(this.render_data));
    },

    login: function() {
        username = this.$("#login-username").val();
        password = this.$("#login-password").val();
        facility = this.facility || this.$("#login-facility").val();
        this.model.login(username, password, facility, this.handle_login);
    },

    handle_login: function(response) {
        if (response.status == 200) {
            this.trigger("login_success");
        } else {
            var error_data = JSON.parse(response.responseText);
            this.$("#login-" + error_data.error_highlight).parent().addClass("has-error");
            if (error_data.error_highlight == "password") {
                this.$("#login-" + error_data.error_highlight).val("");
            }
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
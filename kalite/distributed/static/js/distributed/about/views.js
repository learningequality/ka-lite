var Backbone = require("base/backbone");

var diagnostics = {};

var AboutView = Backbone.View.extend({
    template: require("./hbtemplates/about.handlebars"),

    initialize: function() {
        this.generate_diagnostics();
    },
    render: function() {
        console.log(JSON.stringify(diagnostics));
        this.$el.html(this.template({
            diagnostics: diagnostics
        }));

        return this;
    },
    generate_diagnostics: function() {
        var self = this;
        $.ajax({
            type: 'get',
            url: 'data/',
            dataType: 'json',
            success: function(data) {
                if(data.status == 'success') {
                    for(var diag in data.diagnostics) {
                        diagnostics[data.diagnostics[diag][0].toUpperCase()] = data.diagnostics[diag][1];
                    }
                    self.render();
                }
            },
            error: function() {
                console.log("An error has occurred while calculating diagnostics.");
            }
        });
    }
});

module.exports = {
    AboutView: AboutView
};

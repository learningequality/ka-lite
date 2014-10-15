var StateModel = Backbone.Model.extend({
    defaults: {
        group_id: GROUP_ID,
        facility_id: FACILITY_ID
    }
});

var FacilityModel = Backbone.Model.extend();

var GroupModel = Backbone.Model.extend();

var FacilityCollection = Backbone.Collection.extend({
    url: FACILITY_RESOURCE_URL
});

var GroupCollection = Backbone.Collection.extend({
    url: GROUP_RESOURCE_URL
});


var FacilitySelectView = Backbone.View.extend({
    template: HB.template('coach_nav/facility-select'),

    initialize: function() {
        this.facility_list = new FacilityCollection();
        this.facility_list.fetch();
        this.listenTo(this.facility_list, 'sync', this.render);
        this.render();
    },

    render: function() {
        this.$el.html(this.template({
            facilities: this.facility_list.toJSON(),
            selected: this.model.get("facility_id")
        }));
        return this;
    },

    events: {
        "change": "facility_changed"
    },

    facility_changed: function() {
        this.model.set("facility_id", this.$(":selected").val());
    }
});

var GroupSelectView = Backbone.View.extend({
    template: HB.template('coach_nav/group-select'),

    initialize: function() {
        this.group_list = new GroupCollection();
        this.fetch_by_facility();
        this.listenTo(this.group_list, 'sync', this.render);
        this.listenTo(this.model, "change:facility_id", this.fetch_by_facility);
        this.render();
    },

    render: function() {
        this.$el.html(this.template({
            groups: this.group_list.toJSON(),
            selected: this.model.get("group_id")
        }));
        return this;
    },

    events: {
        "change": "group_changed"
    },

    group_changed: function() {
        this.model.set("group_id", this.$(":selected").val());
    },

    fetch_by_facility: function() {
        // Get new facility ID and fetch
        this.group_list.fetch({
            data: $.param({
                facility_id: this.model.get("facility_id")
            })
        });
    }
});


var NavigationContainerView = Backbone.View.extend({
    template: HB.template('coach_nav/reports-nav'),

    initialize: function() {
        // Create and fetch our list of groups and facilities on page load
        this.model = new StateModel();
        this.facility_view = new FacilitySelectView({
            model: this.model
        });
        this.group_view = new GroupSelectView({
            model: this.model
        });

        this.render();
    },

    render: function() {
        this.$el.html(this.template({
            selected: REPORT_ID
        }));
        this.$('#group-select-container').append(this.group_view.$el);
        this.$('#facility-select-container').append(this.facility_view.$el);
    },

    events: {
        "click #display-coach-report": "go_to_coach_report"
    },

    go_to_coach_report: function(ev) {
        // Parse options and show the correct coach report page 
        ev.preventDefault();

        var form = this.$('#coachreport-select-form');
        var report = this.$('#report-select').val();
        var facility = this.$('#facility-select').val();
        var group = this.$('#group-select').val();
        var url = "";
        switch (report) {
            case "tabular":
                url = TABULAR_REPORT_URL;
                break;
            case "scatter":
                url = SCATTER_REPORT_URL;
                break;
            case "timeline":
                url = TIMELINE_REPORT_URL;
                break;
            case "test":
                url = TEST_REPORT_URL;
                break;
        }
        url += "?" + $.param({
            facility_id: facility,
            group_id: group
        });

        window.location = url;
    }
});

// Two function below are for the "share" link
function generate_current_link() {
    var url = window.location.href;

    // Add topic paths
    if (typeof get_topic_paths_from_tree != 'undefined') {
        var topic_paths = get_topic_paths_from_tree();
        for (var pi in topic_paths) {
            url += "&topic_path=" + topic_paths[pi];
        }
        // Add axis information
        url = setGetParam(url, "xaxis", $("#xaxis option:selected").val());
        url = setGetParam(url, "yaxis", $("#yaxis option:selected").val());
        url = setGetParam(url, "facility", $("#facility option:selected").val());
        url = setGetParam(url, "group", $("#" + $("#facility option:selected").val() + "_group_select option:selected").val());
    }

    return url;
}
function display_link () {
    var url_field = $('input#url');
    var link_box = $('#link-box');
    var link_text = null;

    if(url_field.is(":visible")){
        url_field.hide();
        link_text = gettext("share");
    }
    else{
        url_field.val(generate_current_link());
        url_field.show().focus().select().attr('readonly', true);
        link_text = gettext("hide");
    }
    link_box.find('a').text("(" + link_text + ")");
}
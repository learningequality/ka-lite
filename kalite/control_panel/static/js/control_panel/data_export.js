// Handles the data export functionality of the control panel
// TODO-blocker(dylanjbarth) 0.13: limit requests and handle pagination

// Models 
var ZoneModel = Backbone.Model.extend();

var FacilityModel = Backbone.Model.extend();

var GroupModel = Backbone.Model.extend();

var DataExportStateModel = Backbone.Model.extend();

// Collections
var ZoneCollection = Backbone.Collection.extend({
    model: ZoneModel,
    url: ALL_ZONES_URL
});

var FacilityCollection = Backbone.Collection.extend({
    model: FacilityModel,
    url: ALL_FACILITIES_URL
});

var GroupCollection = Backbone.Collection.extend({
    model: GroupModel,
    url: ALL_GROUPS_URL
});


// Views

var ZoneSelectView = Backbone.View.extend({

    template: HB.template('data_export/zone-select'),

    initialize: function() {
        // Create collections 
        this.zone_list = new ZoneCollection();

        // on central, this is a dynamic view
        // on distributed, this is a placeholder view,
        if (this.model.get("is_central")) {
            // Re-render self when fetch returns or model state changes
            this.listenTo(this.zone_list, 'sync', this.render);

            // Fetch collection by org_id
            this.zone_list.fetch({
                data: $.param({
                    "org_id": this.options.org_id,
                    "limit": 0
                })
            });
        }

        this.render();
    },

    render: function() {
        var rendered_html = this.template({
            zones: this.zone_list.toJSON(),
            selection: this.model.get("zone_id")
        });

        if (this.model.get("is_central")) {
            this.$el.html(rendered_html);
        } else {
            this.$el.html(rendered_html).hide();
        }
    },

    events: {
        "change": "zone_changed"
    },

    zone_changed: function(ev) {
        // Update state model
        var zone_id = this.$("select").val();
        this.model.set({
            facility_id: undefined,
            group_id: undefined,
            zone_id: zone_id
        });
    }
});

var FacilitySelectView = Backbone.View.extend({

    template: HB.template('data_export/facility-select'),

    initialize: function() {
        // Create collections
        this.facility_list = new FacilityCollection();
        
        // Re-render self when the fetch returns or state model changes
        this.listenTo(this.facility_list, 'sync', this.render);
        this.listenTo(this.facility_list, 'reset', this.render);
        this.listenTo(this.model, 'change:resource_id', this.render);

        // on central, facilities depend on the zone selected
        // on distributed, zone is fixed 
        if (this.model.get("is_central")) {
            // Listen for any changes on the zone model, when it happens, re-fetch self
            this.listenTo(this.model, 'change:zone_id', this.fetch_by_zone);
        }
        
        // Fetch collection, by fixed zone 
        this.fetch_by_zone();

        // Render
        this.render();
    },

    render: function() {

        var template_context = {
            facilities: this.facility_list.toJSON(),
            selection: this.model.get("facility_id"),
            // Facility select is enabled only if zone_id has been set 
            is_disabled: this.is_disabled()
        };

        this.$el.html(this.template(template_context));

        return this;
    },

    is_disabled: function() {
        // Helper function to quickly check whether the facility select input 
        // should be enabled or disabled based on conditions that matter to it. 
        if (this.model.get("resource_id") === "device_log"){
            return true;
        }
        return ((this.model.get("zone_id") === undefined || this.model.get("zone_id") === "") && this.model.get("is_central"));
    },

    render_waiting: function() {
        var template_context = {
            is_disabled: true,
            loading: true
        };

        this.$el.html(this.template(template_context));
    },

    events: {
        "change": "facility_changed"
    },

    facility_changed: function(ev) {
        // Update state model 
        var facility_id = this.$("select").val();

        this.model.set({
            group_id: undefined,
            facility_id: facility_id
        });
    },

    fetch_by_zone: function() {
        // First disable the select
        if (this.model.get("is_central")) {
            var zone_id = this.model.get("zone_id");
            
            // only fetch if a zone ID has been set 
            if (zone_id) {
                this.render_waiting();
                this.facility_list.fetch({
                    data: $.param({
                        "zone_id": zone_id,
                        "limit": 0
                    })
                });
            } else {
                this.facility_list.reset();
            }
        } else {
            this.render_waiting();
            this.facility_list.fetch();
        }
    }
});

var GroupSelectView = Backbone.View.extend({
    
    template: HB.template('data_export/group-select'),

    initialize: function() {
        // Create collections
        this.group_list = new GroupCollection();

        // Re-render self when the fetch returns or state model changes
        this.listenTo(this.group_list, 'sync', this.render);
        this.listenTo(this.group_list, 'reset', this.render);
        this.listenTo(this.model, 'change:resource_id', this.render);

        // on central, groups depend on facilities which depend on the zone selected
        // on distributed, zone is fixed, so groups just depend on facilities 
        // Regardless, wait for any changes on the facility model, and then re-fetch self
        this.listenTo(this.model, 'change:facility_id', this.fetch_by_facility);

        // Render
        this.render();
    },

    render: function() {
        var template_context = {
            groups: this.group_list.toJSON(),
            selection: this.model.get("group_id"),
            // Group select is enabled only if facility_id has been set 
            is_disabled: this.is_disabled()
        };

        this.$el.html(this.template(template_context));

        return this;
    },

    is_disabled: function() {
        if (this.model.get("resource_id") === "device_log"){
            return true;
        }
        return !this.model.get("facility_id");
    },

    render_waiting: function() {
        var template_context = {
            is_disabled: true,
            loading: true
        };

        this.$el.html(this.template(template_context));
    },

    events: {
        "change": "group_changed"
    },

    group_changed: function(ev) {
        var group_id = this.$("select").val();
        this.model.set({ group_id: group_id });
    },

    fetch_by_facility: function() {
        var facility_id = this.model.get("facility_id");
        // only fetch if facility ID has been set 
        if (facility_id) {
            this.render_waiting();
            this.group_list.fetch({
                data: $.param({
                    "facility_id": facility_id,
                    "limit": 0
                })
            });
        } else {
            this.group_list.reset();
        }
    }
});

var DataExportView = Backbone.View.extend({
    // the containing view
    template: HB.template('data_export/data-export-container'),

    initialize: function() {

        this.zone_select_view = new ZoneSelectView({
            org_id: this.options.org_id,
            model: this.model
        });

        this.facility_select_view  = new FacilitySelectView({
            model: this.model
        });

        this.group_select_view = new GroupSelectView({
            model: this.model
        });

        this.render();
    },

    events: {
        "click #export-button": "export_data",
        "change #resource-id": "resource_changed"
    },

    render: function() {
        // render container     
        this.$el.html(this.template(this.model.attributes));

        // append zone, facility & group select views.
        this.$('#student-select-container').append(this.zone_select_view.$el);
        this.$('#student-select-container').append(this.facility_select_view.$el);
        this.$('#student-select-container').append(this.group_select_view.$el);
    },

    resource_changed: function() {
        this.model.set({
            resource_id: this.$('#resource-id').val()
        });
    },

    resource_endpoint: function() {
        // Return the API url endpoint for the current resource id
        var resource_id = this.model.get("resource_id");
        switch  (resource_id) {
            case "facility_user":
                return FACILITY_USER_CSV_URL;
            case "test_log":
                return TEST_LOG_CSV_URL;
            case "attempt_log":
                return ATTEMPT_LOG_CSV_URL;
            case "exercise_log":
                return EXERCISE_LOG_CSV_URL;
            case "device_log":
                return DEVICE_LOG_CSV_URL;
        }
    },

    export_data: function(ev) {
        ev.preventDefault();

        // Update export link based on currently selected paramters 
        var zone_id = this.model.get("zone_id");
        var facility_id = this.model.get("facility_id");
        var group_id = this.model.get("group_id");
        var resource_endpoint = this.resource_endpoint();

        // If no zone_id, all is selected, so compile a comma seperated string
        // of zone ids to pass to endpoint
        var zone_ids = "";
        if (zone_id===undefined || zone_id==="") {
            zone_ids = _.map(this.zone_select_view.zone_list.models, function(zone) { return zone.get("id"); }).join();
        }

        var export_params = "?" + $.param({
            group_id: group_id,
            facility_id: facility_id,
            zone_id: zone_id,
            zone_ids: zone_ids,
            format:"csv",
            limit:0
        });

        var export_data_url = this.resource_endpoint() + export_params;
        window.location = export_data_url;
    }
});

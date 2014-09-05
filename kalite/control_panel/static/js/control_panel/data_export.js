// Handles the data export functionality of the control panel

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
        "click #export-button": "export_data"
    },  

    render: function() {
        // render container     
        this.$el.html(this.template());

        // append zone, facility & group select views.
        this.$('#student-select-container').append(this.zone_select_view.$el)
        this.$('#student-select-container').append(this.facility_select_view.$el);
        this.$('#student-select-container').append(this.group_select_view.$el);
    },

    resource_id: function() {
        // Returns the currently selected resource id
        return $("#resource-id").find(":selected").attr("data-resource-id");
    },

    resource_endpoint: function() {
        // Return the API url endpoint for the current resource id
        var resource_id = this.resource_id();
        switch  (resource_id) {
            case "facility_user":
                return FACILITY_USER_CSV_URL;
            case "test_log":
                return TEST_LOG_CSV_URL;
            case "attempt_log":
                return ATTEMPT_LOG_CSV_URL;
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
        if (!zone_id) {
            var zone_ids_string = ""
            var zone_ids = $("#zone-name").find("option");
            for (var i = 0; i < zone_ids.length; i++) {
                var zone_id = $(zone_ids[i]).attr("data-zone-id");
                if (zone_id) {
                    zone_ids_string += "," + zone_id;
                }
            }
        }

        var export_data_url = this.resource_endpoint();
        if (group_id) {
            export_data_url += "?group_id=" + group_id;
        } else if (facility_id) {
            export_data_url += "?facility_id=" + facility_id;
        } else if (zone_id) {
            export_data_url += "?zone_id=" + zone_id;
        } else if (zone_ids_string) {
            export_data_url += "?zone_ids=" + zone_ids_string;
        }

        export_data_url += "&format=csv"

        window.location = export_data_url;
    }
});


var ZoneSelectView = Backbone.View.extend({

    template: HB.template('data_export/zone-select'),

    initialize: function() {
        // Create collections 
        this.zone_list = new ZoneCollection();

        // on central, this is a dynamic view
        // on distributed, this is a placeholder view,
        if (this.model.attributes.is_central) {
            // Re-render self when fetch returns or model state changes
            this.listenTo(this.zone_list, 'sync', this.render);

            // Fetch collection by org_id
            this.zone_list.fetch({
                data: $.param({ "org_id": this.options.org_id })
            });
        }

        // Render 
        this.render();
    },

    render: function() {
        var rendered_html = this.template({
            zones: this.zone_list.toJSON(),
            selection: this.model.attributes.zone_id
        });

        // TODO(dylanjbarth): perhaps hide this using css rather than JS?
        if (this.model.attributes.is_central) {
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
        var zone_id = $("#" + ev.target.id).find(":selected").attr("data-zone-id");

        this.model.set({ 
            facility_id: undefined,
            group_id: undefined,
            zone_id: zone_id
        });
    }
})


var FacilitySelectView = Backbone.View.extend({

    template: HB.template('data_export/facility-select'),

    initialize: function() {
        // Create collections
        this.facility_list = new FacilityCollection();
        
        // Re-render self when the fetch returns or state model changes
        this.listenTo(this.facility_list, 'sync', this.render);
        this.listenTo(this.model, 'change', this.render);

        // on central, facilities depend on the zone selected
        // on distributed, zone is fixed 
        if (this.model.attributes.is_central) {
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
            selection: this.model.attributes.facility_id,
            // Facility select is enabled only if zone_id has been set 
            is_disabled: this.model.attributes.zone_id ? false : true
        };

        this.$el.html(this.template(template_context));

        return this;
    },

    events: {
        "change": "facility_changed"
    },

    facility_changed: function(ev) {
        // Update state model 
        var facility_id = $("#" + ev.target.id).find(":selected").attr("data-facility-id");
        this.model.set({ 
            group_id: undefined ,
            facility_id: facility_id
        });
    },

    fetch_by_zone: function() {
        var zone_id = this.model.get("zone_id");
        // only fetch if a zone ID has been set 
        if (zone_id) {
            this.facility_list.fetch({
                data: $.param({ "zone_id": zone_id })
            });
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
        this.listenTo(this.model, 'change', this.render);       

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
            selection: this.model.attributes.group_id,
            // Group select is enabled only if facility_id has been set 
            is_disabled: this.model.attributes.facility_id ? false : true
        };

        this.$el.html(this.template(template_context));

        return this;
    },

    events: {
        "change": "group_changed"
    },

    group_changed: function(ev) {
        var group_id = $("#" + ev.target.id).find(":selected").attr("data-group-id");
        this.model.set({ group_id: group_id });
    },

    fetch_by_facility: function() {
        var facility_id = this.model.get("facility_id");
        // only fetch if facility ID has been set 
        if (facility_id) {
            this.group_list.fetch({
                data: $.param({ "facility_id": facility_id })
            });
        }
    }
});



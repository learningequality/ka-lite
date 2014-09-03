// Handles the data export functionality of the control panel

// Models 
var ZoneModel = Backbone.Model.extend();

var FacilityModel = Backbone.Model.extend();

var GroupModel = Backbone.Model.extend();

var StudentSelectStateModel = Backbone.Model.extend();  

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

        console.log("bloasdf")
        window.dat = this.model

        this.render();
    },

    render: function() {
        // render container     
        this.$el.html(this.template());

        // append zone, facility & group select views. hide zone select if not central.
        if (this.options.is_central) {
            this.$('#student-select-container').append(this.zone_select_view.$el);    
        } else { 
            this.$('#student-select-container').append(this.zone_select_view.$el).hide();
        }
        this.$('#student-select-container').append(this.facility_select_view.$el);
        this.$('#student-select-container').append(this.group_select_view.$el);
    },

    events: {
        "click #export-button": "exportData"
    },

    exportData: function(ev) {
        ev.preventDefault();

        // Get the final ids
        var facility_id = this.model.get("facility_id") ? this.model.get("facility_id") : "all";
        var group_id = this.model.get("group_id") ? this.model.get("group_id") : "all";

        // Format them for the form 
        var facility_input = sprintf("<input type='hidden' value='%(facility_id)s' name='facility_id'>", {"facility_id": facility_id});
        var group_input = sprintf("<input type='hidden' value='%(group_id)s' name='group_id'>", {"group_id": group_id});

        // Append the data we care about, and submit it
        // TODO(dylan) make an API endpoint, this is lame 
        var form = $('#data-export-form');
        form
            .append(facility_input)
            .append(group_input)
            .attr("action", document.URL)
            .append("<input type='hidden' name='csrfmiddlewaretoken' value='" + csrftoken + "' />") 
            .submit();
    }
});


var ZoneSelectView = Backbone.View.extend({
    template: HB.template('data_export/zone-select'),

    initialize: function() {
        console.log("A new ZoneSelectView was born!");

        // Create collections 
        this.zone_list = new ZoneCollection();

        // Re-render self when fetch returns or model state changes
        this.listenTo(this.zone_list, 'sync', this.render);

        // Fetch collection by zone_id
        this.zone_list.fetch({
            data: $.param({ "org_id": this.options.org_id })
        });

        // Render 
        this.render();
    },

    render: function() {
        console.log("Rendering zone select view");
        console.log("Zone id " + this.model.attributes.zone_id)

        this.$el.html(this.template({
            zones: this.zone_list.toJSON(),
            selection: this.model.attributes.zone_id
        }));
    },

    events: {
        "change": "zone_changed"
    },

    zone_changed: function(ev) {
        // When zone is changed by the user, we reset facility_id to be nothing
        this.model.set({ facility_id: "all" });

        // update the state model
        var zone_id = $("#" + ev.target.id).find(":selected").attr("data-zone-id");
        this.model.set({ zone_id: zone_id });
    }
})


var FacilitySelectView = Backbone.View.extend({
    template: HB.template('data_export/facility-select'),

    initialize: function() {

        console.log("A new FacilitySelectView was born!");
        
        // Create collections
        this.facility_list = new FacilityCollection();

        // Re-render self when the fetch returns or state model changes
        this.listenTo(this.facility_list, 'sync', this.render);

        // Fetch collection, by zone if org id exists
        this.facility_list.fetch();

        // Render
        this.render();
    },

    render: function() {

        console.log("Rendering facility select view")
        console.log("Facility id " + this.model.attributes.facility_id);

        this.$el.html(this.template({
            facilities: this.facility_list.toJSON(),
            selection: this.model.attributes.facility_id
        }));

        return this;
    },

    events: {
        "change": "facility_changed"
    },

    facility_changed: function(ev) {
        // When facility is changed by the user, we reset group_id to be nothing
        this.model.set({ group_id: "all" });

        // update the state model
        var facility_id = $("#" + ev.target.id).find(":selected").attr("data-facility-id");
        this.model.set({ facility_id: facility_id });
    },

    fetch_by_zone: function() {
        var zoneID = this.model.get("facility_id") === "all" ? undefined : this.model.get("facility_id");
        this.group_list.fetch({
            data: $.param({ "facility_id": facility_id })
        })
    }
});


var GroupSelectView = Backbone.View.extend({
    // inner view containing the facility and group select boxes 
    
    template: HB.template('data_export/group-select'),

    initialize: function() {

        console.log("A new GroupSelectView was born!");

        // Create collections
        this.group_list = new GroupCollection();

        // Re-render self when the fetch returns 
        this.listenTo(this.group_list, 'sync', this.render);

        // Fetch collection
        this.fetchByFacility();

        // Render
        this.render();

        // Listen for any changes on the state model, when it happens, re-fetch self
        this.listenTo(this.model, 'change:facility_id', this.fetchByFacility);
    },

    render: function() {

        console.log("Rendering group select view");
        console.log("Group id " + this.model.attributes.group_id);

        this.$el.html(this.template({
            groups: this.group_list.toJSON(),
            selection: this.model.attributes.group_id
        }));

        return this;
    },

    events: {
        "change": "group_changed"
    },

    group_changed: function(ev) {
        var group_id = $("#" + ev.target.id).find(":selected").attr("data-group-id");
        this.model.set({ group_id: group_id });
    },

    fetchByFacility: function() {
        // pass undefined to the api for 'all'
        var facility_id = this.model.get("facility_id") === "all" ? undefined : this.model.get("facility_id");
        this.group_list.fetch({
            data: $.param({ "facility_id": facility_id })
        })
    }
});



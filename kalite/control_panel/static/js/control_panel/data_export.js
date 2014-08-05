// Handles the data export functionality of the control panel

// Models 
var FacilityModel = Backbone.Model.extend();

var GroupModel = Backbone.Model.extend();

var StudentSelectStateModel = Backbone.Model.extend();  

// Collections
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

        var self = this;

        this.facility_select_view  = new FacilitySelectView({
            model: this.model
        });

        this.group_select_view = new GroupSelectView({
            model: this.model
        });

        this.render();
    },

    render: function() {
        // render container     
        this.$el.html(this.template());

        // append facility & group select views
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
        // TODO(dylan) is this hacky? not sure what the right paradigm is 
        var form = $('#data-export-form');
        form
            .append(facility_input)
            .append(group_input)
            .attr("action", document.URL)
            .append("<input type='hidden' name='csrfmiddlewaretoken' value='" + csrftoken + "' />") 
            .submit();
    }
});


var FacilitySelectView = Backbone.View.extend({
    template: HB.template('data_export/facility-select'),

    initialize: function() {
        // Create collections
        this.facility_list = new FacilityCollection();

        // Re-render self when the fetch returns or state model changes
        this.listenTo(this.facility_list, 'sync', this.render);

        // Fetch collection 
        this.facility_list.fetch();

        // Render
        this.render();
    },

    render: function() {
        this.$el.html(this.template({
            facilities: this.facility_list.toJSON(),
            selection: this.model.attributes.facility_id
        }));

        return this;
    },

    events: {
        "change": "facilityChanged"
    },

    facilityChanged: function(ev) {
        // update the state model
        var facilityID = $("#" + ev.target.id).find(":selected").attr("data-facility-id");
        this.model.set({ facility_id: facilityID });
    }
});


var GroupSelectView = Backbone.View.extend({
    // inner view containing the facility and group select boxes 
    
    template: HB.template('data_export/group-select'),

    initialize: function() {
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
        // TODO(dylan) this prevents reset of the group :( but how else to do it?
        this.model.set({ group_id: undefined });
        this.$el.html(this.template({
            groups: this.group_list.toJSON()
        }));

        return this;
    },

    events: {
        "change": "groupChanged"
    },

    groupChanged: function(ev) {
        var groupID = $("#" + ev.target.id).find(":selected").attr("data-group-id");
        this.model.set({ group_id: groupID });
    },

    fetchByFacility: function() {
        var facilityID = this.model.get("facility_id");
        // TODO(dylan): are we handling pagination from the API?
        this.group_list.fetch({
            data: $.param({ "facility_id": facilityID })
        })
    }
});



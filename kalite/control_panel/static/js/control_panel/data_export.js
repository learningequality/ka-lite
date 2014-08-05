// Handles the data export functionality of the control panel

// Models 
var FacilityModel = Backbone.Model.extend();

var GroupModel = Backbone.Model.extend();

var StudentSelectStateModel = Backbone.Model.extend({
    // a model for storing the state of the currently selected Facility and Group
    defaults: {
        "facility_id": "all",
        "group_id": "all"
    }
});  


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
        this.model = new StudentSelectStateModel();    

        this.render();
    },

    render: function() {
        this.facility_select_view  = new FacilitySelectView({
            model: this.model,
            selected: this.options.facility_id
        });

        this.group_select_view = new GroupSelectView({
            model: this.model,
            selected: this.options.group_id
        });
        
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

        // Re-render self when the fetch returns 
        this.listenTo(this.facility_list, 'sync', this.render);

        // Fetch collection 
        this.facility_list.fetch();

        // Render
        this.render()
    },

    render: function() {
        this.$el.html(this.template({
            facilities: this.facility_list.toJSON()
        }));

        $('[data-facility-id=' + this.options.selected + ']').prop("selected", true);

        // When we re-render this view, "All" is selected by default
        this.model.set({facility_id: "all"});
    },

    events: {
        "change": "facilityChanged"
    },

    facilityChanged: function(ev) {
        // update the state model
        var facilityID = $("#" + ev.target.id).find(":selected").attr("data-facility-id");
        this.model.set({ facility_id: facilityID });
        this.options.selected = facilityID;
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
        this.group_list.fetch();

        // Render
        this.render();

        // Listen for any changes on the state model, when it happens, re-fetch self
        this.listenTo(this.model, 'change:facility_id', this.stateModelChanged);
    },

    render: function() {
        this.$el.html(this.template({
            groups: this.group_list.toJSON()
        }));

        $('[data-group-id=' + this.options.selected + ']').prop("selected", true);

        // When we re-render this view, "All" is selected by default
        this.model.set({group_id: "all"});
    },

    events: {
        "change": "groupChanged"
    },

    groupChanged: function(ev) {
        var groupID = $("#" + ev.target.id).find(":selected").attr("data-group-id");
        this.model.set({ group_id: groupID });
        this.options.selected = groupID;
    },

    stateModelChanged: function() {
        var facilityID = this.model.get("facility_id");
        // TODO(dylan): are we handling pagination??
        this.group_list.fetch({
            data: $.param({ "facility_id": facilityID })
        })
    }
});



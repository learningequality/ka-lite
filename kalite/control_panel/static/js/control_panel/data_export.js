// Handles the data export functionality of the control panel

// Models 
var FacilityModel = Backbone.Model.extend({
    initialize: function() {
        console.log("A new facility was was born!");
    }
});

var GroupModel = Backbone.Model.extend({
    initialize: function() {
        console.log("A new group was born!");
    }
});

var StudentSelectStateModel = Backbone.Model.extend({
    // a model for storing the state of the currently selected Facility and Group
    defaults: {
        "facility_id": "all",
        "group_id": "all"
    },
    initialize: function() {
        console.log("A new StudentSelectStateModel was born");
        console.log(this);
    }
});  


// Collections
var FacilityCollection = Backbone.Collection.extend({ 
    model: FacilityModel, 
    url: ALL_FACILITIES_URL,

    initialize: function() {
        console.log("A new FacilityCollection was born!");
    }
});

var GroupCollection = Backbone.Collection.extend({ 
    model: GroupModel,
    url: ALL_GROUPS_URL,

    initialize: function() {
        console.log("A new GroupCollection was born!");
    }

});


// Views 
var DataExportView = Backbone.View.extend({
    // the containing view
    template: HB.template('data_export/data-export-container'),

    initialize: function() {
        console.log("A new DataExportView was born!");
        this.model = new StudentSelectStateModel();    
        this.render();
    },

    render: function() {
        this.facility_select_view  = new FacilitySelectView({
            model: this.model
        });

        this.group_select_view = new GroupSelectView({
            model: this.model
        })
        
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
        var self = this;
        console.log("Exporting CSV for: "); 
        var facility_id = this.model.get("facility_id") ? this.model.get("facility_id") : "all";
        var group_id = this.model.get("group_id") ? this.model.get("group_id") : "all";
        console.log("Facility: " + facility_id);
        console.log("Group: " + group_id);
        console.log(document.URL);
        $.ajax({
            url: document.URL,
            type: 'POST',
            data: {
                "facility_id": facility_id,
                "group_id": group_id 
            },
            success: function(data) {
                console.log("success");
                console.log(data)
            },
            error: function(err) {
                show_message("error", err.responseText);
            }
        });
    }

});


var FacilitySelectView = Backbone.View.extend({
    template: HB.template('data_export/facility-select'),

    initialize: function() {
        console.log("A new FacilitySelectView was born!");
        
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

        // When we re-render this view, "All" is selected by default
        this.model.set({group_id: "all"});
    },

    events: {
        "change": "groupChanged"
    },

    groupChanged: function(ev) {
        var groupID = $("#" + ev.target.id).find(":selected").attr("data-group-id");
        this.model.set({ group_id: groupID });
    },

    stateModelChanged: function() {
        var facilityID = this.model.get("facility_id");
        // TODO(dylan): are we handling pagination??
        this.group_list.fetch({
            data: $.param({ "facility_id": facilityID })
        })
    }
});



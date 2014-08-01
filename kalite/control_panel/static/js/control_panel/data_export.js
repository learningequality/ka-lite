// Handles the data export functionality of the control panel

// Models 
var FacilityModel = Backbone.Model.extend();

var GroupModel = Backbone.Model.extend();

var TestLogModel = Backbone.Model.extend();

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
    url: FACILITIES_URL // TODO(dylan) add in the zone id to this query 
});

var GroupCollection = Backbone.Collection.extend({ 
    model: GroupModel,
    url: GROUPS_URL
});

var TestLogCollection = Backbone.Collection.extend({
    model: TestLogModel,
    url: TEST_LOGS_URL
})


// Views 
var DataExportView = Backbone.View.extend({
    // the containing view
    template: HB.template('data_export/data-export-container'),

    initialize: function() {
        this.model = new StudentSelectStateModel();    
        this.test_logs = new TestLogCollection();
        this.render();

        // Trigger a data export when we finish fetching test logs
        this.listenTo(this.test_logs, 'sync', this.exportCSV);
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
        "click #export-button": "getTestLogs"
    },

    getTestLogs: function(ev) {
        ev.preventDefault();

        console.log("Export button clicked. Fetching requested test log data.");

        // Get the ids
        var facility_id = this.model.get("facility_id") ? this.model.get("facility_id") : "all";
        var group_id = this.model.get("group_id") ? this.model.get("group_id") : "all";

        // Get the test logs we care about 
        this.test_logs.fetch({
            data: $.param({ "facility_id": facility_id, "group_id": group_id })
        })
    },

    exportCSV: function(ev) {

        console.log(ev)
        if (this.test_logs.length === 0) {
            show_message("warning", gettext("No test logs exist for the students specified, so there is nothing to export."));
        } else {
            var test_log_data = []
            
            // Create header cols 
            var header = ["Facility Name", "Facility ID", "Group Name", "Group ID", "Student User ID", "Test ID", "Num correct", "Total number completed"];
            test_log_data.push(header);

            // Create body cols 
            this.test_logs.each(function(test_log) {
                log_attr = test_log.attributes;
                group_name = log_attr.user.group ? log_attr.user.group.name : "Ungrouped";
                group_id = log_attr.user.group ? log_attr.user.group.id : "None";
                log_attr_array = [log_attr.user.facility.name, log_attr.user.facility.id, group_name, group_id, log_attr.user.id, log_attr.test, log_attr.total_correct, log_attr.total_number];
                test_log_data.push(log_attr_array);
            });

            // Create CSV 
            var csvContent = "data:text/csv;charset=utf-8,";
            _.each(test_log_data, function(test_log, i) {
                var dataString = test_log.join(",");
                csvContent += i < test_log_data.length ? dataString + "\n" : dataString;
            }); 

            // Nice filename for Sarojini
            window.test_logs = this.test_logs;
            filename = this.model.facility_id === 'all' ? 'f_all__' : sprintf('f_%(facility_name)s__', {'facility_name': this.test_logs.models[0].attributes.user.facility.name});
            today = new Date();
            filename += sprintf('%(year)s-%(month)s-%(day)s', {'year': today.getFullYear(), 'month': today.getMonth()+1, 'day': today.getDate()});

            // Endcode csv and trigger download
            var encodedUri = encodeURI(csvContent);
            var link = $("<a href='" + encodedUri + "' download='" + filename + "'></a>");
            link[0].click();

            show_message("success", gettext("Your CSV download has started."));
        }
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
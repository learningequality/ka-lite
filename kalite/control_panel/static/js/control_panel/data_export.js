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
            .append(CSRF_TOKEN) // TODO(dylan) do we need a CSRF if we do a GET? 
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


// else:
//         # Get the params 
//         facility_id = request.GET.get("facility_id")
//         group_id = request.GET.get("group_id")

//         ## CSV File Specification
//         # CSV Cols Facility Name | Facility ID* | Group Name | Group ID | Student User ID* | Test ID | Num correct | Total number completed
        
//         ## Fetch data for CSV
//         # Facilities 
//         if facility_id == 'all':
//             # TODO(dylan): can this ever break? Will an admin always have at least one facility in a zone?
//             facilities = Facility.objects.by_zone(get_object_or_None(Zone, id=zone_id))
//         else:   
//             facilities = Facility.objects.filter(id=facility_id)

//         # Facility Users 
//         if group_id == 'all': # get all students at the facility
//             facility_ids = [facility.id for facility in facilities]
//             facility_users = FacilityUser.objects.filter(facility__id__in=facility_ids)
//         else: # get the students for the specific group
//             facility_users = FacilityUser.objects.filter(group__id=group_id)
        
//         ## A bit of error checking 
//         if len(facility_users) == 0:
//             messages.error(request, _("No students exist for this facility and group combination."))
//             return context 

//         # TestLogs
//         user_ids = [u.id for u in facility_users]
//         test_logs = TestLog.objects.filter(user__id__in=user_ids)

//         if len(test_logs) == 0:
//             messages.error(request, _("No test logs exist for these students."))
//             return context 

//         ## Build CSV 
//         # Nice filename for Sarojini
//         filename = 'f_all__' if facility_id == 'all' else 'f_%s__' % facilities[0].name
//         filename += 'g_all__' if group_id == 'all' else 'g_%s__' % facility_users[0].group.name
//         filename += '%s' % datetime.datetime.today().strftime("%Y-%m-%d")
//         csv_response = HttpResponse(content_type="text/csv")
//         csv_response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename

//         # CSV header
//         writer = csv.writer(csv_response)
//         writer.writerow(["Facility Name", "Facility ID", "Group Name", "Group ID", "Student User ID", "Test ID", "Num correct", "Total number completed"])
        
//         # CSV Body
//         for t in test_logs:
//             group_name = t.user.group.name if hasattr(t.user.group, "name") else "Ungrouped"
//             group_id = t.user.group.id if hasattr(t.user.group, "id") else "None"
//             writer.writerow([t.user.facility.name, t.user.facility.id, group_name, group_id, t.user.id, t.test, t.total_correct, t.total_number])

//         return csv_response

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

var TestModel = Backbone.Model.extend({
    initialize: function() {
        console.log("A new test was born!");
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
var TestCollection = Backbone.Collection.extend({ model: TestModel });


// Views 
var DataExportView = Backbone.View.extend({
    // the containing view
    template: HB.template('data_export/data-export-container'),

    initialize: function() {
        console.log("A new DataExportView was born!");        
        this.render();
    },

    render: function() {
        this.student_select_view  = new StudentSelectView();
        
        // render container     
        this.$el.html(this.template());

        // append student select view
        this.$('#student-select-container').html(this.student_select_view.$el);
    }

})

var StudentSelectView = Backbone.View.extend({
    // inner view containing the facility and group select boxes 
    
    template: HB.template('data_export/student-select-container'),

    initialize: function() {

        var self = this;

        console.log("A new SelectView was born!");
        
        // Create collections
        this.facility_list = new FacilityCollection();
        this.group_list = new GroupCollection();

        // Listen for dem changez
        this.listenTo(this.facility_list, 'reset', this.render);
        this.listenTo(this.group_list, 'reset', this.render);

        // Fetch collections 
        this.facility_list.fetch({reset: true}).then(function() { self.render() });
        this.group_list.fetch({reset: true}).then(function() { self.render() });
    },

    render: function() {
        this.$el.html(this.template({
            facilities: this.facility_list.toJSON(),
            groups: this.group_list.toJSON()
        }));
    }
});



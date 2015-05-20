var CoachReportView = BaseView.extend({

    template: HB.template('coach_nav/reports-nav'),

    initialize: function(options) {

        this.facility_select_view = new FacilitySelectView({model: this.model});
        this.group_select_view = new GroupSelectView({model: this.model});

        this.render();
    },

    render: function() {
        this.$el.html(this.template());
        this.$('#group-select-container').append(this.group_select_view.$el);
        this.$('#facility-select-container').append(this.facility_select_view.$el);
        this.tabular_view = new TabularReportView({model: this.model});
        this.$("#student_report_container").append(this.tabular_view.$el);
    }
});


var eventData = { 
    page: 1,
    totalPages: 2,
    questions: [
    {
        question: "1",
        anchor: "a",
        events: [
            {
                attempt: "1",
                action: "answered '10'",
                duration: "40 sec",         
                status: "incorrect"                 
            },
            {
                attempt: "2",
                action: "answered '20'",
                duration: "45 sec",         
                status: "incorrect"
            },
            {
                attempt: "3",
                action: "used hint (3)",
                duration: "30 sec",         
                status: "incorrect"
            }
        ]
    },
    {
        question: "2",
        anchor: "b",
        events: [
            {
                attempt: "1",
                action: "answered '5'",
                duration: "30 sec",         
                status: "incorrect"                 
            },
            {
                attempt: "2",
                action: "answered '22'",
                duration: "20 sec",         
                status: "incorrect"
            },
            {
                attempt: "3",
                action: "used hint (0)",
                duration: "10 sec",         
                status: "correct"
            }
        ]
    },
    {
        question: "3",
        anchor: "c",
        events: [
            {
                attempt: "1",
                action: "answered '25'",
                duration: "30 sec",         
                status: "incorrect"                 
            },
            {
                attempt: "2",
                action: "answered '50'",
                duration: "10 sec",         
                status: "incorrect"
            },
            {
                attempt: "3",
                action: "answered '30'",
                duration: "20 sec",         
                status: "correct"
            }
        ]
    },
    {
        question: "4",
        anchor: "d",
        events: [
            {
                attempt: "1",
                action: "answered '2'",
                duration: "25 sec",         
                status: "incorrect"                 
            },
            {
                attempt: "2",
                action: "answered '0'",
                duration: "20 sec",         
                status: "incorrect"
            },
            {
                attempt: "3",
                action: "answered '4'",
                duration: "15 sec",         
                status: "correct"
            }
        ]
    },
    {
        question: "5",
        anchor: "a",
        events: [
            {
                attempt: "1",
                action: "answered '5'",
                duration: "30 sec",         
                status: "incorrect"                 
            },
            {
                attempt: "2",
                action: "answered '10'",
                duration: "25 sec",         
                status: "incorrect"
            },
            {
                attempt: "3",
                action: "answered '0'",
                duration: "30 sec",         
                status: "correct"
            }
        ]
    },
    {   
        question: "6",
        anchor: "b",
        events: [
            {
                attempt: "1",
                action: "answered '45'",
                duration: "15 sec",         
                status: "incorrect"                 
            },
            {
                attempt: "2",
                action: "answered '50'",
                duration: "30 sec",         
                status: "incorrect"
            },
            {
                attempt: "3",
                action: "answered '55'",
                duration: "20 sec",         
                status: "correct"
            }
        ]
    },
    {       
        question: "7",
        anchor: "c",
        events: [
            {
                attempt: "1",
                action: "answered '133'",
                duration: "10 sec",         
                status: "incorrect"                 
            },
            {
                attempt: "2",
                action: "answered '255'",
                duration: "50 sec",         
                status: "incorrect"
            },
            {
                attempt: "3",
                action: "answered '300'",
                duration: "10 sec",         
                status: "correct"
            }
        ]
    },
    {       
        question: "8",
        anchor: "d",
        events: [
            {
                attempt: "1",
                action: "answered '14'",
                duration: "15 sec",         
                status: "incorrect"                 
            },
            {
                attempt: "2",
                action: "answered '12'",
                duration: "30 sec",         
                status: "incorrect"
            },
            {
                attempt: "3",
                action: "answered '13'",
                duration: "20 sec",         
                status: "correct"
            }
        ]
    }   
]};
        
var detailsPanelView = BaseView.extend({
    
    //Number of items to show from the collection
    limit: 4,
    
    template: HB.template("coach_nav/detailspanel"),
    
    initialize: function () {
        _.bindAll(this);
        eventData["pages"] = [];
        for (var i = 0; i < eventData.totalPages; i++) {
            eventData.pages.push(i+1);
        }; 
        this.render();
    },
    
    render: function() {
        this.$el.html(this.template(eventData));
        this.bodyView = new detailsPanelBodyView ({
            data: { questions: eventData.questions.slice(0, this.limit)},
            el: this.$(".body")
        });
    }
});


var detailsPanelBodyView = BaseView.extend({
    
    template: HB.template("coach_nav/detailspanelbody"),
    
    initialize: function (options) {
        _.bindAll(this);
        this.data = options.data;
        this.render();
    },
    
    render: function() {
        this.$el.html(this.template(this.data));
    }
});

var TabularReportView = BaseView.extend({

    template: HB.template("tabular_reports/tabular-view"),

    initialize: function() {
        _.bindAll(this);
        this.set_data_model();
        this.listenTo(this.model, "change", this.set_data_model);
    },

    render: function() {
        this.$el.html(this.template({
            learners: this.learners.toJSON(),
            contents: this.contents.toJSON()
        }));
    },

    set_data_model: function (){
        var self = this;
        this.data_model = new CoachReportModel({
            facility: this.model.get("facility"),
            group: this.model.get("group")
        });
        if (this.model.get("facility")) {
            this.data_model.fetch().then(function() {
                self.learners = new Backbone.Collection(self.data_model.get("learners"));
                self.contents = new Backbone.Collection(self.data_model.get("contents"));
                for (var i = 0; i < self.learners.length; i++) {
                    self.learners.models[i].set("logs", _.object(
                        _.map(_.filter(self.data_model.get("logs"), function(log) {
                            return log.user === self.learners.models[i].get("pk");
                        }), function(item) {
                            return [item.exercise_id || item.video_id || item.content_id, item];
                        })));
                }
                self.render();
            });
        }
    }

});

var FacilitySelectView = Backbone.View.extend({
    template: HB.template('coach_nav/facility-select'),

    initialize: function() {
        _.bindAll(this);
        this.facility_list = new FacilityCollection();
        this.facility_list.fetch();
        this.listenTo(this.facility_list, 'sync', this.render);
        this.render();
    },

    render: function() {
        this.$el.html(this.template({
            facilities: this.facility_list.toJSON(),
            selected: this.model.get("facility")
        }));
        if (!this.model.get("facility")) {
            this.facility_changed();
        }
        return this;
    },

    events: {
        "change": "facility_changed"
    },

    facility_changed: function() {
        this.model.set("facility", this.$(":selected").val());
    }
});

var GroupSelectView = Backbone.View.extend({
    template: HB.template('coach_nav/group-select'),

    initialize: function() {
        this.group_list = new GroupCollection();
        this.fetch_by_facility();
        this.listenTo(this.group_list, 'sync', this.render);
        this.listenTo(this.model, "change:facility", this.fetch_by_facility);
        this.render();
    },

    render: function() {
        this.$el.html(this.template({
            groups: this.group_list.toJSON(),
            selected: this.model.get("group")
        }));
        return this;
    },

    events: {
        "change": "group_changed"
    },

    group_changed: function() {
        this.model.set("group", this.$(":selected").val());
    },

    fetch_by_facility: function() {
        if (this.model.get("facility")) {
            // Get new facility ID and fetch
            this.group_list.fetch({
                data: $.param({
                    facility_id: this.model.get("facility"),
                    // TODO(cpauya): Find a better way to set the kwargs argument of the tastypie endpoint
                    // instead of using GET variables.  This will set it as False on the endpoint.
                    groups_only: ""
                })
            });
        }
    }
});

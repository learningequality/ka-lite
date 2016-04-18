var BaseView = require("base/baseview");
var _ = require("underscore");
var $ = require("base/jQuery");
var Backbone = require("base/backbone");

var messages = require("utils/messages");
var Models = require("./models");
var TabularReportViews = require("../tabular_reports/views");
var d3 = require("d3");

var date_string = require("utils/datestring").date_string;
var d3 = require("d3");

require("bootstrap-datepicker/dist/js/bootstrap-datepicker");
require("bootstrap-multiselect/dist/js/bootstrap-multiselect");

/*
Hierarchy of views:
CoachReportView:
    - FacilitySelectView
    - GroupSelectView
    - CoachSummaryView
*/

var TimeSetView = BaseView.extend({
    template: require("./hbtemplates/datepicker.handlebars"),

    events: {
        "click .setrange:not([disabled])": "set_range"
    },

    initialize: function () {
        var server_date_now = new Date(new Date().getTime() - window.statusModel.get("client_server_time_diff"));
        var default_start_date = new Date(server_date_now.getTime());
        default_start_date = new Date(default_start_date.setDate(default_start_date.getDate()-ds.coachreports.default_coach_report_day_range));

        this.model.set({
            "start_date": default_start_date,
            "end_date": server_date_now
        });
        this.render();
    },

    render: function() {
        this.$el.html(this.template({
            start_date: icu.getDateFormat("SHORT").format(this.model.get("start_date")),
            end_date: icu.getDateFormat("SHORT").format(this.model.get("end_date"))
        }));

        var format = icu.getDateFormatSymbols().order_short;

        format = format[0] + "/" + format[1] + "/" + format[2];

        format = format.toLowerCase().replace("y", "yy");

        var self = this;

        this.datepicker = this.$('.date-range').each(function(){
            $(this).datepicker({
                format: format,
                endDate: "0d",
                todayBtn: "linked",
                todayHighlight: true
            });
            $(this).datepicker().on('changeDate', function() {
                self.$(".setrange").removeAttr("disabled");
            });
        });
    },

    set_range: function() {
        this.model.set({
            start_date: this.$("#start").datepicker("getDate"),
            end_date: this.$("#end").datepicker("getDate")
        });
        this.model.trigger("set_time");
        this.$(".setrange").attr("disabled", "disabled");
        return false;
    }
});

var CoachSummaryView = BaseView.extend({
    /*
    This view displays summary stats for the currently selected facility (and optionally group)
    */

    template: require("./hbtemplates/landing.handlebars"),

    events: {
        "click #show_tabular_report": "toggle_tabular_view",
        "click #topic-list-submit": "set_topics"
    },


    /*
    this function populates the topic selection list
    */
    appendTopicList: function() {
        var parseData = this.data_model.get("available_topics");
        var targetElem = $("#topic-list").get(0);
        var frag = document.createDocumentFragment();

        var tids = $.parseJSON(this.data_model.get("topic_ids") || "[]");
        var ctr = -1;

        parseData.forEach(function(datum, index) {
            var opt = document.createElement("option");
            //this part maintains any currently selected
            //options as checked instead of reverting to default
            if(tids.length > 0) {
                ctr = tids.indexOf(datum.id);
                if(ctr !== -1){
                    opt.selected = "selected";
                    delete tids[ctr];
                    ctr = -1;
                }
            }
            if(datum.id.includes('pre-alg')) {
                opt.innerHTML = "Pre Alg: " + datum.title;
            } else {
                opt.innerHTML = datum.title;
            }

            opt.value = datum.id;
            frag.appendChild(opt);
        });
        targetElem.appendChild(frag);
    }, 

    /*
    this function produces a radial graph and inserts it into the target_elem
    data_sub is a portion of the data, while the data_total param is the total
    IE time spent doing backflips vs total time spent alive
    */
    displayRadialGraph: function(target_elem, data_sub, data_total) {
        var targetElemBox = $("#" + target_elem).get(0);
        var targetElemP = $("#" + target_elem + "_p").get(0);

        if(!data_sub || !data_total) {
            targetElemP.innerHTML = "N/A";
        } else {
            var parseData = [
                //parsing data to 2 decimal positions
                { label: gettext("Hours spent on content"), count: Math.round((data_sub * 100)/data_total) },
                { label: gettext("Other activites (exercises, etc.)"), count: Math.round(((data_total - data_sub) * 100)/data_total) }
            ];

            //adjusting the graph's size based on target_elem's sizing
            var width = targetElemBox.clientWidth;
            var height = targetElemBox.clientHeight;
            var radius = (Math.min(width, height) / 2);

            var color = d3.scale.category20();

            var svg = d3.select("#" + target_elem)
                .append("svg")
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", "translate(" + (width/2) + "," + (height/2) + ")");

            var arc = d3.svg.arc()
                .innerRadius(radius - radius/6)
                .outerRadius(radius);

            var pie = d3.layout.pie()
                .value(function(d) { return d.count; })
                .sort(null);

            var path = svg.selectAll("path")
                .data(pie(parseData))
                .enter()
                .append("path")
                .attr("d", arc)
                .attr("fill", function(d, i) {
                    return color(d.data.label);
                });

            //parsing to 2 decimals
            var content_percentage = Math.round((data_sub * 100)/data_total);
            targetElemP.innerHTML = content_percentage + "%";

            //this will display relevant data when you hover over that data's arc on the radial graph
            path.on('mouseover', function(d) {
                targetElemP.innerHTML = (d.data.label + ": " + d.data.count + "%");
            });

            //when not hovering, you'll see the content percentage
            path.on('mouseout', function() {
                targetElemP.innerHTML = content_percentage + "%";
            });
        }
    },

    initialize: function() {
        _.bindAll(this, "set_data_model", "render");
        this.listenTo(this.model, "change:facility", this.set_data_model);
        this.listenTo(this.model, "change:group", this.set_data_model);
        this.listenTo(this.model, "change:topic_ids", this.set_data_model);
        this.listenTo(this.model, "set_time", this.set_data_model);
        this.set_data_model();
    },

    set_topics: function() {
        var topic_ids = _.map(this.$("#topic-list option:checked"), function (node) {return node.value;});
        this.model.set("topic_ids", JSON.stringify(topic_ids));
    },

    set_data_model: function (){
        if (this.data_model) {
            var check_fields = ["facility", "group", "start_date", "end_date", "topic_ids"];
            var data_fields = _.pick(this.data_model.attributes, check_fields);
            var status_fields = _.pick(this.model.attributes, check_fields);
            if (!_.isEqual(data_fields, status_fields)) {
                delete this.data_model;
            }
        }

        if (!this.data_model) {
            this.data_model = new Models.CoachReportAggregateModel({
                facility: this.model.get("facility"),
                group: this.model.get("group"),
                start_date: date_string(this.model.get("start_date")),
                end_date: date_string(this.model.get("end_date")),
                topic_ids: this.model.get("topic_ids")
            });
            if (this.model.get("facility")) {
                this.listenTo(this.data_model, "sync", this.render);
                this.loading("#content-container");
                this.data_model.fetch();
            }

        }
    },

    set_progress_bar: function() {
        
        var in_progress = this.data_model.get("total_in_progress");
        var complete = this.data_model.get("total_complete");
        var struggling = this.data_model.get("total_struggling");
        var not_attempted = this.data_model.get("total_not_attempted");

        var total = complete + in_progress + struggling;

        var h = 50;
        var w = 500;
        var dataset = [struggling/total, complete/total, in_progress/total];


        var svg = d3.select("div.progressbar").append("svg").attr("width", w).attr("height", h).
            attr("class", "col-md-8 innerbar");

        svg.selectAll("rect").data(dataset).enter().append("rect").attr("x", function(d, i){
                var out = _.reduce(dataset.slice(0, i), function(memo, num) { return memo + num; }, 0) * w;
                out = isNaN(out) ? 0 : out;
                return out;
            }).attr("y", 0).attr("width", function(d) {
                return isNaN(d * w) ? 0 : d*w;
            }).attr("height", h).attr("class", "rect").attr("class", function(d, i){
                switch(i) {
                    case(0):
                        return "struggling";
                    case(1):
                        return "complete";
                    case(2):
                        return "partial";
                }
            });

        // Sets the text on the bar itself
        svg.selectAll("text").data(dataset).enter().append("text").text(function(d, i) {
            switch(i) {
                case(0):
                    return struggling;
                case(1):
                    return complete;
                case(2):
                    return in_progress;
            }
        }).attr("fill", "black").attr("x", function(d, i){
            var out = (_.reduce(dataset.slice(0, i), function(memo, num) { return memo + num; }, 0) + d/2) * w;
            out = isNaN(out) ? 0 : out;
            return out;
        }).attr("y", h/2).attr("font-size", "12px").style("text-anchor", "middle");

    },

    render: function() {

        this.loaded("#content-container");
        this.$el.html(this.template({
            status:this.model.attributes,
            data: this.data_model.attributes,
            start_date: icu.getDateFormat("SHORT").format(this.model.get("start_date")),
            end_date: icu.getDateFormat("SHORT").format(this.model.get("end_date"))
        }));

        messages.clear_messages();

        // If no user data at all, then show a warning to the user
        var ref, ref1;

        if ((this.data_model !== undefined ? this.data_model.get("learner_events") !== undefined ? this.data_model.get("learner_events").length : void 0 : void 0) === 0) {
          messages.show_message("warning", gettext("No recent learner data for this group is available."));
        }

        this.set_progress_bar();

        if (this.tabular_report_view) {
            this.tabular_report_view.remove();
            delete this.tabular_report_view;
        }

        this.displayRadialGraph("full_circle1", this.data_model.get("content_time_spent"), this.data_model.get("total_time_logged"));

        this.appendTopicList();


        $('#topic-list').multiselect({
            nonSelectedText: gettext('Default: Overview'),
            buttonWidth: '75%',
            numberDisplayed: 2,
            maxHeight: 350,
            disableIfEmpty: true,
            enableCaseInsensitiveFiltering: true
        });

        $('#topic-list-div > .btn-group > button').css({'width': '100%'});

    },

    toggle_tabular_view: _.debounce(function() {
        var self = this;
        if (!this.tabular_report_view) {
            this.$("#show_tabular_report").text("Loading");
            this.$("#show_tabular_report").attr("disabled", "disabled");
            this.tabular_report_view = new TabularReportViews.TabularReportView({model: this.model, complete: function() {
                if (self.tabular_report_view) {
                    // Check that tabular report view still exists, as it is possible for it to have been removed
                    // by the time this call back gets called.
                    self.$("#show_tabular_report").text(gettext("Hide Tabular Report"));
                    self.$("#show_tabular_report").removeAttr("disabled");
                }
            }});
            this.$("#detailed_report_view").append(this.tabular_report_view.el);
        } else {
            this.$("#show_tabular_report").text(gettext("Show Tabular Report"));
            this.tabular_report_view.remove();
            delete this.tabular_report_view;
        }
    }, 100)

});

var FacilitySelectView = Backbone.View.extend({
    /*
    This fetches data for facilities and displays them in a drop down
    */

    template: require("./hbtemplates/facility-select.handlebars"),

    initialize: function() {
        _.bindAll(this, "render");
        this.facility_list = new Models.FacilityCollection();
        this.listenTo(this.facility_list, 'sync', this.render);
        this.facility_list.fetch({
                data: $.param({
                    zone_id: ZONE_ID
                })
            });
    },

    render: function() {
        this.$el.html(this.template({
            facilities: this.facility_list.toJSON(),
            selected: this.model.get("facility")
        }));
        var id = this.model.get("facility");
        // This nonsense of 'id' not being the Backbone 'id' is because of tastypie Resource URLs being used as model ids
        this.model.set({
            "facility_name": this.facility_list.find(function(model){ return model.get("id") === id;}).get("name")
        });
        return this;
    },

    events: {
        "change": "facility_changed"
    },

    facility_changed: function() {
        var id = this.$(":selected").val();
        // This nonsense of 'id' not being the Backbone 'id' is because of tastypie Resource URLs being used as model ids
        this.model.set({
            "facility": id,
            "facility_name": this.facility_list.find(function(model){ return model.get("id") === id;}).get("name")
        });
    }
});

var GroupSelectView = Backbone.View.extend({
    /*
    This fetches group data for facilities and displays them in a drop down
    */

    template: require("./hbtemplates/group-select.handlebars"),

    initialize: function() {
        _.bindAll(this, "render");
        this.group_list = new Models.GroupCollection();
        this.listenTo(this.group_list, 'sync', this.render);
        this.fetch_by_facility();
        this.listenTo(this.model, "change:facility", this.fetch_by_facility);
    },

    render: function() {
        var self = this;

        // Add in 'All' and 'Ungrouped' groups if appropriate
        // Might be better to add in to the parse method of the collection
        if (this.group_list.length > 0) {
            this.group_list.add({
                id: "",
                name: gettext("All")
            }, {at: 0, silent: true});
            this.group_list.add({
                id: "Ungrouped",
                name: gettext("Ungrouped")
            }, {silent: true});
        }

        // Remove reference to groups from another facility
        // This nonsense of 'id' not being the Backbone 'id' is because of tastypie Resource URLs being used as model ids
        if (!this.group_list.some(function(model){ return model.get("id") === self.model.get("group");})) {
            this.model.set({
                "group": undefined,
                "group_name": undefined
            }, {silent: true});
        }

        this.$el.html(this.template({
            groups: this.group_list.toJSON(),
            selected: this.model.get("group")
        }));

        var id = this.model.get("group");
        var output, ref;
        // This nonsense of 'id' not being the Backbone 'id' is because of tastypie Resource URLs being used as model ids
        output = (ref = this.group_list.find(function(model) {
          return model.get("id") === id;
        })) !== undefined ? ref.get("name") : void 0;

        if (output) {
            this.model.set({
                "group_name": output
            });
        }

        return this;
    },

    events: {
        "change": "group_changed"
    },

    group_changed: function() {
        var id = this.$(":selected").val();
        // This nonsense of 'id' not being the Backbone 'id' is because of tastypie Resource URLs being used as model ids
        this.model.set({
            "group": id,
            "group_name": this.group_list.find(function(model){ return model.get("id") === id;}).get("name")
        });
    },

    fetch_by_facility: function() {
        if (this.model.get("facility")) {
            // Get new facility ID and fetch
            this.group_list.fetch({
                data: $.param({
                    facility_id: this.model.get("facility")
                })
            });
        }
    }
});

var CoachReportView = BaseView.extend({
    /*
    This is the wrapper view for the coach reports
    */

    template: require("./hbtemplates/reports-nav.handlebars"),

    initialize: function(options) {

        this.facility_select_view = new FacilitySelectView({model: this.model});
        this.group_select_view = new GroupSelectView({model: this.model});
        this.coach_summary_view = new CoachSummaryView({model: this.model});
        this.time_set_view = new TimeSetView({model: this.model});

        this.render();
    },

    render: function() {
        this.$el.html(this.template());
        this.$('#group-select-container').append(this.group_select_view.el);
        this.$('#facility-select-container').append(this.facility_select_view.el);
        this.$("#time-set-container").append(this.time_set_view.el);
        this.$("#student_report_container").append(this.coach_summary_view.el);

    },

});

module.exports = {
    CoachReportView: CoachReportView,
    CoachSummaryView: CoachSummaryView,
    FacilitySelectView: FacilitySelectView,
    GroupSelectView: GroupSelectView
};

function radialProgress(parent) {
    var _data=null,
        _duration= 1000,
        _selection,
        _margin = {top:0, right:0, bottom:30, left:0},
        __width = 300,
        __height = 300,
        _diameter,
        _label="",
        _fontSize=10;


    var _mouseClick;

    var _value= 0,
        _minValue = 0,
        _maxValue = 100;

    var  _currentArc= 0, _currentArc2= 0, _currentValue=0;

    var _arc = d3.svg.arc()
        .startAngle(0 * (Math.PI/180)); //just radians

    var _arc2 = d3.svg.arc()
        .startAngle(0 * (Math.PI/180))
        .endAngle(0); //just radians


    _selection=d3.select(parent);


    function component() {

        _selection.each(function (data) {

            // Select the svg element, if it exists.
            var svg = d3.select(this).selectAll("svg").data([data]);

            var enter = svg.enter().append("svg").attr("class","radial-svg").append("g");

            measure();

            svg.attr("width", __width)
                .attr("height", __height);


            var background = enter.append("g").attr("class","component")
                .attr("cursor","pointer")
                .on("click",onMouseClick);


            _arc.endAngle(360 * (Math.PI/180))

            background.append("rect")
                .attr("class","background")
                .attr("width", _width)
                .attr("height", _height);

            background.append("path")
                .attr("transform", "translate(" + _width/2 + "," + _width/2 + ")")
                .attr("d", _arc);

            background.append("text")
                .attr("class", "label")
                .attr("transform", "translate(" + _width/2 + "," + (_width + _fontSize) + ")")
                .text(_label);
           var g = svg.select("g")
                .attr("transform", "translate(" + _margin.left + "," + _margin.top + ")");


            _arc.endAngle(_currentArc);
            enter.append("g").attr("class", "arcs");
            var path = svg.select(".arcs").selectAll(".arc").data(data);
            path.enter().append("path")
                .attr("class","arc")
                .attr("transform", "translate(" + _width/2 + "," + _width/2 + ")")
                .attr("d", _arc);

            //Another path in case we exceed 100%
            var path2 = svg.select(".arcs").selectAll(".arc2").data(data);
            path2.enter().append("path")
                .attr("class","arc2")
                .attr("transform", "translate(" + _width/2 + "," + _width/2 + ")")
                .attr("d", _arc2);


            enter.append("g").attr("class", "labels");
            var label = svg.select(".labels").selectAll(".label").data(data);
            label.enter().append("text")
                .attr("class","label")
                .attr("y",_width/2+_fontSize/3)
                .attr("x",_width/2)
                .attr("cursor","pointer")
                .attr("width",_width)
                // .attr("x",(3*_fontSize/2))
                .text(function (d) { return Math.round((_value-_minValue)/(_maxValue-_minValue)*100) + "%" })
                .style("font-size",_fontSize+"px")
                .on("click",onMouseClick);

            path.exit().transition().duration(500).attr("x",1000).remove();


            layout(svg);

            function layout(svg) {

                var ratio=(_value-_minValue)/(_maxValue-_minValue);
                var endAngle=Math.min(360*ratio,360);
                endAngle=endAngle * Math.PI/180;

                path.datum(endAngle);
                path.transition().duration(_duration)
                    .attrTween("d", arcTween);

                if (ratio > 1) {
                    path2.datum(Math.min(360*(ratio-1),360) * Math.PI/180);
                    path2.transition().delay(_duration).duration(_duration)
                        .attrTween("d", arcTween2);
                }

                label.datum(Math.round(ratio*100));
                label.transition().duration(_duration)
                    .tween("text",labelTween);

            }

        });

        function onMouseClick(d) {
            if (typeof _mouseClick == "function") {
                _mouseClick.call();
            }
        }
    }

    function labelTween(a) {
        var i = d3.interpolate(_currentValue, a);
        _currentValue = i(0);

        return function(t) {
            _currentValue = i(t);
            this.textContent = Math.round(i(t)) + "%";
        }
    }

    function arcTween(a) {
        var i = d3.interpolate(_currentArc, a);

        return function(t) {
            _currentArc=i(t);
            return _arc.endAngle(i(t))();
        };
    }

    function arcTween2(a) {
        var i = d3.interpolate(_currentArc2, a);

        return function(t) {
            return _arc2.endAngle(i(t))();
        };
    }


    function measure() {
        _width=_diameter - _margin.right - _margin.left - _margin.top - _margin.bottom;
        _height=_width;
        _fontSize=_width*.2;
        _arc.outerRadius(_width/2);
        _arc.innerRadius(_width/2 * .85);
        _arc2.outerRadius(_width/2 * .85);
        _arc2.innerRadius(_width/2 * .85 - (_width/2 * .15));
    }


    component.render = function() {
        measure();
        component();
        return component;
    }

    component.value = function (_) {
        if (!arguments.length) return _value;
        _value = [_];
        _selection.datum([_value]);
        return component;
    }


    component.margin = function(_) {
        if (!arguments.length) return _margin;
        _margin = _;
        return component;
    };

    component.diameter = function(_) {
        if (!arguments.length) return _diameter
        _diameter =  _;
        return component;
    };

    component.minValue = function(_) {
        if (!arguments.length) return _minValue;
        _minValue = _;
        return component;
    };

    component.maxValue = function(_) {
        if (!arguments.length) return _maxValue;
        _maxValue = _;
        return component;
    };

    component.label = function(_) {
        if (!arguments.length) return _label;
        _label = _;
        return component;
    };

    component._duration = function(_) {
        if (!arguments.length) return _duration;
        _duration = _;
        return component;
    };

    component.onClick = function (_) {
        if (!arguments.length) return _mouseClick;
        _mouseClick=_;
        return component;
    }

    return component;

}


var data = {
    users: [ 
    {
        learner: "Ellie C.",
        taskstatus: "mastered",
        task: "ch. 17c",
        taskval: "95%" 
    },
    {
        learner: "Eric Y.",
        taskstatus: "mastered",
        task: "ch. 16b",
        taskval: "89%"  
    },
    {
        learner: "Bob B.",
        taskstatus: "struggling",
        task: "ch. 15b",
        taskval: "45%"
    },
    {
        learner: "Anne P.",
        taskstatus: "struggling",
        task: "ch. 17c",
        taskval: "60%"
    }

    ],
    group: "group 6b",
    weekhours: "4 hrs",
    exercisehours: "5.2 hrs"
};

var CoachSummaryView = BaseView.extend({

    template: HB.template("coach_nav/landing"),

    initialize: function() {
        _.bindAll(this);
        this.render();
    },

    render: function() {
        this.$el.html(this.template(data));

        var rp2 = radialProgress(document.getElementById('full_circle2'))
                .diameter(150)
                .value(81)
                .render();

        var rp3 = radialProgress(document.getElementById('full_circle3'))
                .diameter(150)
                .value(78)
                .render();

    }

});

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

var DetailPanelInlineRowView = BaseView.extend({

    tagName: 'tr',

    className: 'details-row',

    initialize: function(options) {
        this.contents_length = options.contents_length;
        this.content_item = options.content_item;
        this.render();
    },

    render: function() {
        this.detail_view = new detailsPanelView({
            tagName: 'td',
            model: this.model,
            content_item: this.content_item,
            attributes: {colspan: this.contents_length + 1}
        });
        this.$el.append(this.detail_view.el);
    }
})
        
var detailsPanelView = BaseView.extend({
    
    //Number of items to show from the collection
    limit: 4,
    
    template: HB.template("coach_nav/detailspanel"),
    
    initialize: function (options) {
        _.bindAll(this);
        this.content_item = options.content_item;
        if (this.content_item.get("kind") === "Exercise") {
            this.collection = new window.AttemptLogCollection([], {
                user: this.model.get("user"),
                limit: this.limit,
                exercise_id: this.model.get("exercise_id"),
                order_by: "timestamp"
            });
            this.collection.fetch();
        }
        this.listenToOnce(this.collection, "sync", this.render);
        this.render();
    },
    
    render: function() {
        var item_count = 0;
        if (this.collection.meta) {
            item_count = this.collection.meta.total_count;
        }
        this.pages = [];
        if (item_count/this.limit > 1) {
            for (var i=1; i < item_count/this.limit + 1; i++) {
                this.pages.push(i);
            }
        }
        this.$el.html(this.template({
            model: this.model.attributes,
            itemdata: this.content_item.attributes,
            pages: this.pages,
            collection: this.collection.to_objects()
        }));
        this.bodyView = new detailsPanelBodyView ({
            collection: this.collection,
            el: this.$(".body")
        });
    }
});


var detailsPanelBodyView = BaseView.extend({
    
    template: HB.template("coach_nav/detailspanelbody"),
    
    initialize: function (options) {
        _.bindAll(this);
        this.render();
    },
    
    render: function() {
        this.$el.html(this.template({
            collection: this.collection.to_objects()
        }));
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
            contents: this.contents.toJSON(),
            learners: this.contents.length
        }));
        var row_views = [];
        for (var i = 0; i < this.learners.length; i++) {
            var row_view = this.add_subview(TabularReportRowView, {model: this.learners.at(i), contents: this.contents})
            row_views.push(row_view);
            this.listenTo(row_view, "detail_view", this.set_detail_view);
        }
        this.append_views(row_views, ".student-data");
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
    },

    set_detail_view: function(detail_view) {
        if (this.detail_view) {
            this.detail_view.remove();
        }
        if (detail_view) {
            this.detail_view = detail_view;
        }
    }

});

var TabularReportRowView = BaseView.extend({

    template: HB.template("tabular_reports/tabular-view-row"),

    tagName: 'tr',

    initialize: function(options) {
        _.bindAll(this);

        this.contents = options.contents;
        this.render();
    },

    render: function() {
        this.$el.html(this.template(this.model.attributes));

        var cell_views = [];
        for (var i = 0; i < this.contents.length; i++) {
            var data = this.model.get("logs")[this.contents.at(i).get("id")];
            var new_view = this.add_subview(TabularReportRowCellView, {model: new Backbone.Model(data)});
            cell_views.push(new_view);
            this.listenTo(new_view, "detail_view", this.show_detail_view);
        }
        this.append_views(cell_views);
    },

    show_detail_view: function(model) {
        if (this.detail_view) {
            // TODO (rtibbles): Implement Models properly here to reflect server side id attributes
            if (this.detail_view.model.cid === model.cid) {
                delete this.detail_view;
                this.trigger("detail_view");
                return false
            }
            this.detail_view.remove();
        }


        var model_id = model.get("exercise_id") || model.get("video_id") || model.get("content_id");
        this.detail_view = new DetailPanelInlineRowView({
            model: model,
            contents_length: this.contents.length,
            content_item: this.contents.find(function(item) {return item.get("id") === model_id;})
        });
        this.$el.after(this.detail_view.el);

        this.trigger("detail_view", this.detail_view);

    }

});

var TabularReportRowCellView = BaseView.extend({

    tagName: 'td',

    events: {
        "click": "show_detail_view"
    },

    status_class: function() {
        var status_class = "partial";
        if (_.isEmpty(this.model.attributes)) {
            status_class = "not-attempted";
        } else if (this.model.get("complete")) {
            status_class = "complete";
        } else if (this.model.get("struggling")) {
            status_class = "struggling";
        }
        return status_class;
    },

    className: function() {
        return sprintf("status data %s", this.status_class());
    },

    title_attributes: {
        "not-attempted": gettext("Not Attempted"),
        "partial": gettext("Attempted"),
        "complete": gettext("Complete"),
        "struggling": gettext("Struggling")
    },

    attributes: function() {
        return {title: this.title_attributes[this.status_class()]};
    },

    initialize: function() {
        this.render();
    },

    render: function() {
        if (this.model.has("streak_progress")) {
            this.$el.html(this.model.get("streak_progress") + "%");
        }
    },

    show_detail_view: function() {
        if (_.isEmpty(this.model.attributes)) {
            return false;
        } else {
            this.trigger("detail_view", this.model);
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

var KMapEditor = {
    ZOOM_EXERCISES: 8,
    ZOOM_TOPICS: 6,
    ptaklist: {"1-digit addition": [0,0],
               "1-digit subtraction": [-15,0],
               "2-digit addition": [0,7],
               "2 and 3-digit subtraction": [-15,7]},
              

    exercises: null,
    maplayout: null,
    exercisesCompleted: null,

    raphael: {},

    minX: 0,
    minY: 0,
    maxX: 0,
    maxY: 0,
    zoomLevel: 0,

    X_SPACING: null,
    Y_SPACING: null,
    ICON_SIZE: null,
    LABEL_WIDTH: null,
    IMG_LIVE: null,
    IMG_DEV: null,
    IMG_SELECTED: null,
    IMG_SELECTED_DEV: null,
    IMG_NOT_STARTED: null,
    IMG_PARTIAL: null,
    IMG_COMPLETE: null,

    // exerciseData       /api/v1/exercises
    // defaultMapLayout   /api/v1/topicversion/default/maplayout
    init: function(exerciseData, defaultMapLayout, exercisesCompleted, zoom) {
        this.exercises = exerciseData;
        this.maplayout = defaultMapLayout;
        this.exercisesCompleted = exercisesCompleted;

        // Helper method to get exercise by name
        exerciseData.get = function(search) {
            var array = this;
            var index = _.memoize(function(id) {
                var idx = $.map(array, function(ex, n) {
                    if (ex.id === id) {
                        return n;
                    }
                });
                return idx[0];
            })(search);
            return this[index];
        };

        this.setZoom(zoom);

        this.drawMap();
    },

    setZoom: function(zoom) {
        this.zoomLevel = Math.min(Math.max(zoom, this.ZOOM_TOPICS), this.ZOOM_EXERCISES);
        if (this.zoomLevel === this.ZOOM_EXERCISES) {
            this.X_SPACING = 65;
            this.Y_SPACING = 105;
            this.ICON_SIZE = 26;
            this.LABEL_WIDTH = 60;
        } else if (this.zoomLevel === this.ZOOM_HYBRID) {
            this.X_SPACING = 32;
            this.Y_SPACING = 36;
            this.ICON_SIZE = 10;
            this.LABEL_WIDTH = 10;
        } else {
            this.X_SPACING = 16;
            this.Y_SPACING = 18;
            this.ICON_SIZE = 40;
            this.LABEL_WIDTH = 80;
        }
        this.IMG_LIVE = "/static/images/node-not-started-" + this.ICON_SIZE + ".png";
        this.IMG_DEV = "/static/images/node-not-started-" + this.ICON_SIZE + "-faded.png";
        this.IMG_SELECTED = "/static/images/node-complete-" + this.ICON_SIZE + ".png";
        this.IMG_SELECTED_DEV = "/static/images/node-complete-" + this.ICON_SIZE + "-faded.png";
        this.IMG_NOT_STARTED = "/static/images/node-not-started-" + this.ICON_SIZE + ".png";
        this.IMG_PARTIAL = "/static/images/node-partial-" + this.ICON_SIZE + ".png";
        this.IMG_COMPLETE = "/static/images/node-complete-" + this.ICON_SIZE + ".png";
    },

    createCanvas: function() {
        this.raphael = Raphael($("#map")[0]);

        if (this.zoomLevel === this.ZOOM_EXERCISES) {
            this.minX = Math.min.apply(Math, _.pluck(this.exercises, "h_position"));
            this.minY = Math.min.apply(Math, _.pluck(this.exercises, "v_position"));
            this.maxX = Math.max.apply(Math, _.pluck(this.exercises, "h_position"));
            this.maxY = Math.max.apply(Math, _.pluck(this.exercises, "v_position"));
        } else if (this.zoomLevel === this.ZOOM_TOPICS) {
            var topicList = _.values(this.maplayout.nodes);
            this.minX = Math.min.apply(Math, _.pluck(topicList, "h_position"));
            this.minY = Math.min.apply(Math, _.pluck(topicList, "v_position"));
            this.maxX = Math.max.apply(Math, _.pluck(topicList, "h_position"));
            this.maxY = Math.max.apply(Math, _.pluck(topicList, "v_position"));
        }
        console.log(this.maxX-this.minX);
        console.log(this.maxY-this.minY);

        this.raphael.setSize(
            (this.maxX - this.minX + 2) * this.X_SPACING,
            (this.maxY - this.minY + 2) * this.Y_SPACING
        );
        var temp=(this.maxX - this.minX + 2) * this.X_SPACING;
        console.log(temp);
        temp=(this.maxY - this.minY + 2) * this.Y_SPACING
         console.log(temp);

        $("#map-container").css("min-height", (this.maxY - this.minY) * this.Y_SPACING + 120);

        var mapHeight = $("#map-container").height();
        var mapWidth = $("#map-container").width();

        $("#map").css({
            "margin-left": mapWidth / 2 - (this.maxX - this.minX) * this.X_SPACING / 2,
            "margin-top": 30
        });
    },

    drawMap: function() {
        $("#map").empty();
        this.createCanvas();
       

        // add topics
        if (this.zoomLevel === this.ZOOM_TOPICS) {
            $.each(this.maplayout.nodes, function(topicId, topic) {
                console.log(topicId);
                var newDiv = $("<div>")
                    .addClass("exercise")
                    .css({
                        "left": (topic.h_position - KMapEditor.minX) * KMapEditor.X_SPACING,
                        "top": (topic.v_position - KMapEditor.minY) * KMapEditor.Y_SPACING,
                        "width": KMapEditor.LABEL_WIDTH
                    })
                    .appendTo($("#map"));

                var newTopic = $("<a>")
                    .attr("href", "/exercisedashboard/?topic=" + topicId)
                    .appendTo(newDiv);

                $("<img>")
                    .attr({
                        src: "/static" + topic.icon_url
                    })
                    .appendTo(newTopic);

                $("<div>")
                    .addClass("exercise exercise-label")
                    .css({"font-size": "12px", "width": "80px"})
                    .text(topic.title)
                    .appendTo(newTopic);
            });

            $.each(this.maplayout.polylines, function(topicId, polyline) {
                var path = "";
                $.each(polyline.path, function(n, coordinate) {
                    path += Raphael.format( "L{0},{1}",
                        (coordinate.x - KMapEditor.minX) * KMapEditor.X_SPACING + (KMapEditor.LABEL_WIDTH / 2),
                        (coordinate.y - KMapEditor.minY) * KMapEditor.Y_SPACING + 20)
                });
                path = "M" + path.substr(1);
                KMapEditor.raphael.path(path).attr({"stroke-width": 1, "stroke": "#999"});
            });
        }
        
        // add exercises
        if (this.zoomLevel === this.ZOOM_EXERCISES || this.zoomLevel === this.ZOOM_HYBRID) {
            _.each(this.exercises, function(ex) {
                if (ex.title in KMapEditor.ptaklist){ex.h_position=KMapEditor.ptaklist[ex.title][0];ex.v_position=KMapEditor.ptaklist[ex.title][1]};
                var newDiv = $("<div>")
                    .appendTo($("#map"))
                    .css({
                        "left": (ex.h_position - KMapEditor.minX) * KMapEditor.X_SPACING,
                        "top": (ex.v_position - KMapEditor.minY) * KMapEditor.Y_SPACING - KMapEditor.ICON_SIZE / 2,
                        "width": KMapEditor.LABEL_WIDTH
                    })
                    .addClass("exercise");
                var newEx = $("<a>")
                    .attr("href", ex.path)
                    .appendTo(newDiv);

                var image_src = KMapEditor.IMG_NOT_STARTED;
                if (KMapEditor.exercisesCompleted[ex.id] === "partial") {
                    image_src = KMapEditor.IMG_PARTIAL;
                } else if (KMapEditor.exercisesCompleted[ex.id] === "complete") {
                    image_src = KMapEditor.IMG_COMPLETE;
                }

                $("<img>")
                    .attr({
                        src: image_src,
                        width: KMapEditor.ICON_SIZE,
                        height: KMapEditor.ICON_SIZE
                    })
                    .addClass("exercise")
                    .addClass("ex-live")
                    .bind("dragstart", function(event) { event.preventDefault(); })
                    .appendTo(newEx);

                $("<div>")
                    .addClass("exercise exercise-label")
                    .css({"font-size": "12px", "width": "80px"})
                    .text(ex.title)
                    .css({"width": KMapEditor.LABEL_WIDTH + "px"})
                    .appendTo(newEx);
                    
                   //console.log(ex.title);  

                $.each(ex.prerequisites, function(n, prereq) {
                    KMapEditor.addPath(prereq, ex.id);
                });
                
            });
            
        }
        KMapEditor.addPath2([0,0],[-8,0],1); 
                        //console.log("just after");
    },

    addPath: function(src, dst) {
        //console.log(src);
        //console.log(dst);
        var src_ex = this.exercises.get(src);
        var dst_ex = this.exercises.get(dst);
        //console.log(src_ex);

        if (src_ex == null || dst_ex == null) {
            return;
        }

        this.raphael.path(
            Raphael.format("M{0},{1}L{2},{3}",
                (src_ex.h_position - this.minX) * this.X_SPACING + (this.LABEL_WIDTH / 2),
                (src_ex.v_position - this.minY) * this.Y_SPACING,
                (dst_ex.h_position - this.minX) * this.X_SPACING + (this.LABEL_WIDTH / 2),
                (dst_ex.v_position - this.minY) * this.Y_SPACING
        )).attr({
            "stroke-width": 1,
            "stroke": "#777"
        });
        console.log(src_ex.h_position+" "+src_ex.v_position);
        console.log(this.minX+" "+this.maxX);
        console.log(this.minY+" "+this.maxY);
        console.log(this.X_SPACING+" "+this.Y_SPACING);
        console.log(this.LABEL_WIDTH)
        },

    addPath2: function(from, to, scale) {
        
        //console.log(this.Y_SPACING + " " + this.X_SPACING);
        //console.log(this);

        this.raphael.path(
            Raphael.format("M{0},{1}l{2},{3}l{4},{5}L{6},{7}",
            0,0,0,390,390,0,0,0
            
            
                
        )).attr({
            "stroke-width": 5,
            "stroke": "#777"
        });
        this.raphael.path(
            Raphael.format("M{0},{1}l{2},{3}l{4},{5}L{6},{7}",
            0,0,390,0,0,390,0,0
            
            
                
        )).attr({
            "stroke-width": 5,
            "stroke": "#777"
        });
        this.raphael.path(
            Raphael.format("M{0},{1}l{2},{3}",
            195,195,195,-195
            
            
                
        )).attr({
            "stroke-width": 5,
            "stroke": "#777"
        });
        this.raphael.path(
            Raphael.format("M{0},{1}l{2},{3}",
            195,195,-195,195
            
            
                
        )).attr({
            "stroke-width": 5,
            "stroke": "#777"
        });
        this.raphael.path(
            Raphael.format("M{0},{1}l{2},{3}",
            195,195,200,0
            
            
                
        )).attr({
            "stroke-width": 5,
            "stroke": "#777"
        });
        this.raphael.path(
            Raphael.format("M{0},{1}l{2},{3}",
            195,195,-200,0
            
            
                
        )).attr({
            "stroke-width": 5,
            "stroke": "#777"
        });
        this.raphael.path(
            Raphael.format("M{0},{1}l{2},{3}",
            195,195,0,200
            
            
                
        )).attr({
            "stroke-width": 5,
            "stroke": "#777"
        });
        this.raphael.path(
            Raphael.format("M{0},{1}l{2},{3}",
            195,195,0,-200
            
            
                
        )).attr({
            "stroke-width": 5,
            "stroke": "#999"
        });
        
        tile=this.raphael.text(100,20,"KA Mothership").attr({
            "stroke-width": 1,
            "stroke": "#777",
            "font-size": 32,
            "fill": "#777",
            "font-family": "Arial, Helvetica, sans-serif",
            "href": "http://www.khanacademy.org",
            "target": "_blank"
        });
        
        tile.mouseover(function(e) {
        pX = e.pageX;
        pY = e.pageY;
        });
        tile.click(function() {
        console.log('x: '+pX+'| y:'+pY);
        this.attr({"font-size":16});
        });
        
        tile2=this.raphael.text(100,60,"Herb Gross").attr({
            "stroke-width": 1,
            "stroke": "#777",
            "font-size": 32,
            "fill": "#777",
            "font-family": "Arial, Helvetica, sans-serif",
            "href": "http://www.adjectivenounmath.com",
            "target": "_blank"
        });
        
        tile2.mouseover(function(e) {
        pX = e.pageX;
        pY = e.pageY;
        });
        tile2.click(function() {
        console.log('x: '+pX+'| y:'+pY);
        this.attr({"font-size":16});
        });
            
        console.log("this is the object");
        console.log(this);
        
        
        
    }
};

$(document).ready(function() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
        vars[key] = value;
    });
    
    if (!vars["topic"]) {
        // Top level of the topic tree
        $(".topic-button").hide();
        $.getJSON("/api/knowledge_map/root")
            .success(function(defaultMapLayout) {
                KMapEditor.init([], defaultMapLayout, {}, 6);
            });
    } else {
        // Second level of the topic tree
        $.getJSON("/api/knowledge_map/" + vars["topic"])
            .success(function(exerciseLayout) {

                var exercises = $.map(exerciseLayout.nodes, function(exercise) { return exercise });
                var exercise_ids = $.map(exerciseLayout.nodes, function(exercise) { return exercise.id });
                doRequest("/api/get_exercise_logs", exercise_ids)
                    .success(function(data) {
                        var exercisesCompleted = {};
                        $.each(data, function(ind, status) {
                            exercisesCompleted[status.exercise_id] = status.complete ? "complete" : "partial";
                        });
                        KMapEditor.init(exercises, [], exercisesCompleted, 8);
                        
                    })
                    .fail(function (resp) {
                        // Turned off because it duplicates "Progress not loaded" message
                        // communicate_api_failure(resp, "id_student_logs");
                        KMapEditor.init(exercises, [], [], 8);
                    });
                 
            });
            
    }
});

var KMapEditor = {
    ZOOM_EXERCISES: 8,
    ZOOM_TOPICS: 6,
    ptaklist: {"1-digit addition": [0,0],
               "1-digit subtraction": [-15,0],
               "2-digit addition": [0,7],
               "2 and 3-digit subtraction": [-15,7]},
               
    ptakidlist: {"addition_1": [0,0],
               "subtraction_1": [-15,0]},
               

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
                //if (ex.title in KMapEditor.ptaklist){ex.h_position=KMapEditor.ptaklist[ex.title][0];ex.v_position=KMapEditor.ptaklist[ex.title][1]};
                if (ex.id in KMapEditor.ptakidlist){ex.h_position=KMapEditor.ptakidlist[ex.id][0];ex.v_position=KMapEditor.ptakidlist[ex.id][1]};
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
            0,0,0,390,390,0,0,0)).attr(
            {"stroke-width": 5,
             "stroke": "#777"}).mouseover(function(e) {
             this.attr({"stroke-width": 10})}).mouseout(function(e){
             this.attr({"stroke-width":0, "fill": "#6bb6e8","opacity": 0.3})});
             
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
        
        wi = "m 100,190 -0.0667,-3.15742 -1.17911,-4.5265 -0.64664,-6.14309 -1.13162,-2.42491 0.96996,-3.07155 0.8083,-2.90989 1.45495,-2.58656 -0.64665,-3.39487 -0.64664,-3.55653 0.48498,-1.77827 1.93993,-2.42491 0.16166,-2.74823 -0.8083,-1.29328 0.64664,-2.58657 -0.45252,-4.17071 2.74823,-5.65811 2.90989,-6.78974 0.16166,-2.26325 -0.32332,-0.96996 -0.80831,0.48498 -4.20317,6.30476 -2.74823,4.04151 -1.93992,1.77827 -0.8083,2.26324 -1.95495,0.8083 -1.13162,1.93993 -1.45495,-0.32332 -0.16166,-1.77827 1.29329,-2.4249 2.10158,-4.68816 1.77827,-1.6166 0.99083,-2.35785 -2.56045,-1.90134 -1.97482,-10.36699 -3.54747,-1.34198 -1.94626,-2.30833 -12.12971,-2.72164 -2.87589,-1.01205 -8.21312,-2.16729 -7.91792,-1.15875 -3.76516,-5.13067 -0.7504,0.55401 -1.19791,-0.16166 -0.64665,-1.13162 -1.33401,0.29655 -1.13163,0.16166 -1.77826,0.96996 -0.96997,-0.64664 0.64665,-1.93993 1.93992,-3.07155 1.13162,-1.13162 -1.93992,-1.45494 -2.10159,0.8083 -2.90989,1.93992 -7.43638,3.23321 -2.90989,0.64664 -2.90988,-0.48498 -0.98173,-0.87825 -2.1167,2.83518 -0.22862,2.74347 0,8.45903 -1.14312,1.60037 -5.25832,3.88657 -2.28622,5.94419 0.45724,0.22862 2.51485,2.05761 0.68586,3.20072 -1.82898,3.20071 0,3.88659 0.45725,6.63005 2.97209,2.9721 3.42935,0 1.82898,3.20072 3.42933,0.45724 3.88659,5.71557 7.0873,4.11521 2.0576,2.74347 0.9145,7.43024 0.68586,3.31502 2.28623,1.60036 0.22862,1.37174 -2.0576,3.42933 0.22862,3.20073 2.51485,3.88658 2.51485,1.14311 2.97209,0.45724 1.34234,1.38012 45.29836,-2.66945 z";
        wimap=this.raphael.path(wi).attr({"fill":"#777","opacity": 0.5});
        il = "m 100,305 0.0312,-3.22971 0.56739,-4.64596 2.33253,-2.91586 1.86665,-4.07576 2.23302,-3.99533 -0.3715,-5.2524 -2.00521,-3.54257 -0.0964,-3.34668 0.69483,-5.26951 -0.82541,-7.17837 -1.06634,-15.77745 -1.29328,-15.01734 -0.92228,-11.6392 -0.27251,-0.92139 -0.8083,-2.58657 -1.29328,-3.71819 -1.61661,-1.77827 -1.45494,-2.58656 -0.23357,-5.48896 -45.79643,2.59825 0.22862,2.37195 2.28623,0.68587 0.91448,1.14311 0.45725,1.82898 3.88658,3.42934 0.68588,2.28623 -0.68588,3.42934 -1.82898,3.65796 -0.68586,2.51484 -2.28623,1.82899 -1.82898,0.68587 -5.25832,1.37173 -0.68587,1.82898 -0.68587,2.05761 0.68587,1.37174 1.82898,1.60036 -0.22862,4.1152 -1.82899,1.60036 -0.68586,1.60036 0,2.74347 -1.82898,0.45724 -1.60036,1.14312 -0.22862,1.37174 0.22862,2.0576 -1.71467,1.31457 -1.0288,2.80064 0.45724,3.65795 2.28623,7.31593 7.31593,7.54455 5.48693,3.65796 -0.22862,4.34383 0.9145,1.37174 6.40143,0.45724 2.74347,1.37174 -0.68586,3.65796 -2.28623,5.94419 -0.68587,3.20072 2.28622,3.88658 6.40144,5.25832 4.57246,0.68587 2.05759,5.0297 2.05761,3.20071 -0.91449,2.97209 1.60036,4.11521 1.82898,2.05761 1.41403,-0.88069 0.90766,-2.07479 2.21308,-1.7472 2.13147,-0.6144 2.60253,1.1798 3.62699,1.3757 1.18895,-0.29823 0.19987,-2.25845 -1.2873,-2.41179 0.30422,-2.37672 1.8384,-1.34745 3.02254,-0.81029 1.2609,-0.45852 -0.61261,-1.38688 -0.79137,-2.35437 1.4326,-0.98096 1.15747,-3.21403 z";
        ilmap=this.raphael.path(il).attr({"fill":"#777","opacity": 0.5});
        ilmap.scale(0.5,0.5,100,305);
        wimap.scale(0.5,0.5,100,305);
        
        //first text
        tile=this.raphael.text(100,20,"KA Mothership").attr({
            "stroke-width": 1,
            "stroke": "#777",
            "font-size": 12,
            "fill": "#777",
            "font-family": "Arial, Helvetica, sans-serif",
            "href": "http://www.khanacademy.org",
            "target": "_blank"
        });
        
        tile.mouseover(function(e) {
        pX = e.pageX;
        pY = e.pageY;
        this.attr({"font-size":24});
        }).mouseout(function(e){
        this.attr({"font-size":12});});
        tile.click(function() {
        console.log('x: '+pX+'| y:'+pY);
        this.attr({"font-size":16});
        });
        
        //second text
        tile2=this.raphael.text(100,60,"Herb Gross").attr({
            "stroke-width": 1,
            "stroke": "#777",
            "font-size": 12,
            "fill": "#777",
            "font-family": "Arial, Helvetica, sans-serif",
            "href": "http://www.adjectivenounmath.com",
            "target": "_blank"
        });
        
        tile2.mouseover(function(e) {
        pX = e.pageX;
        pY = e.pageY;
        this.attr({"font-size":24});
        }).mouseout(function(e){
        this.attr({"font-size":12});});
        tile2.click(function() {
        console.log('x: '+pX+'| y:'+pY);
        this.attr({"font-size":16});
        });
        
        //third text
        tile3=this.raphael.text(100,100,"We4DKids").attr({
            "stroke-width": 1,
            "stroke": "#777",
            "font-size": 12,
            "fill": "#777",
            "font-family": "Arial, Helvetica, sans-serif",
            "href": "http://www.we4dkids.com",
            "target": "_blank"
        });
        
        tile3.mouseover(function(e) {
        pX = e.pageX;
        pY = e.pageY;
        this.attr({"font-size":24});
        }).mouseout(function(e){
        this.attr({"font-size":12});});
        tile3.click(function() {
        console.log('x: '+pX+'| y:'+pY);
        this.attr({"font-size":16});
        });
        //tempmatrix=raphael.matrix(1,0,0,1,50,50);
        img1=this.raphael.image("temp.png", 0,0,50,50).attr({"opacity": 0.8});
        img1.translate(150,150).rotate(45,150,150);
        //img1.transform(tempmatrix);
            
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

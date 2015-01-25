$(function(){
window.statusModel.loaded.then(function() {
  var user_exercises_json;
  var url = setGetParamDict(K_MAP_URL, {
    user: statusModel.get("user_id"), 
    completion_timestamp__gte: '1001-10-20',
    completion_timestamp__lte: '3017-12-22'     //include all exerciselog
  }); 

  doRequest(url).success(function(user_json) {
    user_exercises_json = user_json;

  //create the hashtatble 
  var user_hashtable = {};
  for (var key in user_exercises_json["objects"]) {
    user_hashtable[user_exercises_json["objects"][key].exercise_id] = user_exercises_json["objects"][key];
  }

  // color-order: math_blue/sifi_scarlet/econ_orange/artist_red/cyber_green/test_purple/partner_emerald/college_pink
  var color_scheme_array = ["#1c758a","#94424f","#c78d46","#cf5044","#699c52","#644172","#49a88f","#e89cb9"];

  var width = window.innerWidth,
    height = window.innerHeight,
    root;

  var force = d3.layout.force()
    // .theta(.0001)
    // .alpha(0.1)
    .size([width, height]);

  $( ".kalite-navbar" ).after(function() {
    return "<kmap></kmap>";
  });

  function zoomHandler() {
    var label_translate = d3.event.translate;
    var label_scale = d3.event.scale;
    svg.attr("transform", "translate(" + label_translate + ")scale(" + label_scale + ")");
  }

  var svg = d3.select("kmap").append("svg")
    .attr("width", "100%")
    .attr("height", window.innerHeight - 180)
    .call(d3.behavior.zoom().scaleExtent([0.01, 30]).on("zoom", zoomHandler))
    .append("g");

  var link = svg.selectAll(".link"),
      node = svg.selectAll(".node");

  var subject_list = [];
  d3.json(sprintf(ALL_TOPICS_URL, {channel_name: "khan"}), function(error, json) {
      root = json;

      for(var c in root.children){
        subject_list[c] = root.children[c].slug;
      }
      update();
  });

  var loading = svg.append("text")
      .attr("x", width / 2)
      .attr("y", height / 2)
      .attr("dy", ".35em")
      .style("text-anchor", "middle")
      .text("Preparing the knowledge map based on your learning data...");

  var n_tick = 1;
  var links_table = {}; //for link look up
  var nodes;
  var unfold_scale_factor = 1;
  var scale_factor = 1; //for initial map size

  function update() {
    nodes = initial(root);
    if(nodes){
      unfold_scale_factor += nodes.length * 0.00005;
    }

    force.linkDistance(function(d){ 
      if(d.target.kind !== "Topic"){
        return  d.source.children.length * 1 + d.source.title.length * 1.5; 
      }else{
        return  d.source.children.length * 4 + d.target.title.length * 5; 
      }
    })
    .linkStrength(function(d){
      if(d.target.kind !== "Topic"){
        return 1;
      }else if(d.source.kind == "Subject"){
        return 7;
      }
      else{
        return 7.5;
      }
    })
    .charge(function(d){
      if(d.kind == "Exercise" || d.kind == "Video"){
        return -4000;
      }else if(d.kind == "Topic"){
        return d.title.length*(-2000);
      }else{
        return -70000;
      }
    })
    .chargeDistance(20000/unfold_scale_factor)
    .gravity(.912)
    .friction(0.2);

      nodes.pop(); //remove the root node since we don't want to render it.
      var links = d3.layout.tree().links(nodes);

      // Restart the force layout.
      force
          .nodes(nodes)
          .links(links)
          .start();

      // Update links.
      link = link.data(links, function(d) { return d.target.unique_id; });

      link.exit().remove();

      link.enter().insert("line", ".node")
      .attr("stroke-width", "2.5px")
      .attr("stroke", colorline);

      for(var l = 0; l < link[0].length; l++){
        links_table[link[0][l].__data__.source.slug + "," + link[0][l].__data__.target.slug] = link[0][l];
      }

      // Update nodes.
      node = node.data(nodes, function(d) { 
        return d.unique_id; 
      });

      node.exit().remove();

      var nodeEnter = node.enter().append("g")
          .attr("class", "node")
          .on("click", click)
          .on("mouseover", highlight_path)
          .on("mouseout", recover_highlight);

      n_tick = nodeEnter[0].length;
      // Use a timeout to allow the rest of the page to load first.
      setTimeout(function() {
        // Run the layout a fixed number of times.
        // The ideal number of times scales with graph complexity.
        // Of course, don't run too long—you'll hang the page!
        for (var i = n_tick * n_tick; i > 0; --i) force.tick();
        force.stop();

        link.attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

        node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
      }, 10);

      //this is not a very smooth way to do adaptive zooming
      if(n_tick <= subject_list.length){
       //don't zoom
      }else{
        if(n_tick < 40){
          scale_factor = 1.2;
        }else if(n_tick<100){
          scale_factor = 2;
        }else if(n_tick<400){
          scale_factor = 3;
        }else if(n_tick<1000){
          scale_factor = 4;
        }else if(n_tick<3000){
          scale_factor = 5;
        }
        var map = document.getElementsByTagName("svg")[0];

        map.setAttribute("viewBox", (map.getBBox().width - width*scale_factor/2) + " " +  (map.getBBox().height 
          - height*scale_factor/2) + " " + width*scale_factor +" "+ height*scale_factor); 

        loading.remove();
      }

      nodeEnter.append("circle")
          .attr("r", function(d) { 
            if(d.kind !== "Topic"){
            return d.size || 10; }});

      nodeEnter.append("rect")
          .attr("width", function(d) { 
            if(d.kind == "Topic"){
             if(d.title.length * 8 > 150){
                return d.title.length * 8/2 + 6;
              }else{
                return d.title.length * 8;
              }}})
          .attr("height", function(d) { 
            if(d.kind == "Topic"){
              if(d.title.length * 8 > 150){
                return 50;
              }else{
                return 30;
              }}})
          .attr("x",function(d) { 
            if(d.kind == "Topic"){
              if(d.title.length * 8 > 150){
                return d.title.length * -8/4 - 3;
              }else{
                return d.title.length * -8/2;
              }}})
          .attr("y", -17)
          .attr("rx", 10)
          .attr("ry", 10);

      node.select("rect")
          .attr("stroke-width", 4)
          .attr("stroke", colornode_stroke)
          .style("fill", colornode_fill);

      nodeEnter.append("text")
          .attr("dy", ".25em")
          .style("fill", init_text_fill)
          .style("font-size", "14")
          .text(function(d) { 
            if(d.kind == "Topic"){
              return d.title; 
            }
          })
          .call(text_wrap);

      nodeEnter.append("text")
          .attr("dy", function(d) { 
            if(d.title.length > 10){
              return "0.1em"; 
            }else{
              return "0.35em";
            }
          })
          .attr("y", -10)
          .style("font-size", "16")
          .style("font-weight", "bold")
          .style("fill", "white")
          .text(function(d) { 
            if(d.kind == "Subject"){
              return d.title + " " + "%" + d.progress.toFixed(2); 
            }
          })
          .call(text_wrap);

      node.select("circle")
          .attr("stroke-width", 4)
          .attr("stroke", colornode_stroke)
          .style("fill", colornode_fill);

      $(".node").tipsy({ 
        gravity: 'w',
        className: 'desc-tip',
        // fade: true,
        offset: 10,
        opacity: 0.7,
        html: true, 
        title: function() {
                var d = this.__data__;
                if(d.kind == 'Video'){
                  return '<span class="nameD-tip">' + d.title + '  </span>' + '<img src=' + "../images/knowledgemap/search-video-available.png" + '/>'; 
                }else if(d.kind == 'Exercise'){
                  return '<span class="nameD-tip">' + d.title + '  </span>' + '<img src=' + "../images/knowledgemap/search-exercise-available.png" + '/>'; 
                }else{
                  return '<span class="nameD-tip">' + d.title + '</span>';
                }
              } 
      });
  }

  function text_wrap(text){
    text.each(function() {
      var rect_width;
      if(d3.select(this).text().length * 8 > 150){
        rect_width = d3.select(this).text().length * 8/2 + 6;
      }else{
        rect_width = d3.select(this).text().length * 8;
      }

      var text = d3.select(this),
          words = text.text().split(/\s+/).reverse(),
          word,
          line = [],
          lineNumber = 0,
          lineHeight = 1, // ems
          y = text.attr("y"),
          dy = parseFloat(text.attr("dy")),
          tspan = text.text(null).append("tspan").attr("x", 0).attr("y", y).attr("dy", dy + "em");
      while (word = words.pop()) {
        line.push(word);
        tspan.text(line.join(" "));
        
        if (tspan.node().getComputedTextLength() > rect_width) {
          line.pop();
          tspan.text(line.join(" "));
          line = [word];
          tspan = text.append("tspan")
                    .attr("x", 0)
                    .attr("y", y)
                    .attr("dy", lineHeight + dy + "em")
                    .text(word);
          y = 7;
        }
      }
    });
  }

  function init_text_fill(d) {
      var subject_domain = d.path.split("/")[1];
      var color_code = subject_list.indexOf(subject_domain);
      var assigned_color = color_scheme_array[color_code];

      return d._children != null &&  d._children[0] != null ? "white" //    collapsed package
          : d.children ? assigned_color // expanded package
          : assigned_color;
  }

  function text_fill(d) {
      var subject_domain = d.path.split("/")[1];
      var color_code = subject_list.indexOf(subject_domain);
      var assigned_color = color_scheme_array[color_code];
      return d._children != null &&  d._children[0] != null ? assigned_color //    collapsed package
          : d.children ? "white" // expanded package
          : assigned_color;
  }

  function colornode_fill(d) {
      var subject_domain = d.path.split("/")[1];
      var color_code = subject_list.indexOf(subject_domain);
      var assigned_color = color_scheme_array[color_code];
      var d3_color = d3.rgb(assigned_color);
      return d._children &&  d._children[0] != null ? assigned_color //    collapsed package
          : d.children && d.kind != "Subject" ? "white" // expanded package
          : d.progress == 100 && !d.children ? assigned_color // completed leaf node
          : d.progress == 0 && !d.children ? "white"  // fresh leaf node
          : d.kind != "Subject" ? d3_color.brighter(1.9) // inprogress leaf node
          : assigned_color;
  }

  function colornode_stroke(d) {
      var subject_domain = d.path.split("/")[1];
      var color_code = subject_list.indexOf(subject_domain);
      var assigned_color = color_scheme_array[color_code];
      return assigned_color;
  }

  function colorline(d) {
    var subject_domain = d.source.path.split("/")[1];
    var color_code = subject_list.indexOf(subject_domain);
    var assigned_color = color_scheme_array[color_code];
    return assigned_color;
  }

  var highlight_recover_color;
  var recover_node_holder = [];
  var recover_link_holder = [];

  function highlight_path(d) {
    highlight_recover_color = d3.select(this).select("circle").attr("stroke");

    d3.select(this).select("circle")
      .attr("stroke", "#00FF00");
    d3.select(this).select("rect")
      .attr("stroke", "#00FF00");

    recover_node_holder.push(d3.select(this));

    var path_array = d.path.split("/");
    var source_curr;
    var target_curr;
    for (var i = 0; i < path_array.length -2; i++){
      target_curr = path_array[i];
      var matched_link = links_table[source_curr + ',' + target_curr];
      if(matched_link){
        matched_link.setAttribute("stroke", "#00FF00");
        recover_link_holder.push(matched_link);
      }
      source_curr = path_array[i];

      for( var n = 0; n < node[0].length; n++){
        if(path_array[i] == node[0][n].__data__.slug && node[0][n].__data__.kind !== "Video" && node[0][n].__data__.kind !== "Exercise"){
          node[0][n].getElementsByTagName("circle")[0].setAttribute("stroke", "#00FF00");
          node[0][n].getElementsByTagName("rect")[0].setAttribute("stroke", "#00FF00");
          recover_node_holder.push(node[0][n]);
        }
      }
    }
    matched_link = links_table[source_curr + ',' + d.slug];
    if(matched_link){
      matched_link.setAttribute("stroke", "#00FF00");
      recover_link_holder.push(matched_link);
    }
  }


  function recover_highlight(d){
    var end_link = recover_node_holder.shift();
    end_link.select("circle").attr("stroke", highlight_recover_color);
    end_link.select("rect").attr("stroke", highlight_recover_color);

    for(var h in recover_node_holder){
      recover_node_holder[h].getElementsByTagName("circle")[0].setAttribute("stroke", highlight_recover_color);
      recover_node_holder[h].getElementsByTagName("rect")[0].setAttribute("stroke", highlight_recover_color);
    }
    for(var j in recover_link_holder){
      recover_link_holder[j].setAttribute("stroke", highlight_recover_color);
    }
    recover_node_holder.length = 0;
    recover_link_holder.length = 0;
  }

  function click(d) {
    d.fixed = true;
    setTimeout(function(){ d.fixed = false; }, 3000);
    if (d3.event.defaultPrevented) return; // ignore drag
     
    if(d.kind !== "Topic" && d.kind !== "Subject"){
        location.href = "/learn/"+ d.path;
    }
  }

  var incr_id = 0;
  function initial(root) {
      var nodes = [], index = 0;
      function process_topics(node){
        if(node.children) node.children.forEach(process_topics);
        if(node.children){
          var topic_progress = 0;
          var unfold_flag = false;
          var inprogress_node_encounter = 0;
          var fresh_node_encounter = 0;
          var complete_node_encounter = 0;
          for(var i in node.children){

            //because same exercise can appear under different topics, use the path + kind to define a unique id
            // node.children[i]["unique_id"] = node.children[i].path + node.children[i].kind;
            node.children[i]["unique_id"] = incr_id;
            incr_id ++;

            if(node.children[i].progress){
              var progress_val = node.children[i].progress;
            }else{
              var progress_val = 0;
            }
          
            var match_hashtable = user_hashtable[node.children[i].id];
            if(match_hashtable){
              progress_val = match_hashtable.streak_progress;
            }
            //update topics.json's end node with personal streak_progress
            if(!node.children[i].children){
              node.children[i]["progress"] = progress_val;
            }

            topic_progress += progress_val;

            if(!node.children[i].children){
              if(progress_val == 100){
                complete_node_encounter++;
              }else if(progress_val == 0){
                fresh_node_encounter++;
              }else{
                inprogress_node_encounter++;
              }
            }
          }
          if(inprogress_node_encounter > 0){
            unfold_flag = true;
          }else if(complete_node_encounter != 0 && fresh_node_encounter != 0){
            unfold_flag = true;
          }
          var total_progress = node.children.length * 100;

          node["progress"] = topic_progress / total_progress * 100;

          node["unfold_flag"] = unfold_flag;
        }
      }
      process_topics(root);

      //prepare the subject nodes
      for(var y in root.children){
        root.children[y]["size"] = 50;   //make subject nodes larger
        root.children[y]["kind"] = "Subject";   //update the kind
        //prevent 100 or 0 progress subject node not shown #1
        if(root.children[y].progress == 100 || root.children[y].progress == 0){
          nodes.push(root.children[y]);
        }
      }

      function recurse(node) {
        if (node.children) node.children.forEach(recurse);
        if(node.children){
          if(node.unfold_flag){
            nodes.push(node)
            for(var t in node.children){
              nodes.push(node.children[t]);
            }
          }else if(node.progress != 0 && node.progress != 100){
            nodes.push(node);
          }
        }

        if (node.children && !node.unfold_flag){
          node["_children"] = [];
          for(var h = node.children.length -1; h >= 0 ; h--){
            if(node.children[h].progress == 0 || node.children[h].progress == 100){
              node._children.push(node.children[h]);
              node.children.splice(h, 1);
            }
          }
        }
      }
    recurse(root);

    //prevent 100 progress subject node not shown #2
    if(root._children){
      root.children = root.children.concat(root._children);
      root._children = null;
    }
    return nodes;
  }

  });
});
});
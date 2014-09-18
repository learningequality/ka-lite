//Modified from http://bl.ocks.org/mbostock/3887118
function d3_scatter(data, options, appendtohtml) {
  // Takes data in the form of an array of users' data.
  // Each user's data is an object with a user attribute,
  // containing an object of all user data, a userid attribute.
  // See scatter_view.js for more details.
  // xCoordinate and yCoordinate determine which items from the user data item will be used.
  // appendtohtml is the element identifier for the svg element to be attached to.

  // Set up variables to define plotting area.
  var margin = {top: 20, right: 40, bottom: 30, left: 100},
      width = 960 - margin.left - margin.right,
      height = 500 - margin.top - margin.bottom;

  // Initialize x and y scales.
  var x = d3.scale.linear()
      .range([0, width]);

  var xCoordinate = options['hAxis']['stat'];

  var y = d3.scale.linear()
      .range([height, 0]);

  var yCoordinate = options['vAxis']['stat'];

  var color = d3.scale.category10();

  var xAxis = d3.svg.axis()
      .scale(x)
      .orient("bottom")
      .ticks(5);

  var yAxis = d3.svg.axis()
      .scale(y)
      .orient("left")
      .ticks(5);
  

  // Create svg object for plot area
  var svg = d3.select(appendtohtml).append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
  
  // Create tooltip object for displaying user specific information
  var tooltip = d3.select("body").append("div")
        .style("visibility", "hidden")
        .attr("id", "summary");
  
  // Set x and y range
  x.domain([0, 100]);
  y.domain([0, 100]);
  
  // Click anywhere on SVG object to hide tooltip
  svg.on("click", function() {
    tooltip.style("visibility", "hidden");
  });
  
  // Create invisible background rectangle to catch any clicks that are not
  // on data points in the plot area. Allows for 'clicking off' the tooltip.
  svg.append("rect")
      .attr("x", 0)
      .attr("y", 0)
      .attr("width", width)
      .attr("height", height)
      .attr("opacity", 0);


  // Create four different rectangles to highlight and label the different quadrants of the graph.
  // Each rectangle is a group with a coloured (fill) rectangle, and a text label.
  var struggling = svg.append("g");
  struggling.append("rect")
    .attr("class", "quadrant-rectangle")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", width/2)
    .attr("height", height/2)
    .attr("fill", "#FF0000");
  struggling.append("text")
    .attr("class", "quadrant-label")
    .attr("x", width/4)
    .attr("y", height/4)
    .text(gettext("Struggling"));

  var bored = svg.append("g");
  bored.append("rect")
    .attr("class", "quadrant-rectangle")
    .attr("x", width/2)
    .attr("y", height/2)
    .attr("width", width/2)
    .attr("height", height/2)
    .attr("fill", "#000000");
  bored.append("text")
    .attr("class", "quadrant-label")
    .attr("x", 3*width/4)
    .attr("y", 3*height/4)
    .text(gettext("Bored"));

  var disengaged = svg.append("g");
  disengaged.append("rect")
    .attr("class", "quadrant-rectangle")
    .attr("x", 0)
    .attr("y", height/2)
    .attr("width", width/2)
    .attr("height", height/2)
    .attr("fill", "#FFFF00");
  disengaged.append("text")
    .attr("class", "quadrant-label")
    .attr("x", width/4)
    .attr("y", 3*height/4)
    .text(gettext("Disengaged"));

  var ontarget = svg.append("g");
  ontarget.append("rect")
    .attr("class", "quadrant-rectangle")
    .attr("x", width/2)
    .attr("y", 0)
    .attr("width", width/2)
    .attr("height", height/2)
    .attr("fill", "#00FF00");
  ontarget.append("text")
    .attr("class", "quadrant-label")
    .attr("x", 3*width/4)
    .attr("y", height/4)
    .text(gettext("On Target"));

  // Create and draw x and y axes
  svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height/2 + ")")
      .call(xAxis)
    .append("text")
      .attr("class", "label")
      .attr("font-weight", "bold")
      .attr("x", width)
      .attr("y", -6)
      .style("text-anchor", "end")
      .text(options['hAxis']['title']);

  svg.append("g")
      .attr("class", "y axis")
      .attr("transform", "translate(" + width/2 + ",0)")
      .call(yAxis)
    .append("text")
      .attr("class", "label")
      .attr("font-weight", "bold")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", ".71em")
      .style("text-anchor", "end")
      .text(options['vAxis']['title']);


  // Plot all data points
  svg.selectAll(".dot")
      .data(data)
    .enter().append("circle")
      .attr("class", "dot")
      .attr("r", 3.5)
      .attr("cx", function(d) { return x(d[xCoordinate]); })
      .attr("cy", function(d) { return y(d[yCoordinate]); })
      .style("fill", "black")
      // Add invisible stroke border to increase the effective area of the data point.
      .style("stroke-width", "10")
      .style("stroke", "black")
      .style("stroke-opacity", "0")
      .style("cursor", "pointer")
      // Define click behaviour
      .on("click", function(d) {
        // Prevent svg click behaviour of hiding tooltip from happening
        d3.event.stopPropagation();
        // Show tooltip if it is currently hidden
        if(tooltip.style("visibility")=="hidden") {
          tooltip.html(d["tooltip"])
            .style("visibility", "visible")
            .style("left", (d3.event.pageX) + "px")     
            .style("top", (d3.event.pageY - 28) + "px");
          // Mark this item as having the tooltip
          d3.select(this).attr("tooltip", true);
        } else {
          // Hide tooltip if already open for this item
          if(d3.select(this).attr("tooltip")=="true") {
            tooltip.style("visibility", "hidden");
          } else {
            // Otherwise unflag other point as tooltip
            svg.selectAll(".dot").attr("tooltip", false);
            // Flag this item with tooltip
            d3.select(this).attr("tooltip", true);
            // Change tooltip information to this point
            tooltip.html(d["tooltip"])
              // Position tooltip based on data point
              // TODO: Intelligently position tooltip when near the edge
              // of the plot area to prevent overflow.
              .style("left", (d3.event.pageX) + "px")     
              .style("top", (d3.event.pageY - 28) + "px");
          }
        }
      })
      // Animate and grow data point on mouseover.
      .on("mouseover", function(d) {
        d3.select(this).transition()
        .attr("r", 13.5)
        .attr("stroke-width", 0)
        .duration(500)
        .ease("elastic",2,0.5);
      })
      // Shrink back on mouseout.
      .on("mouseout", function(d) {
        d3.select(this).transition()
        .attr("r", 3.5)
        .attr("stroke-width", 10);
      })
      // Add user name as hover text.
      .append("svg:title")
      .text(function(d) { return d["user"]; });

}

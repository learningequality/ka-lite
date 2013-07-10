//Modified from http://bl.ocks.org/mbostock/3887118
function d3_scatter(data, xCoordinate, yCoordinate, appendtohtml) {
  // Takes data in the form of an array of users' data.
  // Each user's data is an object with a user attribute,
  // containing an object of all user data, a userid attribute.
  // See scatter_view.js for more details.
  // xCoordinate and yCoordinate determine which items from the user data item will be used.
  // appendtohtml is the element identifier for the svg element to be attached to.

  // Set up variables to define plotting area.
  var margin = {top: 20, right: 20, bottom: 30, left: 40},
      width = 960 - margin.left - margin.right,
      height = 500 - margin.top - margin.bottom;

  // Initialize x and y scales.

  var x = d3.scale.linear()
      .range([0, width]);

  var y = d3.scale.linear()
      .range([height, 0]);

  var color = d3.scale.category10();

  var xAxis = d3.svg.axis()
      .scale(x)
      .orient("bottom");

  var yAxis = d3.svg.axis()
      .scale(y)
      .orient("left");
  

  // Create svg object for plot area
  var svg = d3.select(appendtohtml).append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
  
  // Create tooltip object for displaying user specific information
  var tooltip = d3.select("body").append("div")
        .style("visibility", "hidden")
        .attr("id", "summary")
  
  // Set x and y range
  x.domain(d3.extent(data, function(d) { return d[xCoordinate]; })).nice();
  y.domain(d3.extent(data, function(d) { return d[yCoordinate]; })).nice();
  
  // Click anywhere on SVG object to hide tooltip
  svg.on("click", function() {
    tooltip.style("visibility", "hidden");
  })
  
  // Create invisible background rectangle to catch any clicks that are not
  // on data points in the plot area. Allows for 'clicking off' the tooltip.
  svg.append("rect")
      .attr("x", 0)
      .attr("y", 0)
      .attr("width", width)
      .attr("height", height)
      .attr("opacity", 0)
  
  // Create and draw x and y axes
  svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis)
    .append("text")
      .attr("class", "label")
      .attr("x", width)
      .attr("y", -6)
      .style("text-anchor", "end")
      .text(xCoordinate);

  svg.append("g")
      .attr("class", "y axis")
      .call(yAxis)
    .append("text")
      .attr("class", "label")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", ".71em")
      .style("text-anchor", "end")
      .text(yCoordinate)


  // Plot all data points
  svg.selectAll(".dot")
      .data(data)
    .enter().append("circle")
      .attr("class", "dot")
      .attr("r", 3.5)
      .attr("cx", function(d) { return x(d[xCoordinate]); })
      .attr("cy", function(d) { return y(d[yCoordinate]); })
      .style("fill", "black")
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
      // Add user name as hover text.
      .append("svg:title")
      .text(function(d) { return d["user"]; });

}
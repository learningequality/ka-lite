// Modified from http://bl.ocks.org/mbostock/3884955

function d3_multiTimeSeries (data, timeScale, appendtohtml) {
    // Takes data in the form of an array of users' data.
    // Each user's data is an object with a name attribute,
    // and a values attribute, containing an array of objects
    // each with a Date and pctmastery attribute. See timeline_view.js for more details.
    // timeScale is a collection of all Date objects in data for scaling the x-axis.
    // appendtohtml is the element identifier for the svg element to be attached to.

    // Set up variables to define plotting area.
    var margin = {top: 20, right: 80, bottom: 30, left: 50},
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    // Initialize x and y scales.
    var x = d3.time.scale()
        .range([0, width]);

    var y = d3.scale.linear()
        .range([height, 0]);

    // TODO: Dynamic Color Ranging based on number of students
    var color = d3.scale.category20();

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left");

    // Create object to plot line
    var line = d3.svg.line()
        .interpolate("basis")
        .x(function(d) { return x(d.date); })
        .y(function(d) { return y(d.pctmastery); });

    // Create svg object
    var svg = d3.select(appendtohtml).append("svg")
        .attr("width", width + margin.left + margin.right + 75)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Set range of x, y, and line colors

    color.domain(data.map(function(obj) { return obj["name"]; }));

    x.domain(d3.extent(timeScale));


    //TODO dynamically range based on values
    y.domain([0, 100]);
    //   d3.min(data, function(c) { return d3.min(c.values, function(v) { return v.pctmastery; }); }),
    //   d3.max(data, function(c) { return d3.max(c.values, function(v) { return v.pctmastery; }); })
    // ]);

    // Add x and y axes

    svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis);

    svg.append("g")
      .attr("class", "y axis")
      .call(yAxis)
    .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", ".71em")
      .style("text-anchor", "end")
      .text("pctmastery");

    // Feed data into user object

    var user = svg.selectAll(".user")
      .data(data)
    .enter().append("g")
      .attr("class", "user");

    // Draw lines

    user.append("path")
      .attr("class", "line")
      .attr("d", function(d) { return line(d.values); })
      .attr("username", function(d) {return d.name.replace(", ","");})
      .style("stroke", function(d) { return color(d.name); })
      .append("svg:title")
      .text(function(d) { return d.name; });

    // Draw legend box to the right of the plot area.

    var legend = svg.selectAll(".legend")
      .data(color.domain())
    .enter().append("g")
      .attr("class", "legend")
      .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; })      
      .on("mouseover", function(d) {
          d3.select('[username=' + d.replace(", ","") + ']').style("stroke-width", 5);
      })
      .on("mouseout", function(d) {
          d3.select('[username=' + d.replace(", ","") + ']').style("stroke-width", 1.5);
      });

    // Draw a box and text for each user

    legend.append("rect")
      .attr("x", width + 108)
      .attr("width", 18)
      .attr("height", 18)
      .style("fill", color);

    legend.append("text")
      .attr("x", width + 102)
      .attr("y", 9)
      .attr("dy", ".35em")
      .style("text-anchor", "end")
      .text(function(d) { return d; });
}
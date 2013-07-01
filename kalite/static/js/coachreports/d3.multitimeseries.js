// Modified from http://bl.ocks.org/mbostock/3884955

function d3_multiTimeSeries (data, timeScale, appendtohtml) {
    var margin = {top: 20, right: 80, bottom: 30, left: 50},
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    var parseDate = d3.time.format("%Y%m%d").parse;

    var x = d3.time.scale()
        .range([0, width]);

    var y = d3.scale.linear()
        .range([height, 0]);

    console.log(data);

    // TODO: Dynamic Color Ranging based on number of students
    var color = d3.scale.category20();

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left");

    var line = d3.svg.line()
        .interpolate("basis")
        .x(function(d) { return x(d.date); })
        .y(function(d) { return y(d.pctmastery); });

    var svg = d3.select(appendtohtml).append("svg")
        .attr("width", width + margin.left + margin.right + 75)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    color.domain(data.map(function(obj) { return obj["name"]; }));

    x.domain(d3.extent(timeScale));

    y.domain([0, 100]);
    //   d3.min(data, function(c) { return d3.min(c.values, function(v) { return v.pctmastery; }); }),
    //   d3.max(data, function(c) { return d3.max(c.values, function(v) { return v.pctmastery; }); })
    // ]);

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

    var user = svg.selectAll(".user")
      .data(data)
    .enter().append("g")
      .attr("class", "user");

    user.append("path")
      .attr("class", "line")
      .attr("d", function(d) { return line(d.values); })
      .attr("username", function(d) {return d.name.replace(", ","");})
      .style("stroke", function(d) { return color(d.name); })
      .append("svg:title")
      .text(function(d) { return d.name; });

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
//Modified from http://bl.ocks.org/mbostock/3887118
function d3_scatter(data, xCoordinate, yCoordinate, appendtohtml) {
  
  var margin = {top: 20, right: 20, bottom: 30, left: 40},
      width = 960 - margin.left - margin.right,
      height = 500 - margin.top - margin.bottom;

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
  
  var svg = d3.select(appendtohtml).append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
  
  var tooltip = d3.select("body").append("div")
        .style("visibility", "hidden")
        .attr("id", "summary")
  
  x.domain(d3.extent(data, function(d) { return d[xCoordinate]; })).nice();
  y.domain(d3.extent(data, function(d) { return d[yCoordinate]; })).nice();
  
  svg.on("click", function() {
    tooltip.style("visibility", "hidden");
  })
  
  svg.append("rect")
      .attr("x", 0)
      .attr("y", 0)
      .attr("width", width)
      .attr("height", height)
      .attr("opacity", 0)
  
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

  svg.selectAll(".dot")
      .data(data)
    .enter().append("circle")
      .attr("class", "dot")
      .attr("r", 3.5)
      .attr("cx", function(d) { return x(d[xCoordinate]); })
      .attr("cy", function(d) { return y(d[yCoordinate]); })
      .style("fill", "black")
      .on("click", function(d) {
        d3.event.stopPropagation();
        if(tooltip.style("visibility")=="hidden") {
          tooltip.html(d["tooltip"])
            .style("visibility", "visible")
            .style("left", (d3.event.pageX) + "px")     
            .style("top", (d3.event.pageY - 28) + "px");
          d3.select(this).attr("tooltip", true);
          console.log(d3.event.pageX);
          console.log(d3.event.pageY);
        } else {
          if(d3.select(this).attr("tooltip")=="true") {
            tooltip.style("visibility", "hidden");
          } else {
            svg.selectAll(".dot").attr("tooltip", false);
            d3.select(this).attr("tooltip", true);
            tooltip.html(d["tooltip"])
              .style("left", (d3.event.pageX) + "px")     
              .style("top", (d3.event.pageY - 28) + "px");
          }
        }
      })
      .append("svg:title")
      .text(function(d) { return d["user"]; });

  var legend = svg.selectAll(".legend")
      .data(color.domain())
    .enter().append("g")
      .attr("class", "legend")
      .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

  legend.append("rect")
      .attr("x", width - 18)
      .attr("width", 18)
      .attr("height", 18)
      .style("fill", color);

  legend.append("text")
      .attr("x", width - 24)
      .attr("y", 9)
      .attr("dy", ".35em")
      .style("text-anchor", "end")
      .text(function(d) { return d; });
}
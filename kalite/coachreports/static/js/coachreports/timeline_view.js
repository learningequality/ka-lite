function drawChart_timeline(chart_div, dataTable, timeScale, options) {
    d3_multiTimeSeries(dataTable, timeScale, chart_div, options);
}

function json2dataTable_timeline(json, xaxis, yaxis) {
    var dataTable = [];
    var timeScale = [];

    nobjects = json['objects'].length;

    var multiplier = 1;

    multiplier = 100/nobjects;

    for (var s in json['objects']){
        var curr_s = json['objects'][s]['exercises'];
        var data_array = {};
        data_array["name"] = json['objects'][s]['user_name'];

        var values = [];

        for (var k in curr_s){
            var curr_k = curr_s[k];
            timeScale.push(new Date(curr_k[xaxis]));
            values.push({
                date: new Date(curr_k[xaxis]), data_point: multiplier*curr_k[yaxis]
            });
        }

        data_array["values"] = values;
        dataTable.push(data_array);
    }
    return [dataTable, timeScale];
  }

function drawJsonChart_timeline(chart_div, json, xaxis, yaxis) {
    var options = {
      title: stat2name(xaxis) + ' vs. ' + stat2name(yaxis) + ' comparison',
      hAxis: {title: "The Exercises Completed", stat: xaxis },
      vAxis: {title: "Mastery", stat: yaxis }
    };
    var data = json2dataTable_timeline(json, xaxis, yaxis);
    var dataTable = data[0];
    var timeScale = data[1];
    if (timeScale.length > 1){
        drawChart_timeline(chart_div, dataTable, timeScale, options);
    } else {
        show_message("info", gettext("Not enough data to show timeline."));
    }
}

function drawJsonChart(chart_div, json, xaxis, yaxis) {
    // Main interface
    drawJsonChart_timeline(chart_div, json, xaxis, yaxis);
}


function drawChart_timeline(chart_div, dataTable, timeScale, options) {
    d3_multiTimeSeries(dataTable, timeScale, chart_div, options);
}

function json2dataTable_timeline(json, xaxis, yaxis) {
    // Given a dictionary, create a data table, one row at a time.
    // console.log("loglog1: ", xaxis);
    // console.log("loglog2: ", yaxis);
    // console.log("loglog3: ", json['objects']);
    console.log("fffffff: ", json['objects']);
    
    var dataTable = [];
    var timeScale = [];

    // nusers = Object.keys(json['objects']).length;
    // console.log("loglog3: ", nusers);

    nobjects = json['objects'].length;
    console.log("loglog66: ", nobjects);
    console.log("loglog4: ", new Date(json['objects'][1]['exercises'][0][xaxis]));
    // return null;

    var multiplier = 1;

    multiplier = 100/32;

    for (var s in json['objects']){
        var curr_s = json['objects'][s]['exercises'];
     //   console.log("haha1: ", curr_s); //each user with all the timelog
        var data_array = {};
        data_array["name"] = json['objects'][s]['user_name'];

        var values = [];

        for (var k in curr_s){
            var curr_k = curr_s[k];
     //       console.log("haha2: ", curr_k);  //each timelog and mstered
            timeScale.push(new Date(curr_k[xaxis]));
            values.push({
                date: new Date(curr_k[xaxis]), data_point: multiplier*curr_k[yaxis]
            });
        }

        data_array["values"] = values;
        // for(var i = 0; i < 2; i++){
        //     timeScale.push(new Date(curr_s[i][xaxis]));
        // }
        dataTable.push(data_array);
    }
    // console.log("elieli dataTable: ", dataTable);
    // console.log("elieli timeScale: ", timeScale);
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


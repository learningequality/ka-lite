function drawChart_timeline(chart_div, dataTable, timeScale, options) {
    d3_multiTimeSeries(dataTable, timeScale, chart_div);
}

function json2dataTable_timeline(json, xaxis, yaxis) {
    // Given a dictionary, create a data table, one row at a time.
    
    var dataTable = [];

    nusers = Object.keys(json['data']).length;

    nobjects = json['exercises'].length || json['videos'].length;

    var timeScale = []
    
    for (var ui=0; ui<nusers; ++ui) {
        var uid = Object.keys(json['data'])[ui];

        var good_xdata = [];
        var good_ydata = []
        var all_xdata = json['data'][uid][xaxis];
        for (var ri in all_xdata) {
            var xdata = all_xdata[ri];
            if (xdata == null) {
                continue;
            }
            good_xdata.push(new Date(xdata));
            timeScale.push(new Date(xdata));
            good_ydata.push( good_ydata.length + 1 );
        }

        // Now create a data table
        var data_array = {};

        data_array["name"] = json["users"][uid]

        var values = []
        
        for (ri=0; ri<good_xdata.length; ++ri) {

            values.push({
                date: good_xdata[ri], pctmastery: 100*good_ydata[ri]/nobjects
            })
        }
        
        data_array["values"] = values;
        
        dataTable.push(data_array);
    }
    return [dataTable, timeScale];
  }

function drawJsonChart_timeline(chart_div, json, xaxis, yaxis) {
    var options = {
      title: stat2name(xaxis) + ' vs. ' + stat2name(yaxis) + ' comparison',
      hAxis: {title: stat2name(xaxis) },
      vAxis: {title: stat2name(yaxis) },
    };
    var data = json2dataTable_timeline(json, xaxis, yaxis);
    var dataTable = data[0];
    var timeScale = data[1];
    return drawChart_timeline(chart_div, dataTable, timeScale, options);
}

function drawJsonChart(chart_div, json, xaxis, yaxis) {
    // Main interface
    drawJsonChart_timeline(chart_div, json, xaxis, yaxis);
}


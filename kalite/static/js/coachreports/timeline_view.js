function drawChart_timeline(chart_div, dataTable, timeScale, options) {
    d3_multiTimeSeries(dataTable, timeScale, chart_div);
}


// Taken from https://gist.github.com/onpubcom/1772996
function date_sort_asc (date1, date2) {
  // This is a comparison function that will result in dates being sorted in
  // ASCENDING order. As you can see, JavaScript's native comparison operators
  // can be used to compare dates. This was news to me.
  if (date1 > date2) return 1;
  if (date1 < date2) return -1;
  return 0;
};

function json2dataTable_timeline(json, xaxis, yaxis) {
    // Given a dictionary, create a data table, one row at a time.
    
    // var parseDate = d3.time.format("%Y%m%d").parse;
    
    console.log(json);
    
    var dataTable = [];

    nusers = Object.keys(json['data']).length;
    
    nexercises = json['exercises'].length;

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

        good_xdata.sort(date_sort_asc);

        // Now create a data table
        var data_array = {};

        data_array["name"] = json["users"][uid]

        var values = []
        
        for (ri=0; ri<good_xdata.length; ++ri) {

            values.push({
                date: good_xdata[ri], pctmastery: 100*good_ydata[ri]/nexercises
            })
        }
        
        data_array["values"] = values;
        
        dataTable.push(data_array);
    }
    timeScale.sort(date_sort_asc);
    return [dataTable, timeScale];
  }

function user2tooltip_timeline(json, uid, xaxis, yaxis) {
    // A very simple tooltip that seems not to be used.
    var html = "<div class='tooltip'>" + json["users"][uid] + "</div>";
    return html;
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


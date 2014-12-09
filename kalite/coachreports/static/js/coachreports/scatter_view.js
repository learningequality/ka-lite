function drawChart(chart_div, dataTable, options) {
    // Used for Google visualizations
    options["legend"] = 'none';
    options["tooltip"] = { isHtml: 'true', trigger: 'selection' };
    d3_scatter(dataTable, options, chart_div);
}

function obj2num(row, stat, json) {
    // This takes a stat--either a number or a dictionary of numbers--
    //    and turns it into a single number or an array of numbers.
    var type = stat2type(stat);
    var xdata = (type=="number") ? 0 : new Date();
    if (typeof row == 'number') {
        xdata = 0+row;
    } else {
        for (var d in row) {
            switch (stat) {
                case "ex:streak_progress": // compute an average
                    xdata += row[d]/json['exercises'].length;
                    break;
                case "ex:points":
                    xdata += row[d];
                    break;
                case "ex:attempts":
                    xdata += row[d]/json['exercises'].length;
                    break;
                    
                // Special case for timestamps, where we want a time series, not a single value.
                case "ex:completion_timestamp":
                    if (row[d] != null && xdata > (new Date(row[d]))) {
                        xdata = new Date(row[d]);
                    }
                    break;
                default:
                    xdata += row[d];
                    break;
            }
        }
    }
    return xdata;
}

function json2dataTable(json, xaxis, yaxis) {
    // Given a dictionary, create a data table, one row at a time.
    var dataTable = [];

    // for (var user in json["data"]) {
    //     var entry = json["data"][user];
    //     entry["user"] = json['users'][user];
    //     entry["userid"] = user;
    //     entry["tooltip"] = user2tooltip(json, user, xaxis, yaxis);
    //     entry[xaxis] = obj2num(entry[xaxis], xaxis, json);
    //     entry[yaxis] = obj2num(entry[yaxis], yaxis, json);
    //     dataTable.push(entry);
    // }
    for (var user in json["objects"]) {
        var entry = [];
        entry["userid"] = user;
        entry["tooltip"] = user2tooltip(json, user, json["objects"][user]["total_attempts"], json["objects"][user]["mastered"]);

        entry[xaxis] = json["objects"][user]["mastered"];
        entry[yaxis] = json["objects"][user]["total_attempts"];
       
        dataTable.push(entry);
    }
    return dataTable;
  }

function tablifyThis(ex_data) {
    // I guess this generates small tables?
    var table = "<table class='detail'>";
    for (var i in ex_data) {
        var ex = ex_data[i];
        table += "<tr><td><a href='" + ex["url"] + "'>" + ex["name"] + "</a></td><td class='data'>" + ex["num"] + " attempts</td>";
    }
        
    table += "</table>";
    return table;
}

function user2tooltip(json, user, xaxis, yaxis) {
    // Creating a HTML blob for the tooltip that shows when a user's is clicked.
    var axes = [xaxis];
    var exercises = json["objects"][user]["exercises"];
    var videos = json['videos'];
    var tooltip = "<div class='usertooltip'>";

    var struggling = "<div class='struggling'>";
    var attempted = "<div class='attempted'>";
    var struggles = [];
    var attempts = [];
    tooltip += "<div id='legend'><div class='username'>" + json["objects"][user]["user_name"] + "</div><div class='legend'><div class='struggling'></div>Struggling</div><div class='legend'><div class='notattempted'></div>Not Attempted</div><div class='legend'><div class='attempted'></div>Attempted</div></div>";
    for (var i in exercises){
        if(exercises[i].struggling){
            struggles.push({
                "num": exercises[i].attempts,
                "name": exercises[i].exercise_id,
                "url": exercises[i].exercise_url
            });
        }else{
            attempts.push({
                "num": exercises[i].attempts,
                "name": exercises[i].exercise_id,
                "url": exercises[i].exercise_url
            });
        }
    }
    struggling += tablifyThis(struggles) + "</div>"; 
    attempted += tablifyThis(attempts) + "</div>"; 
    tooltip += struggling + attempted;

    tooltip += "</div>";

    return tooltip;
}

function drawJsonChart(chart_div, json, xaxis, yaxis) {
    // The main function, required by our Google Visualization interface
    var options = {
      title: stat2name(xaxis) + ' vs. ' + stat2name(yaxis) + ' comparison',
      hAxis: {title: stat2name(xaxis), stat: xaxis},
      vAxis: {title: stat2name(yaxis), stat: yaxis}
    };
    var dataTable = json2dataTable(json, xaxis, yaxis);
    $("#summary").remove();
    drawChart("#chart_div", dataTable, options);
}

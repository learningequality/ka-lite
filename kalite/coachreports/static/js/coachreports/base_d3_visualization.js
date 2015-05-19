// Scripts for mapping our stats into text names and Google vis types.
function stat2name(stat) {
    var children = $("#xaxis option");
    for (var opt in children) {
        if (children[opt].value == stat) {
            return children[opt].text;
        }
    }

    var children = $("#yaxis option");
    for (var opt in children) {
        if (children[opt].value == stat) {
            return children[opt].text;
        }
    }
    return null;
}

function plotJsonData(chart_div, base_url, props) {
    /* Called whenever json data blob returns (via AJAX)
       NOTE: you have to implement drawJsonChart(chart_div, json, xaxis, yaxis); */

    // Scrub data
    // if (!props["user"])       { props["user"]       = FORM_USER; }
    // if (!props["topic_path"]) { props["topic_path"] = FORM_TOPIC_PATH; }

    // if (!props["xaxis"] || !props["yaxis"] || !props["topic_path"] || props["topic_path"].length == 0) { // one of the ---- is selected
    //     return false;
    // }

    // Get the data
    var url = base_url + "?" + $.param(props, true); 

    clear_messages();
    doRequest(url)
        .success(function(json) {
            $("#loading").text(sprintf(gettext("Drawing %(xaxis_name)s versus %(yaxis_name)s"), {
                xaxis_name: stat2name(props["xaxis"]),
                yaxis_name: stat2name(props["yaxis"])
            }));
            if (json["objects"].length > 0) {
                drawJsonChart(chart_div, json, props["xaxis"], props["yaxis"]);
            } else {
                show_message("error", gettext("No learner accounts in this group have been created."));
            }
            $("#loading").text("");

        }).fail(function(resp) {
            $("#loading").text("");
        });
    $("#loading").text(sprintf(gettext("Loading '%(xaxis)s' vs. '%(yaxis)s' ..."), props));
    $("#chart_div").html("");
}

function TimelineplotTopics(topic_paths) {
    if (topic_paths==null) {
        topic_paths = get_topic_paths_from_tree();
    }

    plotJsonData(
        "#chart_div",
        TIMELINE_API_DATA_URL,
        {
            "xaxis": "completion_timestamp",
            "yaxis": "mastered",
            "group_id": getParamValue("group_id"),
            "facility_id": getParamValue("facility_id"),

            "completion_timestamp__gte": $("#datepicker_start").val(),
            "completion_timestamp__lte": $("#datepicker_end").val(),

            "topic_path":  topic_paths
        }
    );
}


function plotTopics(topic_paths) {
    if (!$("#content_tree")) {
        return false;
    }
    if (topic_paths==null) {
        topic_paths = get_topic_paths_from_tree();
    }

    plotJsonData(
        "#chart_div",
        API_DATA_URL,
        {
            "xaxis": "Mastery",
            "yaxis": "Attempts",

            "group_id": getParamValue("group_id"),
            "facility_id": getParamValue("facility_id"),

            "completion_timestamp__gte": $("#datepicker_start").val(),
            "completion_timestamp__lte": $("#datepicker_end").val(),

            "topic_path":  topic_paths
        }
    );
}

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
    if (!props["user"])       { props["user"]       = FORM_USER; }
    if (!props["topic_path"]) { props["topic_path"] = FORM_TOPIC_PATH; }

    if (!props["xaxis"] || !props["yaxis"] || !props["topic_path"] || props["topic_path"].length == 0) { // one of the ---- is selected
        return false;
    }

    // Get the data
    var url = base_url + "?" + $.param(props, true);

    clear_messages();
    doRequest(url)
        .success(function(json) {
            $("#loading").text(sprintf(gettext("Drawing %(xaxis_name)s versus %(yaxis_name)s"), {
                xaxis_name: stat2name(props["xaxis"]),
                yaxis_name: stat2name(props["yaxis"])
            }));
            if (Object.keys(json["data"]).length > 0) {
                drawJsonChart(chart_div, json, props["xaxis"], props["yaxis"]);
            } else {
                show_message("error", gettext("No student accounts in this group have been created."));
            }
            $("#loading").text("");

        }).fail(function(resp) {
            $("#loading").text("");
        });
    $("#loading").text(sprintf(gettext("Loading '%(xaxis)s' vs. '%(yaxis)s' ..."), props));
    $("#chart_div").html("");
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
            "xaxis":       $("#xaxis option:selected").val(),
            "yaxis":       $("#yaxis option:selected").val(),
            "user":        "",
            "group":       $("#" + $("#facility option:selected").val() + "_group_select option:selected").val(),
            "facility":    $("#facility option:selected").val(),
            "topic_path":  topic_paths
        }
    );
}


$(function() {
    window.showing_tree = false;

    // Select the values in the
    $("#xaxis").val(FORM_XAXIS).change();
    $("#yaxis").val(FORM_YAXIS).change().prop("disabled", false);


    setTimeout(function() {
        // Set some event functions, once objects are available to manipulate

        // Register a callback
        window.toggle_tree_callbacks.push(plotTopics);

        // Make sure that each dropdown has a callback
        //   to replot upon selection.
        $(".group_select").change(function(event) { changeData(event.target.id); plotTopics(null); });
        $("#facility").change(function() { changeData("facility"); plotTopics(null); });

        // When the button is clicked, toggle the view style
        $("#content_tree_toggle").click(function() {
            toggle_tree();
        });

        // Get the topic tree (starting on window load)
        doRequest(GET_TOPIC_TREE_URL)
            .success(function(treeData) {
                treeData["expand"] = true; // expand the top level

                $("#content_tree").dynatree({
                    imagePath: IMAGES_URL,
                    checkbox: true,
                    selectMode: 3,
                    children: treeData,
                    debugLevel: 0,
                    onDblClick: function(node, event) {
                        node.toggleSelect();
                    },
                    onKeydown: function(node, event) {
                        if( event.which == 32 ) {
                            node.toggleSelect();
                            return false;
                        }
                    },
                    onPostInit: function() {
                        // Load the topics found in the querystring, when the topic_tree finishes initializing
                        topic_paths_in_querystring = FORM_TOPIC_PATH;
                        if (topic_paths_in_querystring.length == 0) {
                            toggle_tree(true); // open tree, force callbacks
                        }
                        else {
                            set_topic_paths_in_tree(this, topic_paths_in_querystring);
                        }

                    }
                });
            });
    }, 200); //200= callback wait time.
});

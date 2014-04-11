function generate_current_link() {
    var url = window.location.href;

    // Add topic paths
    if (typeof get_topic_paths_from_tree != 'undefined') {
        var topic_paths = get_topic_paths_from_tree();
        for (pi in topic_paths) {
            url += "&topic_path=" + topic_paths[pi];
        }
        // Add axis information
        url = setGetParam(url, "xaxis", $("#xaxis option:selected").val());
        url = setGetParam(url, "yaxis", $("#yaxis option:selected").val());
        url = setGetParam(url, "facility", $("#facility option:selected").val());
        url = setGetParam(url, "group", $("#" + $("#facility option:selected").val() + "_group_select option:selected").val());
    }

    return url;
}
function display_link () {
    var url_field = $('input#url');
    var link_box = $('#link-box');
    var link_text = null;

    if(url_field.is(":visible")){
        url_field.hide();
        link_text = gettext("share");
    }
    else{
        url_field.val(generate_current_link());
        url_field.show().focus().select().attr('readonly', true);
        link_text = gettext("hide");
    }
    link_box.find('a').text("(" + link_text + ")");
}
function changeData(type) {
    var opt = $("#" + type + " option:selected");
    $("#" + type + "_editable").text(opt.text());
    // Check to see if the item being passed is a group item - regex match against group in the item.
    var linktype = /group/i.test(type) ? "group" : type
    $(".changeable-link").each(function () {
        this.href = setGetParam(this.href, linktype, opt.val());
    });
    $("#" + type + "_editable").show();
    $("#" + type).hide();
    if (type === "facility") {
        // Show the appropriate group selection for a particular facility when the facility is changed.
        $(".group_div").hide();
        $("#" + $("#facility").val()).show();
        changeData($("#facility").val() + "_group_select")
    }
}
function make_editable(type) {
    if ($("#" + type + " option").length > 1) {
        $("#" + type + "_editable").hide();
        $("#" + type).show();
    }
}

$(function() {
    // Make sure that each dropdown has a callback to replot upon selection.
    // Then, dynamically read the group id from the change event.
    $(".group_select").change(function(event) { changeData(event.target.id); });

    $("#facility").change(function() { changeData("facility"); });

    // Select the values in the dropdowns
    $("#" + FACILITY_ID + "_group_select").val(GROUP_ID).change();
    $("#facility").val(FACILITY_ID).change();
});

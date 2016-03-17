$(function() {

    $("#student").change(function() {
        window.location.href = setGetParam(window.location.href, "user", $("#student option:selected").val());
    });

    $("#playlist").change(function() {
        window.location.href = setGetParam(window.location.href, "playlist", $("#playlist option:selected").val());
    });

    $("#facility").change(function() {
        window.location.href = setGetParamDict(window.location.href, {
            "facility": $("#facility option:selected").val(),
            "group": $("#" + $("#facility option:selected").val() + "_group_select").val(),
            "playlist": ""
        });
    });

    $(".group_select").change(function(event) {
        window.location.href = setGetParam(window.location.href, "group", $(event.target).val());
    });

    // Selector to toggle visible elements is stored in each option value
    cell_height = 27;
    $("#disp_options").change(function() {
        selector = $("#disp_options option:selected").val();

        // adjust the cell height
        cell_height += 50 * Math.pow(-1, 0 + $(selector).is(":visible"));

        // adjust view in data cells
        $(selector).each(function() {
            $(this).toggle();
        });
        $(selector).each(function() {
            $(this).height(20);
            $(this).parent().height(cell_height);
        });

        // Adjust student name cell heights
        $("th.username").each(function() {
            $(this).height(cell_height);
        });
    });
    $(window).resize(function() {
        $('.headrowuser').height($('.headrow.data').height());
    }).resize();
});

$(function(){
    $("#tree").dynatree({
        persist: true,
        expand: false,
        checkbox: true,
        selectMode: 3,
        cookieId: "exercises",
        children: null,

        onPostInit: function(isReloading, isError) {
            if (window.location.href.indexOf("&playlist=") == -1) {
                $("#tree").dynatree("getTree").visit(function(node){
                    node.select(false);
                    node.expand(false);
                });
            }
        },
        onSelect: function(select, dtnode) {
            var selKeys = $.map(dtnode.tree.getSelectedNodes(), function(dtnode){
              return dtnode.data.key;
            });
            window.location.href = setGetParam(window.location.href, "playlist", selKeys);
        }
    });
});

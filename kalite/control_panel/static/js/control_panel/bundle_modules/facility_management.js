var $ = require("base/jQuery");
var _ = require("underscore");
var get_params = require("utils/get_params");
var api = require("utils/api");
require("jquery-sparkline");

function getSelectedItems(select) {
    // Retrieve a list of selected users.
    // var items = $(select).find("tr.selected").map(function () {
    //     return $(this).attr("value");
    // }).get();
    var items = $(select).find("tr.selectable.selected").map(function () {
        return $(this).attr("value");
    }).get();
    return items;
}

function setActionButtonState(select) {
    // argument to allow conditional selection of action buttons.
    if($(select).find("tr.selectable.selected").length) {

        $('button[value="'+select+'"]').removeAttr("disabled").removeAttr("title");
    } else {
        $('button[value="'+select+'"]').attr("disabled", "disabled");
        $('button[value="'+select+'"]').attr("title", "You must select one or more rows from the table below before taking this action.");
    }
}

function setSelectAllState(selectAllId) {
    var allChecked = true;
    // If all checkboxes selected, set to checked, if not, set to unchecked
    var boxes = $(selectAllId).find('tbody').find('input[type="checkbox"]');
    _.each(boxes, function(box) {
        if ($(box).prop('checked') === false){
            allChecked = false;
        }
    });
    var selectAllBox = $(selectAllId).find('thead').find('.select-all');
    $(selectAllBox).prop("checked", allChecked);
}

$(function() {
    // on load add the same title tag to all disabled buttons 
    $('button[disabled="disabled"]').attr("title", "You must select one or more rows from the table below before taking this action.");

    $("#group").change(function(){
        // Change the URL to the selected group.
        GetParams["group_id"] = $("#group option:selected").val();
        window.location.href = get_params.setGetParamDict(window.location.href, GetParams);
    });

    $(".all").click(function(event){
        // Select all checkboxes within local table
        var el = $(event.target.value);
        el.find("thead").find("input.select-all").prop("checked", true);
        el.find("tbody").find("tr").not(".selected").mousedown();
    });

    $(".none").click(function(event){
        // Unselect all checkboxes within local table
        var el = $(event.target.value);
        el.find("thead").find("input.select-all").prop("checked", false);
        el.find("tbody").find("tr.selected").mousedown();
    });

    $(".movegroup").click(function(event) {
        // Move users to the selected group
        var users = getSelectedItems(this.value);
        var group = $(this.value).find('select[value="'+this.value+'"] option:selected').val();

        if (group==="----") {
            alert(gettext("Please choose a group to move users to."));
        } else if (users.length===0) {
            alert(gettext("Please select users first."));
        } else if(!confirm(gettext("You are about to move selected users to another group."))) {
            return;
        } else {
            api.doRequest(window.Urls.move_to_group(), {users: users, group: group})
                .success(function() {
                    location.reload();
                });
        }
    });

    // Code for checkboxes
    $(".select-all").click(function(event){
        // Select all checkboxes within local table
        var el = $(event.target.value);
        if(!event.target.checked){
            el.find("tbody").find("input:checked").mousedown();
        } else {
            el.find("tbody").find("input:checkbox:not(:checked)").mousedown();
        }
    });

    $("input:checkbox").click(function(event){
        var el = event.target.value;
        // Only set action button state on related action buttons.
        setActionButtonState(el);
    });

    $("input:checkbox").mouseup(function(event){
        var el = event.target.value;
        // Set state of select all checkbox based on clicks 
        setSelectAllState(el);
    });

    $(".delete").click(function(event) {
        // Delete the selected users
        var users = getSelectedItems(this.value);

        if (users.length === 0) {
            alert(gettext("Please select users first."));
        } else if (!confirm(gettext("You are about to delete selected users, they will be permanently deleted."))) {
            return;
        } else {
            api.doRequest(window.Urls.delete_users(), {users: users})
                .success(function() {
                    location.reload();
                });
        }
    });

    $(".delete-group").click(function(event) {
        // Delete the selected users
        var groups = getSelectedItems(this.value);

        if (groups.length === 0) {
            alert(gettext("Please select groups first."));
        } else if (!confirm(gettext("You are about to permanently delete the selected group(s). Note that any learners currently in this group will now be characterized as 'Ungrouped' but their profiles will not be deleted."))) {
            return;
        } else {
            api.doRequest(window.Urls.group_delete(), {groups: groups})
                .success(function() {
                    location.reload();
                });
        }
    });

    // When mouse is pressed over a row in the table body (not the header row), make mouseovers select.
    $(".selectable-table").find("tbody").find("tr.selectable").mousedown(function(){
        $(this).toggleClass("selected");
        var checkbox = $(this).find("input");
        if (checkbox.prop("checked")) {
            checkbox.prop("checked", false);
        } else {
            checkbox.prop("checked", true);
        }
        var el = "#" + $(this).attr("type");
        setActionButtonState(el);
        setSelectAllState(el);
        
        // (Currently disabled due to a bit of bugginess with not registering the mouseup event, which created a weird flickering effect. Also, this won't work on tablets, since drag is scroll.) 
        // This code is to allow rows of a selectable-table class table to be clicked for selection,
        // and dragged across with mousedown for selection.
        // $(".selectable-table").find("tbody").find("tr.selectable").mouseover(function(){
        //     $(this).toggleClass("selected");
        //     var checkbox = $(this).find("input");
        //     if (checkbox.prop("checked")) {
        //         checkbox.prop("checked", false);
        //     } else {
        //         checkbox.prop("checked", true);
        //     }
        //     setActionButtonState("#" + $(this).attr("type"));
        // });
    });

    // (Currently disabled for the same reasons as above)
    // Unbind the mouseover selection once the button has been released.
    // $(".selectable-table").find("tbody").find("tr.selectable").mouseup(function(){
    //     $(".selectable-table").find("tbody").find("tr.selectable").unbind("mouseover");
    // });

    // If the mouse moves out of the table with the button still depressed, the above unbind will not fire.
    // Unbind the mouseover once the mouse leaves the table.
    // This means that moving the mouse out and then back in with the button depressed will not select.

    // $(".selectable-table").mouseleave(function(){
    //     $(".selectable-table").find("tbody").find("tr.selectable").unbind("mouseover");
    // })


    // Prevent propagation of click events on links to limit confusing behaviour
    // of rows being selected when links clicked.
    $(".selectable-table").find("a").mousedown(function(event) {
        event.stopPropagation();
        return false;
    });

    $(".selectable-table").find("tbody").find("input").mousedown(function(event){
        event.preventDefault();
    });

    $(".selectable-table").find("tbody").find("input").click(function(event){
        event.preventDefault();
        return false;
    });

    $('.sparklines').sparkline('html', { enableTagOptions: true, disableInteraction: true });
});

module.exports = {
    $: $
};
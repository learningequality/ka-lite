function getSelectedItems(select) {
    // Retrieve a list of selected users.
    // var items = $(select).find("tr.selected").map(function () {
    //     return $(this).attr("value");
    // }).get();
    var items = $(select).find("input:checked").parents("tr").map(function () {
        return $(this).attr("value");
    }).get();
    return items;
}

function setActionButtonState(select) {
    // argument to allow conditional selection of action buttons.

    if($(select).find("input:checked").length) {
        $('button[value="'+select+'"]').removeAttr("disabled");
    } else {
        $('button[value="'+select+'"]').attr("disabled", "disabled");
    }
}

$(function() {

    $("#group").change(function(){
        // Change the URL to the selected group.
        GetParams["group_id"] = $("#group option:selected").val();
        window.location.href = setGetParamDict(window.location.href, GetParams);
    });

    $(".movegroup").click(function(event) {
        // Move users to the selected group
        var users = getSelectedItems(this.value);
        var group = $(this.value).find('select[value="'+this.value+'"] option:selected').val();

        if (group==="----") {
            alert(gettext("Please choose a group to move users to."));
        } else if (users.length==0) {
            alert(gettext("Please select users first."));
        } else if(!confirm(gettext("You are about to move selected users to another group."))) {
            return;
        } else {
            doRequest(MOVE_TO_GROUP_URL, {users: users, group: group})
                .success(function() {
                    location.reload();
                })
        }
    });

    // Code for checkboxes
    $(".select-all").click(function(event){
        // Select all checkbxes within local table
        var el = $(event.target.value);
        if(this.checked) {
            el.find("input").prop("checked", true);
        } else {
            el.find("input").prop("checked", false);
        }
    })

    $("input:checkbox").click(function(event){
        // Only set action button state on related action buttons.
        setActionButtonState(event.target.value);
    })

    $(".delete").click(function(event) {
        // Delete the selected users
        var users = getSelectedItems(this.value);

        if (users.length == 0) {
            alert(gettext("Please select users first."));
        } else if (!confirm(gettext("You are about to delete selected users, they will be permanently deleted."))) {
            return;
        } else {
            doRequest(DELETE_USERS_URL, {users: users})
                .success(function() {
                    location.reload();
                });
        }
    });

    $(".delete-group").click(function(event) {
        // Delete the selected users
        var groups = getSelectedItems(this.value);

        if (groups.length == 0) {
            alert(gettext("Please select groups first."));
        } else if (!confirm(gettext("You are about to permanently delete the selected group(s). Note that any students currently in this group will now be characterized as 'Ungrouped' but their profiles will not be deleted."))) {
            return;
        } else {
            doRequest(DELETE_GROUPS_URL, {groups: groups})
                .success(function() {
                    location.reload();
                });
        }
    });

    // // This code is to allow rows of a selectable-table class table to be clicked for selection,
    // // and dragged across with mousedown for selection.
    // // When mouse is pressed over a row in the table body (not the header row), make mouseovers select.
    // var tableRows = $(".selectable-table").find("tbody").find("tr");
    // tableRows.find('td:not(:has input)').mousedown(function(event){
    //     $(this).toggleClass("selected");
    //     var checkbox = $(this).find("input");
    //     if (checkbox.prop("checked")) {
    //         checkbox.prop("checked", false);
    //     } else {
    //         checkbox.prop("checked", true);
    //     }
    //     // Only set action button state on related action buttons.
    //     setActionButtonState("#" + $(event.currentTarget).attr("type"));
    //     $(".selectable-table").find("tbody").find("tr").mouseover(function(event){
    //         $(this).toggleClass("selected");
    //         var checkbox = $(this).find("input");
    //         if (checkbox.prop("checked")) {
    //             checkbox.prop("checked", false);
    //         } else {
    //             checkbox.prop("checked", true);
    //         }
    //         // This code is to toggle action buttons on only when items have been selected
    //         // Works for now as only students have action buttons
    //         // Only set action button state on related action buttons.
    //         setActionButtonState("#" + $(event.currentTarget).attr("type"));
    //     });
    // });

    // // Unbind the mouseover selection once the button has been released.
    // $(".selectable-table").find("tbody").find("tr").mouseup(function(){
    //     $(".selectable-table").find("tbody").find("tr").unbind("mouseover");
    // });

    // // If the mouse moves out of the table with the button still depressed, the above unbind will not fire.
    // // Unbind the mouseover once the mouse leaves the table.
    // // This means that moving the mouse out and then back in with the button depressed will not select.
    // $(".selectable-table").mouseleave(function(){
    //     $(".selectable-table").find("tbody").find("tr").unbind("mouseover");
    // })

    // // Prevent propagation of click events on links to limit confusing behaviour
    // // of rows being selected when links clicked.
    // $(".selectable-table").find("a").mousedown(function(event) {
    //     event.stopPropagation();
    //     return false;
    // });

});

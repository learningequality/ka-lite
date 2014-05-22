function getSelectedItems(select) {
    // Retrieve a list of selected users.
    var items = $(select).find("tr.selected").map(function () {
        return $(this).attr("value");
    }).get();

    return items;
}

function setActionButtonState(select) {
    // argument to allow conditional selection of action buttons.
    if($(select).find("tr.selected").length) {
        $(select).find(".action button").removeAttr("disabled")
    } else {
        $(select).find(".action button").attr("disabled", "disabled")
    }
}

$(function() {

    $("#group").change(function(){
        // Change the URL to the selected group.
        GetParams["group_id"] = $("#group option:selected").val();
        window.location.href = setGetParamDict(window.location.href, GetParams);
    });

    $(".all").click(function(event){
        // Select all users within local table
        $(event.target.value).find("tr").addClass("selected");
        // Only set action button state on related action buttons.
        setActionButtonState(event.target.value);
    })

    $(".none").click(function(event){
        // Unselect all users within local table
        $(event.target.value).find("tr").removeClass("selected");
        // Only set action button state on related action buttons.
        setActionButtonState(event.target.value);
    })

    $(".movegroup").click(function(event) {
        // Move users to the selected group
        var users = getSelectedItems(this.value);
        var group = $(this.value).find('.movegrouplist option:selected').val();

        console.log(group);

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
        } else if (!confirm(gettext("You are about to delete selected groups, they will be permanently deleted."))) {
            return;
        } else {
            doRequest(DELETE_GROUPS_URL, {groups: groups})
                .success(function() {
                    location.reload();
                });
        }
    });

    // This code is to allow rows of a selectable-table class table to be clicked for selection,
    // and dragged across with mousedown for selection.
    // When mouse is pressed over a row in the table body (not the header row), make mouseovers select.
    $(".selectable-table").find("tbody").find("tr").mousedown(function(event){
        $(this).toggleClass("selected");
        // Only set action button state on related action buttons.
        setActionButtonState("#" + $(event.currentTarget).attr("type"));
        $(".selectable-table").find("tbody").find("tr").mouseover(function(event){
            $(this).toggleClass("selected");
            // This code is to toggle action buttons on only when items have been selected
            // Works for now as only students have action buttons
            // Only set action button state on related action buttons.
            setActionButtonState("#" + $(event.currentTarget).attr("type"));
        });
    });

    // Unbind the mouseover selection once the button has been released.
    $(".selectable-table").find("tbody").find("tr").mouseup(function(){
        $(".selectable-table").find("tbody").find("tr").unbind("mouseover");
    });

    // If the mouse moves out of the table with the button still depressed, the above unbind will not fire.
    // Unbind the mouseover once the mouse leaves the table.
    // This means that moving the mouse out and then back in with the button depressed will not select.
    $(".selectable-table").mouseleave(function(){
        $(".selectable-table").find("tbody").find("tr").unbind("mouseover");
    })

    // Prevent propagation of click events on links to limit confusing behaviour
    // of rows being selected when links clicked.
    $(".selectable-table").find("a").mousedown(function(event) {
        event.stopPropagation();
        return false;
    });

});

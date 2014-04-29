function getSelectedUsers(select) {
    // Retrieve a list of selected users.
    var users = $(select).find("tr.selected").map(function () {
        return $(this).attr("value");
    }).get();

    return users;
}

function setActionButtonState() {
    if($("tr.selected").length) {
        $(".action button").removeAttr("disabled")
    } else {
        $(".action button").attr("disabled", "disabled")
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
        setActionButtonState();
    })

    $(".none").click(function(event){
        // Unselect all users within local table
        $(event.target.value).find("tr").removeClass("selected");
        setActionButtonState();
    })

    $(".movegroup").click(function(event) {
        // Move users to the selected group
        var users = getSelectedUsers(this.value);
        var group = $(this.value).find('.movegrouplist option:selected').val();

        console.log(group);

        if (group==="----") {
            alert(gettext("Please choose a group to move users to."));
        } else if (users.length==0) {
            alert(gettext("Please select users first."));
        } else if(!confirm(gettext("You are about to move selected users to another group."))) {
            return;
        } else {
            doRequest("/securesync/api/move_to_group", {users: users, group: group})
                .success(function() {
                    location.reload();
                })
        }
    });


    $(".delete").click(function(event) {
        // Delete the selected users
        var users = getSelectedUsers(this.value);

        if (users.length == 0) {
            alert(gettext("Please select users first."));
        } else if (!confirm(gettext("You are about to delete selected users, they will be permanently deleted."))) {
            return;
        } else {
            doRequest("/securesync/api/delete_users", {users: users})
                .success(function() {
                    location.reload();
                });
        }
    });

    // This code is to allow rows of a selectable-table class table to be clicked for selection,
    // and dragged across with mousedown for selection.
    // When mouse is pressed over a row in the table body (not the header row), make mouseovers select.
    $(".selectable-table").find("tbody").find("tr").mousedown(function(){
        $(this).toggleClass("selected");
        setActionButtonState();
        $(".selectable-table").find("tbody").find("tr").mouseover(function(){
            $(this).toggleClass("selected");
            // This code is to toggle action buttons on only when items have been selected
            // Works for now as only students have action buttons
            setActionButtonState();
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

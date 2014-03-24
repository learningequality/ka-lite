function getSelectedUsers(select) {
    // Retrieve a list of selected users.
    var users = $(select).find("tr.selected").map(function () {
        return $(this).attr("value");
    }).get();

    return users;
}

$(function() {

    $("#group").change(function(){
        // Change the URL to the selected group.
        GetParams["group_id"] = $("#group option:selected").val();
        window.location.href = setGetParamDict(window.location.href, GetParams);
    });

    $(".all").click(function(event){
        // Select all users within local table
        $(event.target.value).find("tr").addClass("selected")
    })

    $(".none").click(function(event){
        // Unselect all users within local table
        $(event.target.value).find("tr").removeClass("selected")
    })

    $(".movegroup").click(function(event) {
        // Move users to the selected group
        var users = getSelectedUsers(this.value);
        var group = $(this.value).find('.movegrouplist option:selected').val();

        if (!group) {
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

    $(".removegroup").click(function(event) {
        // Move users from the selected group to ungrouped.
        var users = getSelectedUsers(this.value);

        if (users.length == 0) {
            alert(gettext("Please select users first"));
        } else if(!confirm(gettext("You are about to remove selected users from their current group."))) {
            return;
        } else {
            doRequest("/securesync/api/remove_from_group", {users: users})
                .success(function() {
                    location.reload();
                });
        }
    });

    $(".delete").click(function(event) {
        // Delete the selected users
        var users = getSelectedUsers(this.value);

        if (users.length == 0) {
            alert(gettext("Please select users first"));
        } else if (!confirm(gettext("You are about to delete selected users, they will be permanently deleted."))) {
            return;
        } else {
            doRequest("/securesync/api/delete_users", {users: users})
                .success(function() {
                    location.reload();
                });
        }
    });

    $(".selectable-table").find("tbody").find("tr").mousedown(function(){
        $(this).toggleClass("selected");
        $(".selectable-table").find("tbody").find("tr").mouseover(function(){
            $(this).toggleClass("selected");
        });
    });

    $(".selectable-table").find("tbody").find("tr").mouseup(function(){
        $(".selectable-table").find("tbody").find("tr").unbind("mouseover");
    });

    $(".selectable-table").mouseleave(function(){
        $(".selectable-table").find("tbody").find("tr").unbind("mouseover");
    })

});

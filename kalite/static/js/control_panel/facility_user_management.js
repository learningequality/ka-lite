function getSelectedUsers() {
    // Retrieve a list of selected users.
    var users = $("[type=checkbox]:checked").map(function () {
        return this.value;
    }).get();

    return users;
}

$(function() {

    $("#group").change(function(){
        // Change the URL to the selcted group.
        var group_id = $("#group option:selected").val();
        if (group_id) {
            window.location.href = TEMPLATE_GROUP_URL.replace("group_id", group_id);
        }
    });

    $("#all").click(function(){
        // Selected all users
        $("[type=checkbox]").prop("checked",true)
    })

    $("#none").click(function(){
        // Unselect all users
        $("[type=checkbox]").prop("checked",false)
    })

    $("#movegroup").click(function(event) {
        // Move users to the selected group
        var users = getSelectedUsers();
        var group = $('#movegrouplist option:selected').val();

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

    $("#removegroup").click(function(event) {
        // Move users from the selected group to ungrouped.
        var users = getSelectedUsers();

        if (users.length == 0) {
            alert(gettext("Please select users first"));
        } else if(!confirm(gettext("You are about to remove selected users from their current group."))) {
            return;
        } else {
            doRequest("/secursync/api/remove_from_group", {users: users})
                .success(function() {
                    location.reload();
                });
        }
    });

    $("#delete").click(function(event) {
        // Delete the selected users
        var users = getSelectedUsers();

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
});

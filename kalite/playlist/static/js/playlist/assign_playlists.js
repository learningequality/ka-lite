function appendStudentGrp(id, studentGrpName) {
  var selector = sprintf("tr[playlist-id|=%s] ul", id);
  $(selector).append('<li>'+studentGrpName+'</li>');
}

function allowDrop(ev) {
  ev.preventDefault();
}

function drag(ev) {
  var target = ev.currentTarget;
  var studentGrpId = target.getAttribute('student-grp-id');
  var studentGrp = target.innerText || target.textContent;
  var dataTransfer = ev.originalEvent.dataTransfer;
  dataTransfer.setData('student-grp', studentGrp);
  dataTransfer.setData('student-grp-id', studentGrpId);
}

function drop(ev) {
  var target = ev.currentTarget;
  var playlistId = target.getAttribute('playlist-id');
  var dataTransfer = ev.originalEvent.dataTransfer;
  ev.preventDefault();
  var studentGrp = dataTransfer.getData('student-grp');
  appendStudentGrp(playlistId, studentGrp);
}

// modify the groups assigned to a playlist
function api_modify_groups(playlist_id, group_ids_assigned) {
  console.log(ALL_PLAYLISTS_URL);
  var PLAYLIST_DETAIL_URL = ALL_PLAYLISTS_URL + playlist_id + "/"; // note: cleanup to something more readable
  var groups_assigned = group_ids_assigned.map(function (id) { return {"id": id}; });
  doRequest(PLAYLIST_DETAIL_URL,
            {"groups_assigned": groups_assigned},
            {"dataType": "text", // use text so jquery doesn't do the error callback since the server returns an empty response body
             "type": "PATCH"}).success(function(res) {
               console.log(res);
               clear_messages();
              show_message("success", gettext("Successfully updated playlist groups."));
            }).error(function(e) {
              if (e.status === 404) {
                clear_messages();
                show_message("error", gettext("That playlist cannot be found."));
              }
            });
}

function displayGroups() {
    doRequest(ALL_GROUPS_URL).success(function(data) {
        data.objects.map(function(obj) {
            $("#student-groups").append(sprintf('<tr><td student-grp-id="%(id)s" draggable="true">%(name)s</td></tr>', obj));
        });
        $(".span3 td").on('dragstart', drag);
    });
}

function appendPlaylistStudentGroupRow(playlist) {
    return sprintf('<tr class="droppable" playlist-id="%(id)s"><td><ul></ul></td></tr>', playlist);
}

function displayPlaylists() {
    doRequest(ALL_PLAYLISTS_URL).success(function(data) {
        data.objects.map(function(playlist) {
            var playlistTitleRow = sprintf("<tr class='droppable title' playlist-id='%(id)s'><td>%(title)s</td></tr>", playlist);
            var playlistStudentGroupsRow = appendPlaylistStudentGroupRow(playlist);
            $("#playlists").append(playlistTitleRow + playlistStudentGroupsRow);
            $("tr.title").click(function(e) {
                $(e.currentTarget.nextSibling).toggle();
            });

            playlist.groups_assigned.map(function(group) {
                appendStudentGrp(group.id, group.name);
            });
            $(".droppable").on('dragover', allowDrop);
            $(".droppable").on('drop', drop);
        });
    });
}

$(function() {
    displayGroups();
    displayPlaylists();

    $("tr.title+tr").hide();

});

function appendStudentGrp(id, studentGrp) {
  $("#student-grps-" + id + " ul").append('<li>'+studentGrp+'</li>');
}
function allowDrop(ev) {
  ev.preventDefault();
}

function drag(ev) {
  var target = ev.currentTarget;
  var studentGrp = target.innerText || target.textContent;
  ev.originalEvent.dataTransfer.setData('student-grp', studentGrp);
}

function drop(ev) {
  var array = ev.currentTarget.id.split('-');
  var length = array.length;
  var id = array[length - 1];
  ev.preventDefault();
  var studentGrp = ev.originalEvent.dataTransfer.getData('student-grp');
  appendStudentGrp(id, studentGrp);
}

// get and display all groups
$(function() {
    doRequest(ALL_GROUPS_URL).success(function(data) {
        data.objects.map(function(obj) {
            $("table[id|=all-student-groups] tr:last").after(sprintf('<tr><td>%(name)s</td></tr>', obj));
        });
    });
});

$(function() {
    $(".span3 td").on('dragstart', drag);
    $("tr[id|=student-grps]").on('dragover', allowDrop);
    $("tr[id|=student-grps]").on('drop', drop);
    $("tr[id|=title]").on('dragover', allowDrop);
    $("tr[id|=title]").on('drop', drop);
    $("tr[id|=student-grps]").hide();
    $("tr[id|=title]").click(function(e) {
        var target = e.target;
        var targetId = e.currentTarget.id;
        var idNum = targetId.split('-')[1];
        $("#student-grps-" + idNum).toggle();
    });
});

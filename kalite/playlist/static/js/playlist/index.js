$(function() {
    $("tr[id|=student-grps]").hide();
    $("tr[id|=title]").click(function(e) {
        var target = e.target;
        if(!$(target).is(":button")) {
          var targetId = e.currentTarget.id;
          var idNum = targetId.split('-')[1];
          $("#student-grps-" + idNum).toggle();
        }
        else {
        }
    });
});

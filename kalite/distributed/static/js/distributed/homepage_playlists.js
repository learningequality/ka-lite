$(function() {
  $("#playlist-table").hide();
  $.ajax({
    url: ASSIGNED_PLAYLISTS_URL,
    type: 'GET',
    dataType: 'json',
    success: function(data) {
      $("#playlist-table").show();
      $(".loading").hide();
      var playlists = $("#playlists");
      data.objects.map(function(result) {
          var format = formatPlaylist(result);
          $("#playlists").append(format);
      });
      $(".cell-content").dotdotdot({
          ellipsis: '...',
          wrap: 'word',
        fallbackToLetter: true,
        after: null,
        watch: false,
        height: null,
        tolerance: 0
      });
    }
  });
});

function formatPlaylist(data) {
    data.numVideos = data.entries.filter(function(e) { return e.entity_kind == 'Video'; }).length;
    data.numExercises = data.entries.filter(function(e) { return e.entity_kind == 'Exercise'; }).length;
    var format = HB.template("playlists/homepage-playlists-table-cell");
    return format(data);


}

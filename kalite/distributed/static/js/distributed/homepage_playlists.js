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
    var format =
      "<li class=\"pull-left\"><div><span class=\"block cell-content\">" + data.title +"</span><span class=\"pull-left\">5/2</span><span class=\"pull-right\">V:2 Ex:7</span></div></li>";
    return format;


}

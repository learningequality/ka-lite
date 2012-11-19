var flashVars = {
    srt: 1,
    showswitchsubtitles: 1,
    srtcolor: "eeeeee",
    srtsize: 25,
    srtbgcolor: "000000",
    showstop: 1,
    showvolume: 1,
    showfullscreen: 1,
    ondoubleclick: "fullscreen",
    showiconplay: 1,
    iconplaybgcolor: "cceaa9",
    margin: 0,
    buffermessage: "Loading... (_n_)",
    videobgcolor: "000000"
};

var objParams = {
    movie: "/static/flvplayer/player_flv_maxi.swf",
    allowFullScreen: "true",
    allowScriptAccess: "always"
};

function embedSwf(el, width, height, callback) {
    swfobject.embedSWF(
        "/static/flvplayer/player_flv_maxi.swf",
        el,
        width,
        height,
        "9", // flash version requested
        "",
        flashVars,
        objParams,
        {},
        callback
    );
}

function updatePoints() {
    if (videoData.points) {
        $(".points").text(videoData.points);
        $(".points-container").show();
    }
}

$(function() {

    doRequest("/api/get_video_logs", [videoData.youtube_id]).success(function(data) {
        if (data.length === 0) {
            return;
        }
        videoData.total_seconds_watched = data[0].total_seconds_watched;
        videoData.points = data[0].points;
        videoData.complete = data[0].complete;
        updatePoints();
    });

});

function updateVideoStats(time, duration) {
    if ((time * duration) === 0) {
        return;
    }
    if (videoData.complete) {
        return;
    }
    var video_time_elapsed = time - videoData.last_second_watched;
    var current_wall_time = new Date();
    var wall_time_elapsed = (current_wall_time - videoData.last_second_watched_walltime) / 1000;
    videoData.last_second_watched_walltime = current_wall_time;
    videoData.last_second_watched = time;
    var new_seconds_watched = Math.min(video_time_elapsed, wall_time_elapsed);
    if (new_seconds_watched <= 0) {
        return;
    }
    videoData.seconds_watched_since_save += new_seconds_watched;
    var points = Math.floor(100 * (videoData.total_seconds_watched / duration));
    var force_save = false;
    if (points > 95) {
        points = 100;
        force_save = true;
    }
    if (videoData.seconds_watched_since_save > 10 || force_save) {
        videoData.total_seconds_watched += videoData.seconds_watched_since_save;
        data = {
            youtube_id: videoData.youtube_id,
            total_seconds_watched: Math.floor(videoData.total_seconds_watched),
            seconds_watched: Math.floor(videoData.seconds_watched_since_save),
            points: points,
        }
        doRequest("/api/save_video_log", data).success(function(data) {
            videoData.points = data.points;
            updatePoints();
        });
        videoData.seconds_watched_since_save = 0;
    }
}

// listen to callbacks from the FLV player to update stats
window.VideoStats = {
    cacheStats: updateVideoStats
};

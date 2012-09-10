var flashVars = {
    // srt: 1,
    showswitchsubtitles: 1,
    srtcolor: "eeeeee",
    srtsize: 16,
    //srtbgcolor: "000000",
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

function embed_swf(el, width, height, callback) {
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
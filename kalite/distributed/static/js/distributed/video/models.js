window.VideoLogModel = ContentLogModel.extend({

    urlRoot: function() {
        return window.sessionModel.get("GET_VIDEO_LOGS_URL");
    }

});

window.VideoLogCollection = ContentLogCollection.extend({

    model: VideoLogModel,

    model_id_key: "video_id"

});
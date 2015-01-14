window.VideoLogModel = ContentLogModel.extend({

    urlRoot: GET_VIDEO_LOGS_URL

});

window.VideoLogCollection = ContentLogCollection.extend({

    model: VideoLogModel,

    model_id_key: "video_id"

});
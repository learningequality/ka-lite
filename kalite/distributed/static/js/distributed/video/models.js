window.VideoLogModel = ContentLogModel.extend({

    urlRoot: GET_VIDEO_LOGS_URL

});

window.VideoLogCollection = ContentLogCollection.extend({

    model: VideoLogModel

});
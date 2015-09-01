var ContentModels = require("content/models");


var VideoLogModel = ContentModels.ContentLogModel.extend({

    urlRoot: function() {
        return window.sessionModel.get("GET_VIDEO_LOGS_URL");
    }

});

var VideoLogCollection = ContentModels.ContentLogCollection.extend({

    model: VideoLogModel,

    model_id_key: "video_id"

});

module.exports = {
	VideoLogModel: VideoLogModel,
	VideoLogCollection: VideoLogCollection
};
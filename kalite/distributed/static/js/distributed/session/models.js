SessionModel = Backbone.Model.extend({
    defaults: {
        USER_URL                    : "",

        USER_LOGIN_URL              : "",
        STATIC_URL                  : "",

        ALL_ASSESSMENT_ITEMS_URL    : "",
        GET_VIDEO_LOGS_URL          : "",
        GET_EXERCISE_LOGS_URL       : "",
        GET_CONTENT_LOGS_URL        : "",

        KHAN_EXERCISES_SCRIPT_URL   : "",

        CENTRAL_SERVER_HOST         : "",
        SECURESYNC_PROTOCOL         : "",
        CURRENT_LANGUAGE            : "",

        // Used by updates app
        AVAILABLE_LANGUAGEPACK_URL      : "",
        DEFAULT_LANGUAGE                : ""
    }
});

window.sessionModel = new SessionModel();

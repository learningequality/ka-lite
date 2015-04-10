SessionModel = Backbone.Model.extend({
    defaults: {
        SEARCH_TOPICS_URL           : "",
        SEARCH_URL                  : "",
        USER_URL                    : "",
        FORCE_SYNC_URL              : "",

        LOCAL_DEVICE_MANAGEMENT_URL : "",
        USER_LOGIN_URL              : "",
        SET_DEFAULT_LANGUAGE_URL    : "",
        DELETE_USERS_URL            : "",
        DELETE_GROUPS_URL           : "",
        MOVE_TO_GROUP_URL           : "",
        STATIC_URL                  : "",

        ALL_ASSESSMENT_ITEMS_URL    : "",
        GET_VIDEO_LOGS_URL          : "",
        GET_EXERCISE_LOGS_URL       : "",
        GET_CONTENT_LOGS_URL        : "",

        KHAN_EXERCISES_SCRIPT_URL   : "",

        SERVER_INFO_PATH            : "",
        CENTRAL_SERVER_HOST         : "",
        SECURESYNC_PROTOCOL         : "",
        CURRENT_LANGUAGE            : "",

        // Used by updates app
        START_LANGUAGEPACKDOWNLOAD_URL  : "",
        INSTALLED_LANGUAGES_URL         : "",
        AVAILABLE_LANGUAGEPACK_URL      : "",
        DELETE_LANGUAGEPACK_URL         : "",
        DEFAULT_LANGUAGE                : ""
    }
});

window.sessionModel = new SessionModel();

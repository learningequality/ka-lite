module("Session Model Tests", {
  setup: function() {
    return this.sessionModel = new SessionModel();
  }
});

test("Default values", function() {
  expect(18);

  equal(this.sessionModel.get("SEARCH_TOPICS_URL"), "");
  equal(this.sessionModel.get("USER_URL"), "");
  equal(this.sessionModel.get("FORCE_SYNC_URL"), "");
  equal(this.sessionModel.get("LOCAL_DEVICE_MANAGEMENT_URL"), "");

  equal(this.sessionModel.get("SET_DEFAULT_LANGUAGE_URL"), "");
  equal(this.sessionModel.get("DELETE_USERS_URL"), "");
  equal(this.sessionModel.get("DELETE_GROUPS_URL"), "");
  equal(this.sessionModel.get("MOVE_TO_GROUP_URL"), "");
  equal(this.sessionModel.get("STATIC_URL"), "");

  equal(this.sessionModel.get("ALL_ASSESSMENT_ITEMS_URL"), "");
  equal(this.sessionModel.get("GET_VIDEO_LOGS_URL"), "");
  equal(this.sessionModel.get("GET_EXERCISE_LOGS_URL"), "");
  equal(this.sessionModel.get("GET_CONTENT_LOGS_URL"), "");
  equal(this.sessionModel.get("KHAN_EXERCISES_SCRIPT_URL"), "");

  equal(this.sessionModel.get("SERVER_INFO_PATH"), "");
  equal(this.sessionModel.get("CENTRAL_SERVER_HOST"), "");
  equal(this.sessionModel.get("SECURESYNC_PROTOCOL"), "");
  return equal(this.sessionModel.get("CURRENT_LANGUAGE"), "");
});

/*
The updates app defines some variables we should have set.
This is a regression test for issue 3460.
*/
test("Default values for updates app", function() {
  expect(5);

  equal(this.sessionModel.get("START_LANGUAGEPACKDOWNLOAD_URL"), "");
  equal(this.sessionModel.get("INSTALLED_LANGUAGES_URL"), "");
  equal(this.sessionModel.get("AVAILABLE_LANGUAGEPACK_URL"), "");
  equal(this.sessionModel.get("DELETE_LANGUAGEPACK_URL"), "");
  return equal(this.sessionModel.get("DEFAULT_LANGUAGE"), "");
});

var CoachReportRouter = require("../coach_reports/router");
$ = require("base/jQuery");
Backbone = require("base/backbone");

require("../../../css/coachreports/base.less");

global.$ = $;
global.Backbone = Backbone;

$(function() {
    window.coach_router = new CoachReportRouter({facility: global.FACILITY_ID});
});
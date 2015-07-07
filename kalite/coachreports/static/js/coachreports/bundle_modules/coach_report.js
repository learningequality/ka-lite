var CoachReportRouter = require("../coach_reports/router");
$ = require("base/jQuery");
Backbone = require("base/backbone");

global.$ = $;
global.Backbone = Backbone;

$(function() {
    window.coach_router = new CoachReportRouter();
});
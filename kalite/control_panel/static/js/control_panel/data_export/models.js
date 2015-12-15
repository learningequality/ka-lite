// Handles the data export functionality of the control panel
// TODO-blocker(dylanjbarth) 0.13: limit requests and handle pagination
var Backbone = require("base/backbone");


// Models
var ZoneModel = Backbone.Model.extend();

var FacilityModel = Backbone.Model.extend();

var GroupModel = Backbone.Model.extend();

var DataExportStateModel = Backbone.Model.extend();

// Collections
var ZoneCollection = Backbone.Collection.extend({
    model: ZoneModel,
    url: ALL_ZONES_URL
});

var FacilityCollection = Backbone.Collection.extend({
    model: FacilityModel,
    url: ALL_FACILITIES_URL
});

var GroupCollection = Backbone.Collection.extend({
    model: GroupModel,
    url: ALL_GROUPS_URL
});

module.exports = {
	ZoneModel: ZoneModel,
	FacilityModel: FacilityModel,
	GroupModel: GroupModel,
	DataExportStateModel: DataExportStateModel,
	ZoneCollection: ZoneCollection,
	FacilityCollection: FacilityCollection,
	GroupCollection: GroupCollection
};

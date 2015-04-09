module("ContentPointsView Tests", {
  setup: function() {
    this.view = new window.ContentPointsView();
  }
});

test("Default values", function() {
  expect(1);
  equal(this.starting_points, 0);
});
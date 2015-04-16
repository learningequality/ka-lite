module("TopicContainerInnerView tests", {
  setup: function() {
    options = {
        state_model: new Backbone.Model(),
        entity_key: "blah",
        model: new Backbone.Model(),
        entity_collection: Backbone.Model,
        level: 3,
        has_parent: false
    };
    options.model.set(options.entity_key, new Backbone.Model());
    sinon.stub(TopicContainerInnerView.prototype, "add_all_entries");
    return this.theView = new TopicContainerInnerView(options);
  }
});

test("Resizes when the window is resized or scrolled", function() {
  expect(2);
  sinon.spy(this.theView, "window_scroll_callback");
  sinon.spy(this.theView, "window_resize_callback");

  $(window).resize();
  $(window).scroll();

  ok(this.theView.window_resize_callback.called);
  return ok(this.theView.window_scroll_callback.called);
});
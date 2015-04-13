module("TopicContainerInnerView tests", {
  setup: function() {
    options = {
        state_model: sinon.stub(),
        entity_key: sinon.stub(),
        model: sinon.stub(),
        entity_collection: sinon.stub(),
        level: sinon.stub(),
        has_parent: sinon.stub()
    };
    return this.theView = new TopicContainerInnerView(options);
  }
});

test("Resizes when the window is resized or scrolled", function() {
  expect(2);
  sinon.spy(this.theView, "window_scroll_callback");
  sinon.spy(this.theView, "window_resize_callback");

  $(window).resize();
  $(window).scroll();

  ok(this.theView.window_resize_callback.calledOnce);
  ok(this.theView.window_scroll_callback.calledOnce);
});
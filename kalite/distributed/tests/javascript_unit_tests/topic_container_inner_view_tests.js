module("TopicContainerInnerView tests", {
  setup: function() {
    return this.theView = new TopicContainerInnerView();
  }
});

test("Resizes when the window is resized or scrolled", function() {
  expect(2);
  sinon.spy(this.theView, "window_scroll_callback");
  sinon.spy(this.theView, "window_resize_callback");

  $(window).resize();
  $(window).scroll();

  ok(this.theView.window_resize_callback.calledOnce());
  ok(this.theView.window_scroll_callback.calledOnce());
});
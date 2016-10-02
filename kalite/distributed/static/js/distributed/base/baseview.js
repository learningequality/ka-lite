var Backbone = require("./backbone");
var _ = require("underscore");

module.exports = Backbone.View.extend({


    /**
     * Bind error handling
     */
    initialize: function(options) {
        this.bind("error", this.defaultErrorHandler);
    },

    defaultErrorHandler: function(model, error) {
         if (error.status == 500) {
              $("#ajax_user_error").show();
         }
    },

    /**
     * Add a subview to the view to allow for easy clean up on remove/close.
     * @param {Object} subview_type - The constructor for the view you want to instantiate.
     * @param {Object} options - The options object for instantiating the subview.
     */
    add_subview: function(subview_type, options) {
        this.subviews = this.subviews || [];
        var subview = new subview_type(options);
        this.subviews.push(subview);
        return subview;
    },
    
    /**
     * Bulk append views to the view to allow for minimal repaint when adding many views.
     * @param {Array} view_list - An array of all the views you want to append.
     * @param {String} identifier - CSS selector to use to find the element to append to.
     * This parameter is optional, if omitted, it will simply append to the $el of the view.
     */
    append_views: function(view_list, identifier) {
      var docfrag = document.createDocumentFragment();
      for (i = 0; i < view_list.length; i++) {
        docfrag.appendChild(view_list[i].el);
      }
      if (identifier) {
        return this.$(identifier).append(docfrag);
      } else {
        return this.$el.append(docfrag);
      }
    },

    listenToDOM: function(DOMElement, event_name, callback) {
        if (typeof DOMElement.get === "function") {
            DOMElement = DOMElement.get(0);
        }

        var listeners = [];

        this.listenTo({
            on: function(event, handler, context) {
                DOMElement.addEventListener(event, handler, false);
                listeners.push({
                    args: [event, handler],
                    context: context
                });
            },
            off: function(event, handler, context) {
                listeners = listeners.filter(function(listener) {
                    if (listener.context === context) {
                        // Note (aron): For some devices,
                        // whenever we navigate out of a content view
                        // and remove the view's dom element, the
                        // garbage collector garbage collects the
                        // element before this callback is called, so
                        // we really only want to run this when the
                        // DOMElement is still not null, aka not
                        // garbage collected yet.
                        if (typeof DOMElement !== "undefined" && DOMElement !== null) {
                            DOMElement.removeEventListener.apply(DOMElement, listener.args);
                        }

                        return true;
                    }
                });
            }

        }, event_name, callback);
    },

    remove: function() {

        // make sure we never end up removing the same view twice, in case there's weird circularity
        if (this._removed) return;
        this._removed = true;

        // remove this view using the default Backbone code, which removes the DOM element
        Backbone.View.prototype.remove.call(this);

        // recursively remove this view's subviews, to avoid detached views with zombie listeners
        if (this.subviews!==undefined) {
            for (i=0; i < this.subviews.length; i++) {
                if (_.isFunction(this.subviews[i].close)) {
                    this.subviews[i].close();
                } else {
                    this.subviews[i].remove();
                }
            }
        }
    },

    loading: function(element) {
        if (!this._loading) {
            this._loading = true;
            _.bindAll(this, "load_animation");
            _.delay(this.load_animation, 200, element);
        }
    },

    load_animation: function(element) {
        if (this._loading) {
            if (element) {
                $(element).plainOverlay("show", {fillColor: '#c4d7e3', duration: 200});
            } else {
                this.$el.plainOverlay("show", {fillColor: '#c4d7e3', duration: 200});
            }
        }
    },

    loaded: function(element) {
        this._loading = false;
        if (element) {
            $(element).plainOverlay("hide", {duration: 200});
        } else {
            this.$el.plainOverlay("hide", {duration: 200});
        }
    }
});

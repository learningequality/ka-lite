window.BaseView = Backbone.View.extend({

    add_subview: function(subview_type, options) {
        this.subviews = this.subviews || [];
        var subview = new subview_type(options);
        this.subviews.push(subview);
        return subview;
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
                        DOMElement.removeEventListener.apply(DOMElement, listener.args);
                        return true;
                    }
                });
            }
        
        }, event_name, callback);
    },

    remove: function() {
        if (this.subviews!==undefined) {
            for (i=0; i < this.subviews.length; i++) {
                if (_.isFunction(this.subviews[i].close)) {
                    this.subviews[i].close();
                } else {
                    this.subviews[i].remove();
                }
            }
        }
        Backbone.View.prototype.remove.call(this);
    }
});
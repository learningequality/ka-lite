window.BaseView = Backbone.View.extend({
    listenToDOM: function(DOMElement, event_name, callback) {
        if (typeof el.get === "function") {
            el = el.get(0);
        }
        
        var listeners = [];
        
        this.listenTo({
            on: function(event, handler, context) {
                el.addEventListener(event, handler, false);
                listeners.push({
                    args: [event, handler],
                    context: context
                });
            },
            off: function(event, handler, context) {
                listeners = listeners.filter(function(listener) {
                    if (listener.context === context) {
                        el.removeEventListener.apply(el, listener.args);
                        return true;
                    }
                });
            }
        
        }, event_name, callback);
    }
});
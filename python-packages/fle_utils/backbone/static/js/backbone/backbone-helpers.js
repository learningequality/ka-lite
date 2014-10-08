window.BaseView = Backbone.View.extend({
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
    }
});
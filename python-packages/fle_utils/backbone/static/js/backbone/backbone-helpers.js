// EventListener add and remove polyfill
if (!Element.prototype.addEventListener) {
  var oListeners = {};
  function runListeners(oEvent) {
    if (!oEvent) { oEvent = window.event; }
    for (var iLstId = 0, iElId = 0, oEvtListeners = oListeners[oEvent.type]; iElId < oEvtListeners.aEls.length; iElId++) {
      if (oEvtListeners.aEls[iElId] === this) {
        for (iLstId; iLstId < oEvtListeners.aEvts[iElId].length; iLstId++) { oEvtListeners.aEvts[iElId][iLstId].call(this, oEvent); }
        break;
      }
    }
  }
  Element.prototype.addEventListener = function (sEventType, fListener /*, useCapture (will be ignored!) */) {
    if (oListeners.hasOwnProperty(sEventType)) {
      var oEvtListeners = oListeners[sEventType];
      for (var nElIdx = -1, iElId = 0; iElId < oEvtListeners.aEls.length; iElId++) {
        if (oEvtListeners.aEls[iElId] === this) { nElIdx = iElId; break; }
      }
      if (nElIdx === -1) {
        oEvtListeners.aEls.push(this);
        oEvtListeners.aEvts.push([fListener]);
        this["on" + sEventType] = runListeners;
      } else {
        var aElListeners = oEvtListeners.aEvts[nElIdx];
        if (this["on" + sEventType] !== runListeners) {
          aElListeners.splice(0);
          this["on" + sEventType] = runListeners;
        }
        for (var iLstId = 0; iLstId < aElListeners.length; iLstId++) {
          if (aElListeners[iLstId] === fListener) { return; }
        }
        aElListeners.push(fListener);
      }
    } else {
      oListeners[sEventType] = { aEls: [this], aEvts: [ [fListener] ] };
      this["on" + sEventType] = runListeners;
    }
  };
  Element.prototype.removeEventListener = function (sEventType, fListener /*, useCapture (will be ignored!) */) {
    if (!oListeners.hasOwnProperty(sEventType)) { return; }
    var oEvtListeners = oListeners[sEventType];
    for (var nElIdx = -1, iElId = 0; iElId < oEvtListeners.aEls.length; iElId++) {
      if (oEvtListeners.aEls[iElId] === this) { nElIdx = iElId; break; }
    }
    if (nElIdx === -1) { return; }
    for (var iLstId = 0, aElListeners = oEvtListeners.aEvts[nElIdx]; iLstId < aElListeners.length; iLstId++) {
      if (aElListeners[iLstId] === fListener) { aElListeners.splice(iLstId, 1); }
    }
  };
}




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
                        // Note (aron): For some devices,
                        // whenever we navigate out of a content view
                        // and remove the view's dom element, the
                        // garbage collector garbage collects the
                        // element before this callback is called, so
                        // we really only want to run this when the
                        // DOMElement is still not null, aka not
                        // garbage collected yet.
                        if (DOMElement) {
                            DOMElement.removeEventListener.apply(DOMElement, listener.args);
                        }

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

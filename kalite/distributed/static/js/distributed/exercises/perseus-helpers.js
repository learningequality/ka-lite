var _ = require("underscore");
var Backbone = require("base/backbone");
var $ = require("base/jQuery");

require("es5-shim");
global.React = require("react");
global.React.__internalReactMount = require("react-mount");
global.React.__internalReactDOM = require("react-dom");
global.ReactDOM = global.React.__internalReactDOM;

global.React.addons = global.React.__internalAddons = {
  CSSTransitionGroup: require("react-addons-css-transition-group"),
  LinkedStateMixin: require("react-addons-linked-state-mixin"),
  PureRenderMixin: require("react-addons-pure-render-mixin"),
  TransitionGroup: require("react-addons-transition-group"),

  batchedUpdates: global.React.unstable_batchedUpdates,
  cloneWithProps: require("react-addons-clone-with-props"),
  createFragment: require("react-addons-create-fragment"),
  shallowCompare: require("react-addons-shallow-compare"),
  update: require("react-addons-update")
};

global.katex = require("katex");
require("../perseus/lib/katex/katex.css");
require("../perseus/lib/mathquill/mathquill-basic.js");
require("../perseus/lib/mathquill/mathquill.css");
require("../perseus/lib/kas.js");
global.Jed = require("jed");
require("../perseus/ke/local-only/i18n");
$._ = global.i18n._;
require("qtip2");

var KhanUtil = window.KhanUtil || {};

var Khan = window.Khan || {
    error: function() {},
    query: {debug: ""},
    imageBase: window.sessionModel.get("STATIC_URL") + "js/distributed/perseus/ke/images/",
    urlBase: window.sessionModel.get("STATIC_URL") + "js/distributed/perseus/ke/",
    scratchpad: {
        disable: function() {},
        enable: function() {},
        clear: function() {},
        resize: function() {}
    },
    cleanupProblem: function() {},
    warnTimeout: function() {}
};

var Exercises = _.extend({
    localMode: true,
    embeddedMode: true,
    useKatex: true,
    khanExercisesUrlBase: window.sessionModel.get("STATIC_URL") + "perseus/ke/",
    _current_framework: "khan-exercises",
    getCurrentFramework: function() {
        return Exercises._current_framework;
    },
    setCurrentFramework: function(framework) {
        Exercises._current_framework = framework;
    },
    completeStack: {
        getUid: function() { return 0; },
        getCustomStackID: function() { return 0; }
    },
    currentCard: {
        attributes: {},
        get: function() {}
    },
    RelatedVideos: {
        render: function() {}
    },
    incompleteStack: [0],
    // This method allows an event triggered by jQuery to be retriggered as a Backbone Event.
    proxyTrigger: function () {
        // Get the type of event from the first argument (which is the event object itself)
        // Add this as the first argument of the arguments object
        Array.prototype.unshift.apply(arguments, [arguments[0].type]);
        // Call Backbone event trigger with the event name as the first argument
        // and the other arguments as the remainders.
        // Using/modifying the arguments object in this way means we can just pass
        // any arguments seamlessly through to the event.
        this.trigger.apply(this, arguments);
    }
}, Backbone.Events);


// This is necessary as DOM events (as fired by jQuery) are not listenedTo by Backbone listenTo
// Our pass through listenToDOM does not work for Javascript objects, only for true DOM objects.
// So we must manually proxy any triggered events on the Exercises object to Backbone triggers.
$(Exercises).bind({
    checkAnswer: Exercises.proxyTrigger,
    gotoNextProblem: Exercises.proxyTrigger,
    newProblem: Exercises.proxyTrigger,
    newProblemhintUsed: Exercises.proxyTrigger,
    hintUsed: Exercises.proxyTrigger
});

// React.initializeTouchEvents(true);

Exercises.PerseusBridge = {

    // this one needs to be here for khan-exercises
    scoreInput: function() {
        return Exercises.PerseusBridge.itemRenderer.scoreInput();
    },

    getSeedInfo: function() {
        return Exercises.PerseusBridge.itemRenderer.props.item;
    },

    getNumHints: function() {
        return Exercises.PerseusBridge.itemRenderer.getNumHints();
    },

    // this one needs to be here for khan-exercises
    cleanupProblem: function(data) {
        if (Exercises.PerseusBridge.itemMountNode) {
            ReactDOM.unmountComponentAtNode(Exercises.PerseusBridge.itemMountNode);
            Exercises.PerseusBridge.itemMountNode = null;
            return true;
        } else {
            return false;
        }
    },

    // returns a Deferred that is resolved when Perseus is loaded and ready
    load: function() {

        // if we've already started loading Perseus, just return the existing Deferred
        if (Exercises.PerseusBridge._loaded) {
            return Exercises.PerseusBridge._loaded;
        } else { // otherwise, create a Deferred
            Exercises.PerseusBridge._loaded = $.Deferred();
        }

        // Load khan-exercises modules, then perseus
        require("../perseus/ke-deps.js");
        var Perseus = require("../perseus/build/perseus-5.js");
        Exercises.PerseusBridge._initialize(Perseus);

        return Exercises.PerseusBridge._loaded;
    },

    _initialize: function(Perseus) {

        window.Perseus = Perseus;

        Perseus.init({
            skipMathJax: false
        }).then(function() {
            Exercises.PerseusBridge._loaded.resolve();
        });

    },

    render_item: function(item_data) {

        Exercises.PerseusBridge.itemMountNode = document.createElement("div");

        var ItemRenderer = React.createFactory(Perseus.ItemRenderer);
        Exercises.PerseusBridge.itemRenderer = zk = ReactDOM.render(ItemRenderer({
            item: item_data,
            problemNum: Math.floor(Math.random() * 50) + 1,
            initialHintsVisible: 0,
            enabledFeatures: {
                highlight: true,
                toolTipFormats: true
            }
        }, null), Exercises.PerseusBridge.itemMountNode);
        zk.focus();

        // First, unbind any old listeners, otherwise multiple hints will be shown at a time
        $(Exercises.PerseusBridge).unbind("showHint");

        // Show the hint, and decrement the hint count
        $(Exercises.PerseusBridge).bind("showHint", function(data) {
            zk.showHint();
            $(Exercises).trigger("hintShown");
        });

    }

};

global.Exercises = Exercises;
global.Khan = Khan;

require("../perseus/ke/interface.js");

module.exports = {
    KhanUtil: KhanUtil,
    Khan: Khan,
    Exercises: Exercises
};
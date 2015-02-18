var KhanUtil = window.KhanUtil || {};

var Khan = window.Khan || {
    error: function() {},
    query: {debug: ""},
    imageBase: STATIC_URL + "perseus/ke/images/",
    urlBase: STATIC_URL + "perseus/ke/",
    scratchpad: {
        disable: function() {},
        enable: function() {},
        clear: function() {},
        resize: function() {}
    },
    cleanupProblem: function() {}
};

window.Exercises = _.extend({
    localMode: true,
    embeddedMode: true,
    useKatex: true,
    khanExercisesUrlBase: STATIC_URL + "perseus/ke/",
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
    newProblemhintUsed: Exercises.proxyTrigger
});

// React.initializeTouchEvents(true);

Exercises.PerseusBridge = {

    // this one needs to be here for khan-exercises
    scoreInput: function() {
        return Exercises.PerseusBridge.itemRenderer.scoreInput();
    },

    // this one needs to be here for khan-exercises
    cleanupProblem: function(data) {
        if (Exercises.PerseusBridge.itemMountNode) {
            React.unmountComponentAtNode(Exercises.PerseusBridge.itemMountNode);
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
        require([
                STATIC_URL + "perseus/ke-deps.js"
                // STATIC_URL + "perseus/ke/main.js",
            ], function() {
                require([STATIC_URL + "perseus/build/perseus-2.js"], Exercises.PerseusBridge._initialize);
            }
        );

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
        Exercises.PerseusBridge.itemRenderer = zk = React.render(ItemRenderer({
            item: item_data,
            problemNum: Math.floor(Math.random() * 50) + 1,
            initialHintsVisible: false,
            enabledFeatures: {
                highlight: true,
                toolTipFormats: true
            }
        }, null), Exercises.PerseusBridge.itemMountNode);
        zk.focus();

    }

};

// $(Exercises).trigger("clearExistingProblem");

var KhanUtil = window.KhanUtil || {
    debugLog: function() {}
};

var Khan = window.Khan || {
    Util: KhanUtil,
    error: function() {},
    query: {debug: ""},
    imageBase: STATIC_URL + "perseus/ke/images/",
    scratchpad: {
        disable: function() {},
        enable: function() {},
        clear: function() {}
    },
    cleanupProblem: function() {}
};

window.Exercises = {
    localMode: true,
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
    incompleteStack: [0]
};

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
                require([STATIC_URL + "perseus/build/perseus-1.js"], Exercises.PerseusBridge._initialize);
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
        var itemRenderer = Exercises.PerseusBridge.itemRenderer = Perseus.ItemRenderer({
            item: item_data,
            problemNum: Math.floor(Math.random() * 50) + 1,
            initialHintsVisible: false, //&& item_data.hints && item_data.hints.length,
            enabledFeatures: {
                highlight: true,
                toolTipFormats: true//,
                //useMathQuill: true
            },
            apiOptions: {
                // interceptInputFocus: function() {}, // do nothing here; prevent keyboard from popping up
                // fancyDropdowns: true // needed?
                // staticRender: true // don't want; iOS mode, blocks input box rendering
            }
        }, null);
        zk = React.renderComponent(
            Exercises.PerseusBridge.itemRenderer,
            Exercises.PerseusBridge.itemMountNode
        );
        zk.focus();

    }

};

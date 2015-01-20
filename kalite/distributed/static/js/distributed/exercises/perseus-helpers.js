// $(Exercises).trigger("clearExistingProblem");

var icu = {
    getDecimalFormatSymbols: function() {
        return {
            decimal_separator: ".",
            grouping_separator: ",",
            minus: "-"
        };
    },
    getLanguage: function() {
        return "en";
    }
};


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

window.Exercises = {
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
        requirejs([
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

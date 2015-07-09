// For legacy reasons, Perseus assumes that some modules (such as knumber) are
// executed immediately when the exercise content bundle is loaded, so we load
// them all here.

require("./khan-exercise.js");

require("./utils/answer-types.js");
require("./utils/graphie.js");
require("./utils/interactive.js");
require("./utils/kline.js");
require("./utils/knumber.js");
require("./utils/kpoint.js");
require("./utils/kray.js");
require("./utils/kvector.js");
require("./utils/math.js");
require("./utils/answer-types.js");
require("./utils/tmpl.js");
require("./utils/tex.js");
require("./utils/jquery.adhesion.js");
require("./utils/scratchpad.js");
require("./utils/subhints.js");
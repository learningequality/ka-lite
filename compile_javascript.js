var browserify = require('browserify');
var hbsfy = require("hbsfy")
var fs = require("fs");
var _ = require("underscore");

var watch = false;
var debug = false;

if (process.argv.indexOf("--watch") > -1 || process.argv.indexOf("-w") > -1) {
    watch = true;
}

if (process.argv.indexOf("--debug") > -1 || process.argv.indexOf("-d") > -1) {
    debug = true;
}

fs.readdir("kalite", function(err, filenames) {
    var bundles = [];
    var module_paths = [];
    for (var i = 0; i < filenames.length; i++) {
        var module_path = "kalite/" + filenames[i] + "/static/js/" + filenames[i];
        if (fs.existsSync(module_path)) {
            module_paths.push(module_path);
        }
        var bundle_path = "kalite/" + filenames[i] + "/static/js/" + filenames[i] + "/bundle_modules";
        if (fs.existsSync(bundle_path)) {
            var dir_bundles = fs.readdirSync(bundle_path);
            for (var j = 0; j < dir_bundles.length; j++) {
                bundles.push({
                    target_file: "kalite/" + filenames[i] + "/static/js/" + filenames[i] + "/bundles/" + "bundle_" + dir_bundles[j],
                    bundle: bundle_path + "/" + dir_bundles[j]
                });
            }
            if (dir_bundles.length > 0) {
                if (!fs.existsSync("kalite/" + filenames[i] + "/static/js/" + filenames[i] + "/bundles")) {
                    fs.mkdirSync("kalite/" + filenames[i] + "/static/js/" + filenames[i] + "/bundles");
                }
            }
        }
    }

    console.log("Found " + bundles.length + " bundle" + bundles.length !== 1 ? "s" : "" + ", compiling.");

    if (!fs.existsSync("kalite/distributed/static/js/distributed/bundles")) {
        fs.mkdirSync("kalite/distributed/static/js/distributed/bundles");
    }

    var b = browserify(_.map(bundles, function(item) {return item.bundle;}), {
        paths: module_paths,
        cache: {},
        packageCache: {},
        debug: true,
    });

    b.transform(hbsfy);

    b.plugin('factor-bundle', { outputs: _.map(bundles, function(item) {return item.target_file;}) });

    if (watch) {
        var watchify = require("watchify");
        b = watchify(b, {
            verbose: true
        });
        console.log("Starting watcher");
        b.on('update', function (ids) {
            console.log('files changed, bundle updated');
            console.dir(ids);
            b.transform(hbsfy);
            b.plugin('factor-bundle', { outputs: _.map(bundles, function(item) {return item.target_file;}) });
            b.bundle().pipe(fs.createWriteStream('kalite/distributed/static/js/distributed/bundles/bundle_common.js'));
        });
        b.on('log', function(msg) {
            console.log(msg);
        });
    }

    // Don't use minifyify except in production.
    if (!debug) {
        b.plugin('minifyify', {map: false});
    }
    b.bundle().pipe(fs.createWriteStream('kalite/distributed/static/js/distributed/bundles/bundle_common.js'));
    console.log("Bundles written.");
});
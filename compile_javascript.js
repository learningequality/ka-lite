var browserify = require('browserify');
var hbsfy = require("hbsfy")
var fs = require("fs");
var _ = require("underscore");

var watch = false;
var debug = false;
var staticfiles = false;

if (process.argv.indexOf("--watch") > -1 || process.argv.indexOf("-w") > -1) {
    watch = true;
}

if (process.argv.indexOf("--debug") > -1 || process.argv.indexOf("-d") > -1) {
    debug = true;
}

if (process.argv.indexOf("--staticfiles") > -1 || process.argv.indexOf("-s") > -1) {
    staticfiles = true;
}

var log = function(msg) {
    console.log("Watchify: " + msg);
}

var create_bundles = function (b, bundles) {
    b.plugin('factor-bundle', { outputs: _.map(bundles, function(item) {return item.target_file;}) });
    // Don't use minifyify except in production.
    if (!debug) {
        b.plugin('minifyify', {map: false});
    }
    try {
        b.bundle(function(err, buf){
            if (err) {
                log(err);
            } else {
                fs.createWriteStream('kalite' + (staticfiles ? '' : '/distributed') + '/static/js/distributed/bundles/bundle_common.js').write(buf);
                log(bundles.length + " Bundles written.");
            }
        });
    }
    catch (err) {
        log(err);
    }
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
                    target_file: "kalite" + (staticfiles ? '' :  "/" + filenames[i]) + "/static/js/" + filenames[i] + "/bundles/" + "bundle_" + dir_bundles[j],
                    bundle: bundle_path + "/" + dir_bundles[j],
                    alias: dir_bundles[j].split(".").slice(0,-1).join(".")
                });
            }
            if (dir_bundles.length > 0) {
                if (!fs.existsSync("kalite" + (staticfiles ? '' :  "/" + filenames[i]) + "/static/js/" + filenames[i] + "/bundles")) {
                    fs.mkdirSync("kalite" + (staticfiles ? '' :  "/" + filenames[i]) + "/static/js/" + filenames[i] + "/bundles");
                }
            }
        }
    }

    log("Found " + bundles.length + " bundle" + (bundles.length !== 1 ? "s" : "") + ", compiling.");

    if (!fs.existsSync('kalite' + (staticfiles ? '' : '/distributed') + '/static/js/distributed/bundles/')) {
        fs.mkdirSync('kalite' + (staticfiles ? '' : '/distributed') + '/static/js/distributed/bundles/');
    }

    var b = browserify({
        paths: module_paths,
        cache: {},
        packageCache: {},
        debug: true,
    });

    _.each(bundles, function(item) {b.add(item.bundle, {expose: item.alias});})

    b.transform(hbsfy);

    if (watch) {
        var watchify = require("watchify");
        b = watchify(b, {
            verbose: true
        });
        log("Starting watcher");
        b.on('update', function (ids) {
            log('files changed, bundle updated');
            _.each(ids, function(id) {log(id + " changed");});
            create_bundles(b, bundles);
        });
        b.on('log', log);
        b.on('error', function(error) {
            log(error);
            this.emit("end");
        });
    }

    create_bundles(b, bundles);
});
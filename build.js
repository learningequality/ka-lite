var browserify = require('browserify');
var lessify = require('node-lessify');
var hbsfy = require("hbsfy")
var deamdify = require("./javascript_build/deamdify");
var fs = require("fs");
var _ = require("underscore");
var hintify = require("hintify");
var colors = require("colors");
var async = require("async");

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

var log = function(msg, color) {
    console.log(color("Watchify: " + msg));
}

logging = {
    warn: function(msg) {
        log(msg, colors.yellow);
    },

    info: function(msg) {
        log(msg, colors.green);
    },

    error: function(msg) {
        log(msg, colors.red);
    }
};
 
var format_jshint = function(error) {
    return error.severity + ": in " + error.file + ", " + error.message + " line: " + error.line + " col: " + error.column;
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
                logging.error(err);
            } else {
                fs.createWriteStream('kalite' + (staticfiles ? '' : '/distributed') + '/static/js/distributed/bundles/bundle_common.js').write(buf);
                logging.info(bundles.length + " Bundles written.");
            }
        });
    }
    catch (err) {
        logging.error(err);
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

    logging.info("Found " + bundles.length + " bundle" + (bundles.length !== 1 ? "s" : "") + ", compiling.");

    if (!fs.existsSync('kalite' + (staticfiles ? '' : '/distributed') + '/static/js/distributed/bundles/')) {
        fs.mkdirSync('kalite' + (staticfiles ? '' : '/distributed') + '/static/js/distributed/bundles/');
    }

    var b = browserify({
        paths: module_paths,
        cache: {},
        packageCache: {},
        debug: true,
    });

    // Special transform to turn all Khan Exercise utils files into CommonJS modules using deamdify



    var kalite_utils_dir = "kalite/distributed/static/js/distributed/perseus/ke/utils";

    if (!fs.existsSync(kalite_utils_dir + "/../backuputils")) {

        // Assume if the backup exists then we don't need to do this

        logging.warn("DeAMDifying Khan Exercise Util Files");

        var util_files = fs.readdirSync(kalite_utils_dir);

        if (!staticfiles) {

            fs.mkdirSync(kalite_utils_dir + "/../backuputils");

        }

        util_files = _.map(util_files, function(file_name){
            return {
                target_file: "kalite" + (staticfiles ? '' : '/distributed') + "/static/js/distributed/perseus/ke/utils" + "/" + file_name,
                bundle: kalite_utils_dir + "/" + file_name,
                alias: "khan_utils_" + file_name.split(".").slice(0,-1).join("."),
                backup_file: kalite_utils_dir + "/../backuputils/" + file_name
            };});

        var redefine = function(err) {
            if (!err) {
                async.each(util_files, function(item, callback) {
                    var brow = browserify(staticfiles ? item.bundle : item.backup_file);
                    brow.transform(deamdify);
                    brow.plugin('minifyify', {map: false});
                    var out = brow.bundle()
                    out.pipe(fs.createWriteStream(item.target_file));
                    logging.info("Writing " + item.alias);
                    out.on('end', callback);
                });
            } else {
                logging.error(err);
            }
        }

        if (!staticfiles) {
            async.each(util_files, function(item, callback) {
                    var out = fs.createReadStream(item.bundle)
                    out.pipe(fs.createWriteStream(item.backup_file));
                    out.on('end', callback);
                }, redefine);
        } else {
            redefine();
        }

    } else {
        logging.warn("Assuming that Khan Util files are already deAMDified");
    }


    _.each(bundles, function(item) {b.add(item.bundle, {expose: item.alias});})

    // Run jshint first to avoid unnecessary errors due to Syntax.
    b.transform(hintify);
    b.transform(hbsfy);
    
    b.transform(deamdify);
    b.transform(lessify, {global: true});

    if (watch) {
        var watchify = require("watchify");
        b = watchify(b, {
            verbose: true
        });
        logging.info("Starting watcher");
        b.on('update', function (ids) {
            logging.info('files changed, bundle updated');
            _.each(ids, function(id) {logging.info(id + " changed");});
            create_bundles(b, bundles);
        });
    }

    b.on('log', logging.info);
    b.on('error', function(error) {
        logging.error(error);
        this.emit("end");
    });

    create_bundles(b, bundles);
});
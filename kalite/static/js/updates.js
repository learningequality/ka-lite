// Storage variables for this app
var process_names = {};  // (string) indices into all arrays
var process_ids = {};    // ID of updated process information
var process_intervals = {}
var process_interval_handles = {}
var process_callbacks = {}

$(function() {
    $(".progressbar-overall").progressbar({
        value: 0,
        max: 100
    });

    $(".progressbar-current").progressbar({
        value: 0,
        max: 100
    });
});

/* Three functions to support updates:
  updatesStart - triggers the process
  updatesCheck - checks (in a callback loop)
  updatesReset - resets
*/
function has_a_val(key, obj) {
    return key in obj && obj[key];
}

function updatesStart(process_name, interval, callbacks) {
    // Starts looking for updates
    clear_message("id_" + process_name)
    // Store the info
    if (! process_name in process_names) {
        process_names[process_name] = true;
//        = process_names.concat(process_name);
    }
    process_intervals[process_name] = interval ? interval : 5000;
    process_callbacks[process_name] = callbacks;

    // Make sure to reset any old intervals
    if (has_a_val(process_name, process_interval_handles)) {
        clearInterval(process_interval_handles[process_name]);
    }

    process_interval_handles[process_name] = setInterval(
        function () { updatesStart_callback(process_name); },
        process_intervals[process_name]
    );

    updatesStart_callback(process_name);
}

function updatesStart_callback(process_name) {
        // Start the background process
        doRequest("/api/updates/progress?process_name=" + process_name)
            .success(function(progress_log) {
                // Store the info
                var process_name = progress_log.process_name
                if (!process_name) {
                    // Start failed; can exit because this will repeat.
                    return;
                }
                if (!has_a_val(process_name, process_ids)) {
                    process_ids[process_name] = progress_log.process_id
                }

                // Launch a looping timer to call into the update check function
                if (!progress_log.completed) {
                    // Clear interval for start
                    if (has_a_val(process_name, process_interval_handles)) {
                        clearInterval(process_interval_handles[process_name]);
                    }
                    // Create interval for check
                    process_interval_handles[process_name] = setInterval( // call it soon
                        function() { updatesCheck(process_name); }, 
                        process_intervals[process_name]
                    );
                    updatesCheck(process_name);  // call it once directly
                }

                // Do callbacks
                if (process_callbacks[process_name] && "start" in process_callbacks[process_name]) {
                    process_callbacks[process_name]["start"](progress_log);
                }
            }).fail(function(resp) {
                show_message("error", "Error during updatesStart_callback: " + resp.responseText);
                // Do callbacks
                if (process_callbacks[process_name] && "start" in process_callbacks[process_name]) {
                    process_callbacks[process_name]["start"](null, resp);
                }
            });
}

function updatesCheck(process_name, interval) {
    // Check on current updates progress

    // Get progress either generically (by the process_name, giving us the latest progress available),
    //    or by the process_id (connecting us to a specific process.)
    var path = "/api/updates/progress?process_" + (has_a_val(process_name, process_ids) ? ("id=" + process_ids[process_name]) : ("name=" + process_name));
    doRequest(path)
        .success(function(progress_log) {
            var completed = !progress_log.process_name || progress_log.completed;

            // Reasons to exit
            if (completed) {
                // 
                if (progress_log.process_percent == 1.) {
                    show_message("info", "Completed update '" + process_name + "' successfully.", "id_" + process_name)
                    updatesReset(process_name);
                } else if (progress_log.process_name) {
                    show_message("error", "Error during update: " + progress_log.notes, "id_" + process_name);
                    updatesReset(process_name);
                } else {
                }
                //return
            } else if (!process_intervals[process_name]) {
                // If cancelled, stop the madness!
                return;
            }

            if (!has_a_val(process_name, process_ids)) {
                process_ids[process_name] = progress_log.process_id
            }

            // Update the UI
            updateDisplay(process_name, progress_log);

            // Do callbacks
            if (process_callbacks[process_name] && "check" in process_callbacks[process_name]) {
                process_callbacks[process_name]["check"](progress_log);
            }
        }).fail(function(resp) {
            show_message("error", "Error during updatesCheck: " + resp.responseText);
            updatesReset(process_name);
            // Do callbacks
            if (process_callbacks[process_name] && "check" in process_callbacks[process_name]) {
                process_callbacks[process_name]["check"](null, resp);
            }
        });
}

function select_update_elements(process_name, selector) {
    var pb_selector = "#" + process_name + "-progressbar";
    return  $(pb_selector + " " + selector);
}
 
function updateDisplay(process_name, progress_log) {
    window.progress_log = progress_log;
    window.process_name = process_name;
    if (progress_log.completed) {
        select_update_elements(process_name, ".progress-section").hide();
    } else {
        select_update_elements(process_name, ".progress-section").show();
    }

    // Update the UI
    //     Update the progress bars
    select_update_elements(process_name, ".progressbar-current").progressbar({value: 100*progress_log.stage_percent});
    select_update_elements(process_name, ".progressbar-overall").progressbar({value: 100*progress_log.process_percent});

    select_update_elements(process_name, ".stage-current").text(progress_log.cur_stage_num);
    select_update_elements(process_name, ".stage-total").text(progress_log.total_stages);

    select_update_elements(process_name, ".stage-header").text(progress_log.notes);
    select_update_elements(process_name, ".stage-name").text("");

    // Do callbacks
    if (process_callbacks[process_name] && "display" in process_callbacks[process_name]) {
        process_callbacks[process_name]["display"](progress_log);
    }
}


function updatesReset(process_name) {

    // With no args, reset all
    if (!process_name) {
        for (pn in process_names) {
            updatesReset(pn);
        }
        return;
    }

    // Clear all internal functionality
    clearInterval(process_interval_handles[process_name]);

    // Do callbacks
    if (process_callbacks[process_name] && "reset" in process_callbacks[process_name]) {
        process_callbacks[process_name]["reset"](progress_log);
    }

    // Clean up UI
    select_update_elements(process_name, ".progress-section").hide();

    // Delete data
    process_callbacks[process_name] = null
    process_ids[process_name] = null;
    process_intervals[process_name] = null;
    process_interval_handles[process_name];

    if (process_name in process_names) { 
        delete process_names[process_name];
    }

}

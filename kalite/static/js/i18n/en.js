
/* gettext library */

var catalog = new Array();

function pluralidx(n) {
  var v=(n != 1);
  if (typeof(v) == 'boolean') {
    return v ? 1 : 0;
  } else {
    return v;
  }
}
catalog['%(points)d points!'] = '%(points)d points!';
catalog['%(subtitle_count)d Subtitles / %(percent_translated)d%% Translated'] = '%(subtitle_count)d Subtitles / %(percent_translated)d%% Translated';
catalog['%(username)s (Logout)'] = '%(username)s (Logout)';
catalog['An error occurred while contacting the server to start the download process'] = 'An error occurred while contacting the server to start the download process';
catalog['Completed update successfully.'] = 'Completed update successfully.';
catalog['Could not connect to the server.'] = 'Could not connect to the server.';
catalog['Delete %(vid_count)d selected video(s)'] = 'Delete %(vid_count)d selected video(s)';
catalog['Download %(vid_count)d new selected video(s)'] = 'Download %(vid_count)d new selected video(s)';
catalog['Download for language %s started.'] = 'Download for language %s started.';
catalog['Error canceling downloads'] = 'Error canceling downloads';
catalog['Error downloading subtitles'] = 'Error downloading subtitles';
catalog['Error downloading videos'] = 'Error downloading videos';
catalog['Error during update: %(progress_log_notes)s'] = 'Error during update: %(progress_log_notes)s';
catalog['Error getting search data'] = 'Error getting search data';
catalog['Error restarting downloads'] = 'Error restarting downloads';
catalog['Error starting updates process'] = 'Error starting updates process';
catalog['Error starting video download'] = 'Error starting video download';
catalog['Error while checking update status: %(message)s'] = 'Error while checking update status: %(message)s';
catalog['None; Please select now'] = 'None; Please select now';
catalog['Overall progress: %(percent_complete)5.2f%% complete (%(cur_stage)d of %(num_stages)d)'] = 'Overall progress: %(percent_complete)5.2f%% complete (%(cur_stage)d of %(num_stages)d)';
catalog['Set as default'] = 'Set as default';
catalog['Subtitles'] = 'Subtitles';
catalog['Successfully launched data syncing job. After syncing completes, visit the <a href=\'/management/device/\'>device management page</a> to view results.'] = 'Successfully launched data syncing job. After syncing completes, visit the <a href=\'/management/device/\'>device management page</a> to view results.';
catalog['The server does not have internet access; new content cannot be downloaded at this time.'] = 'The server does not have internet access; new content cannot be downloaded at this time.';
catalog['Total Points : %(points)d '] = 'Total Points : %(points)d ';
catalog['Translated'] = 'Translated';
catalog['Unexpected error: no search data found for selected item. Please select another item.'] = 'Unexpected error: no search data found for selected item. Please select another item.';
catalog['Uninterpretable message received.'] = 'Uninterpretable message received.';
catalog['Update cancelled successfully.'] = 'Update cancelled successfully.';
catalog['Upgrade'] = 'Upgrade';
catalog['You are not authorized to complete the request.  Please <a href=\'/securesync/login/\' target=\'_blank\'>login</a> as an administrator, then retry.'] = 'You are not authorized to complete the request.  Please <a href=\'/securesync/login/\' target=\'_blank\'>login</a> as an administrator, then retry.';
catalog['problem on server.'] = 'problem on server.';


function gettext(msgid) {
  var value = catalog[msgid];
  if (typeof(value) == 'undefined') {
    return msgid;
  } else {
    return (typeof(value) == 'string') ? value : value[0];
  }
}

function ngettext(singular, plural, count) {
  value = catalog[singular];
  if (typeof(value) == 'undefined') {
    return (count == 1) ? singular : plural;
  } else {
    return value[pluralidx(count)];
  }
}

function gettext_noop(msgid) { return msgid; }

function pgettext(context, msgid) {
  var value = gettext(context + '' + msgid);
  if (value.indexOf('') != -1) {
    value = msgid;
  }
  return value;
}

function npgettext(context, singular, plural, count) {
  var value = ngettext(context + '' + singular, context + '' + plural, count);
  if (value.indexOf('') != -1) {
    value = ngettext(singular, plural, count);
  }
  return value;
}

function interpolate(fmt, obj, named) {
  if (named) {
    return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
  } else {
    return fmt.replace(/%s/g, function(match){return String(obj.shift())});
  }
}

/* formatting library */

var formats = new Array();

formats['DATETIME_FORMAT'] = 'N j, Y, P';
formats['DATE_FORMAT'] = 'N j, Y';
formats['DECIMAL_SEPARATOR'] = '.';
formats['MONTH_DAY_FORMAT'] = 'F j';
formats['NUMBER_GROUPING'] = '0';
formats['TIME_FORMAT'] = 'P';
formats['FIRST_DAY_OF_WEEK'] = '0';
formats['TIME_INPUT_FORMATS'] = ['%H:%M:%S', '%H:%M'];
formats['THOUSAND_SEPARATOR'] = ',';
formats['DATE_INPUT_FORMATS'] = ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%b %d %Y', '%b %d, %Y', '%d %b %Y', '%d %b, %Y', '%B %d %Y', '%B %d, %Y', '%d %B %Y', '%d %B, %Y'];
formats['YEAR_MONTH_FORMAT'] = 'F Y';
formats['SHORT_DATE_FORMAT'] = 'm/d/Y';
formats['SHORT_DATETIME_FORMAT'] = 'm/d/Y P';
formats['DATETIME_INPUT_FORMATS'] = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S.%f', '%m/%d/%Y %H:%M', '%m/%d/%Y', '%m/%d/%y %H:%M:%S', '%m/%d/%y %H:%M:%S.%f', '%m/%d/%y %H:%M', '%m/%d/%y'];

function get_format(format_type) {
    var value = formats[format_type];
    if (typeof(value) == 'undefined') {
      return msgid;
    } else {
      return value;
    }
}

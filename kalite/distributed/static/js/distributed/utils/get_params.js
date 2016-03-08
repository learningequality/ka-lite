var getParamValue = (function() {
    var params;
    var resetParams = function() {
            var query = window.location.search;
            var regex = /[?&;](.+?)=([^&;]+)/g;
            var match;

            params = {};

            if (query) {
                while((match = regex.exec(query)) !== null) {
                    params[match[1]] = decodeURIComponent(match[2]);
                }
            }
        };

    if(window.addEventListener) {
        window.addEventListener('popstate', resetParams);
    }

    resetParams();

    function getParam(param) {
        return params.hasOwnProperty(param) ? params[param] : null;
    }
    
    return getParam;

})();

function setGetParam(href, name, val) {
    // Generic function for changing a querystring parameter in a url
    var vars = {};
    var base = href.replace(/([#?].*)$/gi, ""); // no querystring, nor bookmark
    var parts = href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m, key, value) {
        vars[key] = value;
    });

    if (val === "" || val == "----" || val === undefined || val === null) {
        delete vars[name];
    } else {
        vars[name] = val;
    }

    var url = base;
    var idx = 0;
    for (var key in vars) {
        url += (idx === 0) ? "?" : "&";
        url += key + "=" + vars[key];//         + $.param(vars);
        idx++;
    }
    return url;
}

function setGetParamDict(href, dict) {
    for (var key in dict) {
         href = setGetParam(href, key, dict[key]);
    }
    return href;
}

module.exports = {
    setGetParam: setGetParam,
    setGetParamDict: setGetParamDict,
    getParamValue: getParamValue
};
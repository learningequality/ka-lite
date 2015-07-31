(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
var table = '00000000 77073096 EE0E612C 990951BA 076DC419 706AF48F E963A535 ' + '9E6495A3 0EDB8832 79DCB8A4 E0D5E91E 97D2D988 09B64C2B 7EB17CBD ' + 'E7B82D07 90BF1D91 1DB71064 6AB020F2 F3B97148 84BE41DE 1ADAD47D ' + '6DDDE4EB F4D4B551 83D385C7 136C9856 646BA8C0 FD62F97A 8A65C9EC ' + '14015C4F 63066CD9 FA0F3D63 8D080DF5 3B6E20C8 4C69105E D56041E4 ' + 'A2677172 3C03E4D1 4B04D447 D20D85FD A50AB56B 35B5A8FA 42B2986C ' + 'DBBBC9D6 ACBCF940 32D86CE3 45DF5C75 DCD60DCF ABD13D59 26D930AC ' + '51DE003A C8D75180 BFD06116 21B4F4B5 56B3C423 CFBA9599 B8BDA50F ' + '2802B89E 5F058808 C60CD9B2 B10BE924 2F6F7C87 58684C11 C1611DAB ' + 'B6662D3D 76DC4190 01DB7106 98D220BC EFD5102A 71B18589 06B6B51F ' + '9FBFE4A5 E8B8D433 7807C9A2 0F00F934 9609A88E E10E9818 7F6A0DBB ' + '086D3D2D 91646C97 E6635C01 6B6B51F4 1C6C6162 856530D8 F262004E ' + '6C0695ED 1B01A57B 8208F4C1 F50FC457 65B0D9C6 12B7E950 8BBEB8EA ' + 'FCB9887C 62DD1DDF 15DA2D49 8CD37CF3 FBD44C65 4DB26158 3AB551CE ' + 'A3BC0074 D4BB30E2 4ADFA541 3DD895D7 A4D1C46D D3D6F4FB 4369E96A ' + '346ED9FC AD678846 DA60B8D0 44042D73 33031DE5 AA0A4C5F DD0D7CC9 ' + '5005713C 270241AA BE0B1010 C90C2086 5768B525 206F85B3 B966D409 ' + 'CE61E49F 5EDEF90E 29D9C998 B0D09822 C7D7A8B4 59B33D17 2EB40D81 ' + 'B7BD5C3B C0BA6CAD EDB88320 9ABFB3B6 03B6E20C 74B1D29A EAD54739 ' + '9DD277AF 04DB2615 73DC1683 E3630B12 94643B84 0D6D6A3E 7A6A5AA8 ' + 'E40ECF0B 9309FF9D 0A00AE27 7D079EB1 F00F9344 8708A3D2 1E01F268 ' + '6906C2FE F762575D 806567CB 196C3671 6E6B06E7 FED41B76 89D32BE0 ' + '10DA7A5A 67DD4ACC F9B9DF6F 8EBEEFF9 17B7BE43 60B08ED5 D6D6A3E8 ' + 'A1D1937E 38D8C2C4 4FDFF252 D1BB67F1 A6BC5767 3FB506DD 48B2364B ' + 'D80D2BDA AF0A1B4C 36034AF6 41047A60 DF60EFC3 A867DF55 316E8EEF ' + '4669BE79 CB61B38C BC66831A 256FD2A0 5268E236 CC0C7795 BB0B4703 ' + '220216B9 5505262F C5BA3BBE B2BD0B28 2BB45A92 5CB36A04 C2D7FFA7 ' + 'B5D0CF31 2CD99E8B 5BDEAE1D 9B64C2B0 EC63F226 756AA39C 026D930A ' + '9C0906A9 EB0E363F 72076785 05005713 95BF4A82 E2B87A14 7BB12BAE ' + '0CB61B38 92D28E9B E5D5BE0D 7CDCEFB7 0BDBDF21 86D3D2D4 F1D4E242 ' + '68DDB3F8 1FDA836E 81BE16CD F6B9265B 6FB077E1 18B74777 88085AE6 ' + 'FF0F6A70 66063BCA 11010B5C 8F659EFF F862AE69 616BFFD3 166CCF45 ' + 'A00AE278 D70DD2EE 4E048354 3903B3C2 A7672661 D06016F7 4969474D ' + '3E6E77DB AED16A4A D9D65ADC 40DF0B66 37D83BF0 A9BCAE53 DEBB9EC5 ' + '47B2CF7F 30B5FFE9 BDBDF21C CABAC28A 53B39330 24B4A3A6 BAD03605 ' + 'CDD70693 54DE5729 23D967BF B3667A2E C4614AB8 5D681B02 2A6F2B94 ' + 'B40BBE37 C30C8EA1 5A05DF1B 2D02EF8D';
var crc32 = function (str, crc) {
    if (crc == null) {
        crc = 0;
    }
    var n = 0;
    var x = 0;
    crc = crc ^ -1;
    for (var i = 0, iTop = str.length; i < iTop; i++) {
        n = (crc ^ str.charCodeAt(i)) & 255;
        x = '0x' + table.substr(n * 9, 8);
        crc = crc >>> 8 ^ x;
    }
    return Math.abs(crc ^ -1);
};
module.exports = crc32;
},{}],2:[function(require,module,exports){
var crc32 = require('./crc32.js');
var localMode;
var VARS = {};
$.tmpl = {
    DATA_ENSURE_LOOPS: 0,
    attr: {
        'data-ensure': function (elem, ensure) {
            return function (elem) {
                var result = !!(ensure && $.tmpl.getVAR(ensure));
                if (!result) {
                    if ($.tmpl.DATA_ENSURE_LOOPS++ > 10000 && localMode) {
                        alert('unsatisfiable data-ensure?');
                        return true;
                    }
                }
                return result;
            };
        },
        'data-if': function (elem, value) {
            var $elem = $(elem);
            value = value && $.tmpl.getVAR(value);
            var $nextElem = $elem.next();
            if ($nextElem.data('lastCond') === undefined) {
                $nextElem.data('lastCond', value);
            }
            if (!value) {
                return [];
            }
        },
        'data-else-if': function (elem, value) {
            var $elem = $(elem);
            var lastCond = $elem.data('lastCond');
            value = !lastCond && value && $.tmpl.getVAR(value);
            var $nextElem = $elem.next();
            if ($nextElem.data('lastCond') === undefined) {
                $nextElem.data('lastCond', lastCond || value);
            }
            if (!value) {
                return [];
            }
        },
        'data-else': function (elem) {
            var $elem = $(elem);
            if ($elem.data('lastCond')) {
                return [];
            }
        },
        'data-each': function (elem, value) {
            var match;
            $(elem).removeAttr('data-each');
            if (match = /^(.+) times(?: as (\w+))?$/.exec(value)) {
                var times = $.tmpl.getVAR(match[1]);
                return {
                    items: $.map(new Array(times), function (e, i) {
                        return i;
                    }),
                    value: match[2],
                    oldValue: VARS[match[2]]
                };
            } else if (match = /^(.*?)(?: as (?:(\w+), )?(\w+))?$/.exec(value)) {
                return {
                    items: $.tmpl.getVAR(match[1]),
                    value: match[3],
                    pos: match[2],
                    oldValue: VARS[match[3]],
                    oldPos: VARS[match[2]]
                };
            }
        },
        'data-unwrap': function (elem) {
            return $(elem).contents();
        },
        'data-video-hint': function (elem) {
            var youtubeIds = $(elem).data('youtube-id');
            if (!youtubeIds) {
                return;
            }
            youtubeIds = youtubeIds.split(/,\s*/);
            var author = $(elem).data('video-hint-author') || 'Sal';
            var msg = $._('Watch %(author)s work through a very similar ' + 'problem:', { author: author });
            var preface = $('<p>').text(msg);
            var wrapper = $('<div>', { 'class': 'video-hint' });
            wrapper.append(preface);
            _.each(youtubeIds, function (youtubeId) {
                var href = 'http://www.khanacademy.org/embed_video?v=' + youtubeId;
                var iframe = $('<iframe>').attr({
                    'frameborder': '0',
                    'scrolling': 'no',
                    'width': '100%',
                    'height': '360px',
                    'src': href
                });
                wrapper.append(iframe);
            });
            return wrapper;
        }
    },
    type: {
        'var': function (elem, value) {
            if (!value && $(elem).children().length > 0) {
                return function (elem) {
                    return $.tmpl.type['var'](elem, elem.innerHTML);
                };
            }
            value = value || $.tmpl.getVAR(elem);
            var name = elem.id;
            if (name) {
                var setVAR = function (name, value) {
                    if (KhanUtil[name]) {
                        Khan.error('Defining variable \'' + name + '\' overwrites utility property of same name.');
                    }
                    VARS[name] = value;
                };
                if (name.indexOf(',') !== -1) {
                    var parts = name.split(/\s*,\s*/);
                    $.each(parts, function (i, part) {
                        if (part.length > 0) {
                            setVAR(part, value[i]);
                        }
                    });
                } else {
                    setVAR(name, value);
                }
            } else {
                if (value == null) {
                    return [];
                } else {
                    var div = $('<div>');
                    var html = div.append(value + ' ').html();
                    return div.html(html.slice(0, -1)).contents();
                }
            }
        }
    },
    getVAR: function (elem, ctx) {
        var code = elem.nodeName ? $(elem).text() : elem;
        if (ctx == null) {
            ctx = {};
        }
        function doEval() {
            with (Math) {
                with (KhanUtil) {
                    with (ctx) {
                        with (VARS) {
                            return eval('(function() { return (' + code + '); })()');
                        }
                    }
                }
            }
        }
        if (Khan.query.debug != null) {
            return doEval();
        } else {
            try {
                return doEval();
            } catch (e) {
                var info;
                if (elem.nodeName) {
                    info = elem.nodeName.toLowerCase();
                    if (elem.id != null && elem.id.length > 0) {
                        info += '#' + elem.id;
                    }
                } else {
                    info = JSON.stringify(code);
                }
                Khan.error('Error while evaluating ' + info, e);
            }
        }
    },
    getVarsHash: function () {
        return crc32(JSON.stringify($.map(VARS, function (value, key) {
            return [
                key,
                String(value)
            ];
        })));
    }
};
if (typeof KhanUtil !== 'undefined') {
    KhanUtil.tmpl = $.tmpl;
}
$.fn.tmplLoad = function (problem, info) {
    VARS = {};
    $.tmpl.DATA_ENSURE_LOOPS = 0;
    localMode = info.localMode;
    if (localMode) {
        $.tmpl.VARS = VARS;
    }
};
$.fn.tmpl = function () {
    for (var i = 0, l = this.length; i < l; i++) {
        traverse(this[i]);
    }
    return this;
    function traverse(elem) {
        var post = [], child = elem.childNodes, ret = process(elem, post);
        if (ret === false) {
            return traverse(elem);
        } else if (ret === undefined) {
        } else if (typeof ret === 'object' && typeof ret.length !== 'undefined') {
            if (elem.parentNode) {
                $.each(ret, function (i, rep) {
                    if (rep.nodeType) {
                        elem.parentNode.insertBefore(rep, elem);
                    }
                });
                $.each(ret, function (i, rep) {
                    traverse(rep);
                });
                elem.parentNode.removeChild(elem);
            }
            return null;
        } else if (ret.items) {
            var origParent = elem.parentNode, origNext = elem.nextSibling;
            $.each(ret.items, function (pos, value) {
                if (ret.value) {
                    VARS[ret.value] = value;
                }
                if (ret.pos) {
                    VARS[ret.pos] = pos;
                }
                var clone = $(elem).clone(true).removeAttr('data-each').removeData('each')[0];
                var conditionals = [
                    'data-if',
                    'data-else-if',
                    'data-else'
                ];
                var declarations = '';
                declarations += ret.pos ? 'var ' + ret.pos + ' = ' + JSON.stringify(pos) + ';' : '';
                declarations += ret.value ? 'var ' + ret.value + ' = ' + JSON.stringify(value) + ';' : '';
                for (var i = 0; i < conditionals.length; i++) {
                    var conditional = conditionals[i];
                    $(clone).find('[' + conditional + ']').each(function () {
                        var code = $(this).attr(conditional);
                        code = '(function() { ' + declarations + ' return ' + code + ' })()';
                        $(this).attr(conditional, code);
                    });
                }
                $(clone).find('.graphie').addBack().filter('.graphie').each(function () {
                    var code = $(this).text();
                    $(this).text(declarations + code);
                });
                if (origNext) {
                    origParent.insertBefore(clone, origNext);
                } else {
                    origParent.appendChild(clone);
                }
                traverse(clone);
            });
            if (ret.value) {
                VARS[ret.value] = ret.oldValue;
            }
            if (ret.pos) {
                VARS[ret.pos] = ret.oldPos;
            }
            $(elem).remove();
            return null;
        }
        for (var i = 0; i < child.length; i++) {
            if (child[i].nodeType === 1 && traverse(child[i]) === null) {
                i--;
            }
        }
        for (var i = 0, l = post.length; i < l; i++) {
            if (post[i](elem) === false) {
                return traverse(elem);
            }
        }
        return elem;
    }
    function process(elem, post) {
        var ret, $elem = $(elem);
        for (var attr in $.tmpl.attr) {
            if ($.tmpl.attr.hasOwnProperty(attr)) {
                var value;
                if (/^data-/.test(attr)) {
                    value = $elem.data(attr.replace(/^data-/, ''));
                } else {
                    value = $elem.attr(attr);
                }
                if (value !== undefined) {
                    ret = $.tmpl.attr[attr](elem, value);
                    if (typeof ret === 'function') {
                        post.push(ret);
                    } else if (ret !== undefined) {
                        return ret;
                    }
                }
            }
        }
        var type = elem.nodeName.toLowerCase();
        if ($.tmpl.type[type] != null) {
            ret = $.tmpl.type[type](elem);
            if (typeof ret === 'function') {
                post.push(ret);
            }
        }
        return ret;
    }
};
$.extend($.expr[':'], {
    inherited: function (el) {
        return $(el).data('inherited');
    }
});
$.fn.extend({
    tmplApply: function (options) {
        options = options || {};
        var attribute = options.attribute || 'id', defaultApply = options.defaultApply || 'replace', parent = {};
        return this.each(function () {
            var $this = $(this), name = $this.attr(attribute), hint = $this.data('apply') && !$this.data('apply').indexOf('hint');
            if (name) {
                if (name in parent && !hint) {
                    parent[name] = $.tmplApplyMethods[$this.data('apply') || defaultApply].call(parent[name], this);
                    if (parent[name] == null) {
                        delete parent[name];
                    }
                } else if ($this.closest(':inherited').length > 0) {
                    parent[name] = this;
                }
            }
        });
    }
});
$.extend({
    tmplApplyMethods: {
        remove: function (elem) {
            $(this).remove();
            $(elem).remove();
        },
        replace: function (elem) {
            $(this).replaceWith(elem);
            return elem;
        },
        splice: function (elem) {
            $(this).replaceWith($(elem).contents());
        },
        append: function (elem) {
            $(this).append(elem);
            return this;
        },
        appendContents: function (elem) {
            $(this).append($(elem).contents());
            $(elem).remove();
            return this;
        },
        prepend: function (elem) {
            $(this).prepend(elem);
            return this;
        },
        prependContents: function (elem) {
            $(this).prepend($(elem).contents());
            $(elem).remove();
            return this;
        },
        before: function (elem) {
            $(this).before(elem);
            return this;
        },
        beforeContents: function (elem) {
            $(this).before($(elem).contents());
            $(elem).remove();
            return this;
        },
        after: function (elem) {
            $(this).after(elem);
            return this;
        },
        afterContents: function (elem) {
            $(this).after($(elem).contents());
            $(elem).remove();
            return this;
        },
        appendVars: function (elem) {
            var parentEnsure = $(this).data('ensure') || '1';
            var childEnsure = $(elem).data('ensure') || '1';
            $(this).data('ensure', '(' + parentEnsure + ') && (' + childEnsure + ')');
            return $.tmplApplyMethods.appendContents.call(this, elem);
        },
        prependVars: function (elem) {
            var parentEnsure = $(this).data('ensure') || '1';
            var childEnsure = $(elem).data('ensure') || '1';
            $(this).data('ensure', '(' + childEnsure + ') && (' + parentEnsure + ')');
            return $.tmplApplyMethods.prependContents.call(this, elem);
        }
    }
});
},{"./crc32.js":1}]},{},[2]);

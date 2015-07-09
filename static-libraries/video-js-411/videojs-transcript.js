/*! videojs-transcript - v0.7.1 - 2015-06-24
* Copyright (c) 2015 Matthew Walsh; Licensed MIT */
(function (window, videojs) {
  'use strict';


// requestAnimationFrame polyfill by Erik Möller. fixes from Paul Irish and Tino Zijdel
// MIT license
// https://gist.github.com/paulirish/1579671
(function() {
  var lastTime = 0;
  var vendors = ['ms', 'moz', 'webkit', 'o'];
  for(var x = 0; x < vendors.length && !window.requestAnimationFrame; ++x) {
    window.requestAnimationFrame = window[vendors[x]+'RequestAnimationFrame'];
    window.cancelAnimationFrame = window[vendors[x]+'CancelAnimationFrame']
    || window[vendors[x]+'CancelRequestAnimationFrame'];
  }
  if (!window.requestAnimationFrame)
    window.requestAnimationFrame = function(callback, element) {
      var currTime = new Date().getTime();
      var timeToCall = Math.max(0, 16 - (currTime - lastTime));
      var id = window.setTimeout(function() { callback(currTime + timeToCall); },
      timeToCall);
      lastTime = currTime + timeToCall;
      return id;
    };
  if (!window.cancelAnimationFrame)
    window.cancelAnimationFrame = function(id) {
      clearTimeout(id);
    };
}());

// Object.create() polyfill
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/create#Polyfill
if (typeof Object.create != 'function') {
  Object.create = (function() {
    var Object = function() {};
    return function (prototype) {
      if (arguments.length > 1) {
        throw Error('Second argument not supported');
      }
      if (typeof prototype != 'object') {
        throw TypeError('Argument must be an object');
      }
      Object.prototype = prototype;
      var result = new Object();
      Object.prototype = null;
      return result;
    };
  })();
}

// forEach polyfill
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/forEach#Polyfill
if (!Array.prototype.forEach) {
  Array.prototype.forEach = function(callback, thisArg) {
    var T, k;
    if (this == null) {
      throw new TypeError(' this is null or not defined');
    }
    var O = Object(this);
    var len = O.length >>> 0;
    if (typeof callback != "function") {
      throw new TypeError(callback + ' is not a function');
    }
    if (arguments.length > 1) {
      T = thisArg;
    }
    k = 0;
    while (k < len) {
      var kValue;
      if (k in O) {
        kValue = O[k];
        callback.call(T, kValue, k, O);
      }
      k++;
    }
  };
}

// classList polyfill
/*! @source http://purl.eligrey.com/github/classList.js/blob/master/classList.js*/
;if("document" in self&&!("classList" in document.createElement("_"))){(function(j){"use strict";if(!("Element" in j)){return}var a="classList",f="prototype",m=j.Element[f],b=Object,k=String[f].trim||function(){return this.replace(/^\s+|\s+$/g,"")},c=Array[f].indexOf||function(q){var p=0,o=this.length;for(;p<o;p++){if(p in this&&this[p]===q){return p}}return -1},n=function(o,p){this.name=o;this.code=DOMException[o];this.message=p},g=function(p,o){if(o===""){throw new n("SYNTAX_ERR","An invalid or illegal string was specified")}if(/\s/.test(o)){throw new n("INVALID_CHARACTER_ERR","String contains an invalid character")}return c.call(p,o)},d=function(s){var r=k.call(s.getAttribute("class")||""),q=r?r.split(/\s+/):[],p=0,o=q.length;for(;p<o;p++){this.push(q[p])}this._updateClassName=function(){s.setAttribute("class",this.toString())}},e=d[f]=[],i=function(){return new d(this)};n[f]=Error[f];e.item=function(o){return this[o]||null};e.contains=function(o){o+="";return g(this,o)!==-1};e.add=function(){var s=arguments,r=0,p=s.length,q,o=false;do{q=s[r]+"";if(g(this,q)===-1){this.push(q);o=true}}while(++r<p);if(o){this._updateClassName()}};e.remove=function(){var t=arguments,s=0,p=t.length,r,o=false;do{r=t[s]+"";var q=g(this,r);if(q!==-1){this.splice(q,1);o=true}}while(++s<p);if(o){this._updateClassName()}};e.toggle=function(p,q){p+="";var o=this.contains(p),r=o?q!==true&&"remove":q!==false&&"add";if(r){this[r](p)}return !o};e.toString=function(){return this.join(" ")};if(b.defineProperty){var l={get:i,enumerable:true,configurable:true};try{b.defineProperty(m,a,l)}catch(h){if(h.number===-2146823252){l.enumerable=false;b.defineProperty(m,a,l)}}}else{if(b[f].__defineGetter__){m.__defineGetter__(a,i)}}}(self))};



// Global settings
var my = {};
my.settings = {};
my.prefix = 'transcript';
my.player = this;

// Defaults
var defaults = {
  autoscroll: true,
  clickArea: 'text',
  showTitle: true,
  showTrackSelector: true,
  followPlayerTrack: true,
  stopScrollWhenInUse: true,
};

/*global my*/
var utils = (function (plugin) {
  return {
    secondsToTime: function (timeInSeconds) {
      var hour = Math.floor(timeInSeconds / 3600);
      var min = Math.floor(timeInSeconds % 3600 / 60);
      var sec = Math.floor(timeInSeconds % 60);
      sec = (sec < 10) ? '0' + sec : sec;
      min = (hour > 0 && min < 10) ? '0' + min : min;
      if (hour > 0) {
        return hour + ':' + min + ':' + sec;
      }
      return min + ':' + sec;
    },
    localize: function (string) {
      return string; // TODO: do something here;
    },
    createEl: function (elementName, classSuffix) {
      classSuffix = classSuffix || '';
      var el = document.createElement(elementName);
      el.className = plugin.prefix + classSuffix;
      return el;
    },
    extend: function(obj) {
      var type = typeof obj;
      if (!(type === 'function' || type === 'object' && !!obj)) {
        return obj;
      }
      var source, prop;
      for (var i = 1, length = arguments.length; i < length; i++) {
        source = arguments[i];
        for (prop in source) {
          obj[prop] = source[prop];
        }
      }
      return obj;
    }
  };
}(my));

var eventEmitter = {
  handlers_: [],
  on: function on (object, eventtype, callback) {
    if (typeof callback === 'function') {
      this.handlers_.push([object, eventtype, callback]);
    } else {
      throw new TypeError('Callback is not a function.');
    }
  },
  trigger: function trigger (object, eventtype) {
    this.handlers_.forEach( function(h) {
      if (h[0] === object &&
          h[1] === eventtype) {
            h[2].apply();
      }
    });
  }
};

var scrollerProto = function(plugin) {

  var initHandlers = function (el) {
    var self = this;
    // The scroll event. We want to keep track of when the user is scrolling the transcript.
    el.addEventListener('scroll', function () {
      if (self.isAutoScrolling) {

        // If isAutoScrolling was set to true, we can set it to false and then ignore this event.
        // It wasn't the user.
        self.isAutoScrolling = false; // event handled
      } else {

        // We only care about when the user scrolls. Set userIsScrolling to true and add a nice class.
        self.userIsScrolling = true;
        el.classList.add('is-inuse');
      }
    });

    // The mouseover event.
    el.addEventListener('mouseenter', function () {
      self.mouseIsOverTranscript = true;
    });
    el.addEventListener('mouseleave', function () {
      self.mouseIsOverTranscript = false;

      // Have a small delay before deciding user as done interacting.
      setTimeout(function () {

        // Make sure the user didn't move the pointer back in.
        if (!self.mouseIsOverTranscript) {
          self.userIsScrolling = false;
          el.classList.remove('is-inuse');
        }
      }, 1000);
    });
  };

  // Init instance variables
  var init = function (element, plugin) {
    this.element = element;
    this.userIsScrolling = false;

    //default to true in case user isn't using a mouse;
    this.mouseIsOverTranscript = true;
    this.isAutoScrolling = true;
    initHandlers.call(this, this.element);
    return this;
  };

  // Easing function for smoothness.
  var easeOut = function (time, start, change, duration) {
    return start + change * Math.sin(Math.min(1, time / duration) * (Math.PI / 2));
  };

  // Animate the scrolling.
  var scrollTo = function (element, newPos, duration) {
    var startTime = Date.now();
    var startPos = element.scrollTop;
    var self = this;

    // Don't try to scroll beyond the limits. You won't get there and this will loop forever.
    newPos = Math.max(0, newPos);
    newPos = Math.min(element.scrollHeight - element.clientHeight, newPos);
    var change = newPos - startPos;

    // This inner function is called until the elements scrollTop reaches newPos.
    var updateScroll = function () {
      var now = Date.now();
      var time = now - startTime;
      self.isAutoScrolling = true;
      element.scrollTop = easeOut(time, startPos, change, duration);
      if (element.scrollTop !== newPos) {
        requestAnimationFrame(updateScroll, element);
      }
    };
    requestAnimationFrame(updateScroll, element);
  };

  // Scroll an element's parent so the element is brought into view.
  var scrollToElement = function (element) {
    if (this.canScroll()) {
      var parent = element.parentElement;
      var parentOffsetBottom = parent.offsetTop + parent.clientHeight;
      var elementOffsetBottom = element.offsetTop + element.clientHeight;
      var relTop = element.offsetTop - parent.offsetTop;
      var relBottom = (element.offsetTop + element.clientHeight) - parent.offsetTop;
      var newPos;

      // If the top of the line is above the top of the parent view, were scrolling up,
      // so we want to move the top of the element downwards to match the top of the parent.
      if (relTop < parent.scrollTop) {
        newPos = element.offsetTop - parent.offsetTop;

      // If the bottom of the line is below the parent view, we're scrolling down, so we want the
      // bottom edge of the line to move up to meet the bottom edge of the parent.
      } else if (relBottom > (parent.scrollTop + parent.clientHeight)) {
        newPos = elementOffsetBottom - parentOffsetBottom;
      }

      // Don't try to scroll if we haven't set a new position.  If we didn't
      // set a new position the line is already in view (i.e. It's not above
      // or below the view)
      // And don't try to scroll when the element is already in position.
      if (newPos !== undefined && parent.scrollTop !== newPos) {
        scrollTo.call(this, parent, newPos, 400);
      }
    }
  };

  // Return whether the element is scrollable.
  var canScroll = function () {
    var el = this.element;
    return el.scrollHeight > el.offsetHeight;
  };

  // Return whether the user is interacting with the transcript.
  var inUse = function () {
    return this.userIsScrolling;
  };

  return {
    init: init,
    to : scrollToElement,
    canScroll : canScroll,
    inUse : inUse
  }
}(my);

var scroller = function(element) {
  return Object.create(scrollerProto).init(element);
};


/*global my*/
var trackList = function (plugin) {
  var activeTrack;
  return {
    get: function () {
      var validTracks = [];
      var i, track;
      my.tracks = my.player.textTracks();
      for (i = 0; i < my.tracks.length; i++) {
        track = my.tracks[i];
        if (track.kind === 'captions' || track.kind === 'subtitles') {
          validTracks.push(track);
        }
      }
      return validTracks;
    },
    active: function (tracks) {
      var i, track;
      for (i = 0; i < my.tracks.length; i++) {
        track = my.tracks[i];
        if (track.mode === 'showing') {
          activeTrack = track;
          return track;
        }
      }
      // fallback to first track
      return activeTrack || tracks[0];
    },
  };
}(my);

/*globals utils, eventEmitter, my, scrollable*/

var widget = function (plugin) {
  var my = {};
  my.element = {};
  my.body = {};
  var on = function (event, callback) {
    eventEmitter.on(this, event, callback);
  };
  var trigger = function (event) {
    eventEmitter.trigger(this, event);
  };
  var createTitle = function () {
    var header = utils.createEl('header', '-header');
    header.textContent = utils.localize('Transcript');
    return header;
  };
  var createSelector = function (){
    var selector = utils.createEl('select', '-selector');
      plugin.validTracks.forEach(function (track, i) {
      var option = document.createElement('option');
      option.value = i;
      option.textContent = track.label + ' (' + track.language + ')';
      selector.appendChild(option);
    });
    selector.addEventListener('change', function (e) {
      setTrack(document.querySelector('#' + plugin.prefix + '-' + plugin.player.id() + ' option:checked').value);
      trigger('trackchanged');
    });
    return selector;
  };
  var clickToSeekHandler = function (event) {
    var clickedClasses = event.target.classList;
    var clickedTime = event.target.getAttribute('data-begin') || event.target.parentElement.getAttribute('data-begin');
    if (clickedTime !== undefined && clickedTime !== null) { // can be zero
      if ((plugin.settings.clickArea === 'line') || // clickArea: 'line' activates on all elements
        (plugin.settings.clickArea === 'timestamp' && clickedClasses.contains(plugin.prefix + '-timestamp')) ||
        (plugin.settings.clickArea === 'text' && clickedClasses.contains(plugin.prefix + '-text'))) {
        plugin.player.currentTime(clickedTime);
      }
    }
  };
  var createLine = function (cue) {
    var line = utils.createEl('div', '-line');
    var timestamp = utils.createEl('span', '-timestamp');
    var text = utils.createEl('span', '-text');
    line.setAttribute('data-begin', cue.startTime);
    timestamp.textContent = utils.secondsToTime(cue.startTime);
    text.innerHTML = cue.text;
    line.appendChild(timestamp);
    line.appendChild(text);
    return line;
  };
  var createTranscriptBody = function (track) {
    if (typeof track !== 'object') {
      track = plugin.player.textTracks()[track];
    }
    var body = utils.createEl('div', '-body');
    var line, i;
    var fragment = document.createDocumentFragment();
    // activeCues returns null when the track isn't loaded (for now?)
    if (!track.activeCues) {
      // If cues aren't loaded, set mode to hidden, wait, and try again.
      // But don't hide an active track. In that case, just wait and try again.
      if (track.mode !== 'showing') {
        track.mode = 'hidden';
      }
      window.setTimeout(function() {
        createTranscriptBody(track);
      }, 100);
    } else {
      var cues = track.cues;
      for (i = 0; i < cues.length; i++) {
        line = createLine(cues[i]);
        fragment.appendChild(line);
      }
      body.innerHTML = '';
      body.appendChild(fragment);
      body.setAttribute('lang', track.language);
      body.scroll = scroller(body);
      body.addEventListener('click', clickToSeekHandler);
      my.element.replaceChild(body, my.body);
      my.body = body;
    }

  };
  var create = function () {
    var el = document.createElement('div');
    my.element = el;
    el.setAttribute('id', plugin.prefix + '-' + plugin.player.id());
    if (plugin.settings.showTitle) {
      var title = createTitle();
      el.appendChild(title);
    }
    if (plugin.settings.showTrackSelector) {
      var selector = createSelector();
      el.appendChild(selector);
    }
    my.body = utils.createEl('div', '-body');
    el.appendChild(my.body);
    setTrack(plugin.currentTrack);
    return this;
  };
  var setTrack = function (track, trackCreated) {
    createTranscriptBody(track, trackCreated);
  };
  var setCue = function (time) {
    var active, i, line, begin, end;
    var lines = my.body.children;
    for (i = 0; i < lines.length; i++) {
      line = lines[i];
      begin = line.getAttribute('data-begin');
      if (i < lines.length - 1) {
        end = lines[i + 1].getAttribute('data-begin');
      } else {
        end = plugin.player.duration() || Infinity;
      }
      if (time > begin && time < end) {
        if (!line.classList.contains('is-active')) { // don't update if it hasn't changed
          line.classList.add('is-active');
          if (plugin.settings.autoscroll && !(plugin.settings.stopScrollWhenInUse && my.body.scroll.inUse())) {
              my.body.scroll.to(line);
          }
        }
      } else {
        line.classList.remove('is-active');
      }
    }
  };
  var el = function () {
    return my.element;
  };
  return {
    create: create,
    setTrack: setTrack,
    setCue: setCue,
    el : el,
    on: on,
    trigger: trigger,
  };

}(my);

var transcript = function (options) {
  my.player = this;
  my.validTracks = trackList.get();
  my.currentTrack = trackList.active(my.validTracks);
  my.settings = videojs.util.mergeOptions(defaults, options);
  my.widget = widget.create();
  var timeUpdate = function () {
    my.widget.setCue(my.player.currentTime());
  };
  var updateTrack = function () {
    my.currentTrack = trackList.active(my.validTracks);
    my.widget.setTrack(my.currentTrack);
  };
  if (my.validTracks.length > 0) {
    updateTrack();
    my.player.on('timeupdate', timeUpdate);
    if (my.settings.followPlayerTrack) {
      my.player.on('captionstrackchange', updateTrack);
      my.player.on('subtitlestrackchange', updateTrack);
    }
  } else {
    throw new Error('videojs-transcript: No tracks found!');
  }
  return {
    el: function () {
      return my.widget.el();
    },
    setTrack: my.widget.setTrack
  };
};
videojs.plugin('transcript', transcript);

}(window, videojs));

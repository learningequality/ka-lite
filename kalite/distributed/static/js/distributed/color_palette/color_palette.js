var $ = require("../base/jQuery");
require("browsernizr/test/inputtypes");
var Modernizr = require("browsernizr");
var colorPaletteTemplate = require("./hbtemplates/color-palette.handlebars");
var BaseView = require("../base/baseview");

var bg_clr, acn_clr, act_clr, hln_clr, byt_clr;
var local_css_container;

module.exports = BaseView.extend({
    template: colorPaletteTemplate,

    events: {
        "change": "render"
    },

    initialize: function(options) {
        //check if color type available
        this.polyfill_verify();

        //retrieve the DOM elements
        local_css_container = $(options.local_css_container);
        bg_clr = $(options.bg_clr);
        acn_clr = $(options.acn_clr);
        act_clr = $(options.act_clr);
        hln_clr = $(options.hln_clr);
        byt_clr = $(options.byt_clr);

        //if not, fallback to simple-color-picker
        this.polyfill_color_picker();

        this.set_save_btn_listener($(options.save_color_palette_btn));

        //always looking for style in the localStorage first
        if(localStorage && localStorage.getItem("k-css")){
            var css = localStorage.getItem("k-css");
            local_css_container.html(css);
        }else{
            //if no localStorage support or no k-css saved in localStorage, create a new template
            this.render();
        }
    },

    render: function(){
        local_css_container.html(
            this.template({
                k_bg_clr: bg_clr.val(),
                k_acn_clr: acn_clr.val(),
                k_act_clr: act_clr.val(),
                k_hln_clr: hln_clr.val(),
                k_byt_clr: byt_clr.val(),
            })
        );
    },

    set_save_btn_listener: function(save_color_palette_btn){
        save_color_palette_btn.click(function(){
            if(localStorage){
                var css = local_css_container.html();
                localStorage.setItem("k-css", css);
            }
        });
    },

    polyfill_verify: function() {
        //if color type not supported(mainly Safari and IE), modify the DOM elements for simple-color-picker.js
        if(!Modernizr.inputtypes.color){
            (function replaceColorTags() {
                var inputs = document.getElementsByTagName("input");
                var colors = [];

                for(var i = 0; i < inputs.length; i++) {
                    if(inputs[i].type.toLowerCase() == 'text') {
                        colors.push(inputs[i]);
                    }
                }

                for(var r = 0; r < colors.length; r++) {
                    var color = colors[r];
                    var polyfill_color = document.createElement("div");
                    polyfill_color.id = color.id;
                    color.parentNode.insertBefore(polyfill_color, color);
                    color.parentNode.removeChild(color);
                }
            })();
        }
    },

    polyfill_color_picker: function(){
        //if color type not supported(mainly Safari and IE), fallback to simple-color-picker.js
        if(!Modernizr.inputtypes.color){
            require('../../../../../../node_modules/simple-color-picker/simple-color-picker.css');
            var ColorPicker = require('../../../../../../node_modules/simple-color-picker');
            require("./color_palette.css");

            var my_background = new ColorPicker({
                el: bg_clr[0],
                color: '#C4D7E3', //default color
                width: 100,
                height: 60
            });
            var my_accent = new ColorPicker({
                el: acn_clr[0],
                color: '#5AA685', //default color
                width: 100,
                height: 60
            });
            var my_action = new ColorPicker({
                el: act_clr[0],
                color: '#FF0076', //default color
                width: 100,
                height: 60
            });
            var my_headline = new ColorPicker({
                el: hln_clr[0],
                color: '#3A7AA2', //default color
                width: 100,
                height: 60
            });
            var my_bodytext = new ColorPicker({
                el: byt_clr[0],
                color: '#000000', //default color
                width: 100,
                height: 60
            });

            my_background.onChange(function(hexStringColor) {
                bg_clr.val(hexStringColor).trigger('change');
            });
            my_accent.onChange(function(hexStringColor) {
                acn_clr.val(hexStringColor).trigger('change');
            });
            my_action.onChange(function(hexStringColor) {
                act_clr.val(hexStringColor).trigger('change');
            });
            my_headline.onChange(function(hexStringColor) {
                hln_clr.val(hexStringColor).trigger('change');
            });
            my_bodytext.onChange(function(hexStringColor) {
                byt_clr.val(hexStringColor).trigger('change');
            });
        }
    }
});
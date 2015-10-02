var $ = require("../base/jQuery");
require("browsernizr/test/inputtypes");
var Modernizr = require("browsernizr");
var colorPaletteTemplate = require("./hbtemplates/color-palette.handlebars");
var BaseView = require("../base/baseview");

var ColorPaletteView = BaseView.extend({
    template: colorPaletteTemplate,
    tagName: "style", 

    initialize: function() {
        this.render();
    },

    render: function(){
        this.$el.html(this.template({
            k_bg_clr: $("#my_background").val(),
            k_acn_clr: $("#my_accent").val(),
            k_act_clr: $("#my_action").val(),
            k_hln_clr: $("#my_headline").val(),
            k_byt_clr: $("#my_bodytext").val(),
        }));
    }
});

$(function(){
    //if color type not supported(mainly Safari and IE), fallback to simple-color-picker.js
    if(!Modernizr.inputtypes.color){
        require('../../../../../../node_modules/simple-color-picker/simple-color-picker.css');
        var ColorPicker = require('../../../../../../node_modules/simple-color-picker');
        require("./color_palette.css");

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

        var my_background = new ColorPicker({
            el: document.getElementById("my_background"),
            color: '#C4D7E3',
            width: 100,
            height: 60
        });
        var my_accent = new ColorPicker({
            el: document.getElementById("my_accent"),
            color: '#5AA685',
            width: 100,
            height: 60
        });
        var my_action = new ColorPicker({
            el: document.getElementById("my_action"),
            color: '#FF0076',
            width: 100,
            height: 60
        });
        var my_headline = new ColorPicker({
            el: document.getElementById("my_headline"),
            color: '#3A7AA2',
            width: 100,
            height: 60
        });
        var my_bodytext = new ColorPicker({
            el: document.getElementById("my_bodytext"),
            color: '#000000',
            width: 100,
            height: 60
        });

        my_background.onChange(function(hexStringColor) {
            $("#my_background").val(hexStringColor);
        });
        my_accent.onChange(function(hexStringColor) {
            $("#my_accent").val(hexStringColor);
        });
        my_action.onChange(function(hexStringColor) {
            $("#my_action").val(hexStringColor);
        });
        my_headline.onChange(function(hexStringColor) {
            $("#my_headline").val(hexStringColor);
        });
        my_bodytext.onChange(function(hexStringColor) {
            $("#my_bodytext").val(hexStringColor);
        });
    }

    var color_palette;

    //always looking for style in the localStorage first
    if(localStorage && localStorage.getItem("k-css")){
        var css = localStorage.getItem("k-css");
        $("#k-local-css").html(css);
    }else{
        //if no localStorage support or no k-css saved in localStorage, create a new template
        color_palette = new ColorPaletteView();
        $("#k-local-css").html(color_palette.$el);
    }

    //for prototyping, I use a single button to trigger color palette update
    $("#change_color_palette").click(function(){
        //save the less generated css to localstorarge for reuse in later page load
        if(typeof color_palette == "undefined"){
            color_palette = new ColorPaletteView();
        }else{
            color_palette.render();
        }
        $("#k-local-css").html(color_palette.$el);
        if(localStorage){
            var css = $("#k-local-css").html();
            localStorage.setItem("k-css", css);
        }
    });

});
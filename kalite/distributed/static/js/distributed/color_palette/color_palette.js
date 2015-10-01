var $ = require("../base/jQuery");
require("browsernizr/test/inputtypes");
var Modernizr = require("browsernizr");
require("./color_palette.css");

$(function(){
    //if color type not supported(mainly Safari and IE), use jscolor.js
    if(!Modernizr.inputtypes.color){
        // require("./jscolor/jscolor.js");
        // require("./jquery-minicolors/jquery.minicolors.min.js");
        require('../../../../../../node_modules/simple-color-picker/simple-color-picker.css');
        var ColorPicker = require('../../../../../../node_modules/simple-color-picker');

        var my_background = new ColorPicker({
            // el: document.getElementsByClassName("my_background")
            el: document.getElementById("scp_background"),
            color: '#C4D7E3',
            width: 100,
            height: 60
        });
        var my_accent = new ColorPicker({
            el: document.getElementById("scp_accent"),
            color: '#5AA685',
            width: 100,
            height: 60
        });
        var my_action = new ColorPicker({
            el: document.getElementById("scp_action"),
            color: '#FF0076',
            width: 100,
            height: 60
        });
        var my_headline = new ColorPicker({
            el: document.getElementById("scp_headline"),
            color: '#3A7AA2',
            width: 100,
            height: 60
        });
        var my_bodytext = new ColorPicker({
            el: document.getElementById("scp_bodytext"),
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
    //always looking for style in the localStorage first
    if(localStorage && localStorage.getItem("k-css")){
        var css = localStorage.getItem("k-css"),
            head = document.head || document.getElementsByTagName('head')[0],
            style = document.createElement('style');

// console.log("k-css: ", css);
        style.type = 'text/css';
        style.id = 'k-local-css';
        if (style.styleSheet){
          style.styleSheet.cssText = css;
        } else {
          style.appendChild(document.createTextNode(css));
        }

        head.appendChild(style);
    }else{
        //if no localStorage support, compile the base less on the fly
        var less = require("../../../../../../node_modules/node-lessify/node_modules/less/dist/less.min.js");
        //need color inputs when channel editor is implemented
    }

    //for prototyping, I use a single button to trigger the less compilation
    $("#change_color_palette").click(function(){
        $('#k-local-css').html(""); //clean the localstorage, which may overwrite the less generated css

        //get input from color picker
        // var my_background = "#" + $("#my_background").val();
        // var my_accent = "#" + $("#my_accent").val();
        // var my_action = "#" + $("#my_action").val();
        // var my_headline = "#" + $("#my_headline").val();
        // var my_bodytext = "#" + $("#my_bodytext").val();
        var my_background = $("#my_background").val();
        var my_accent = $("#my_accent").val();
        var my_action = $("#my_action").val();
        var my_headline = $("#my_headline").val();
        var my_bodytext = $("#my_bodytext").val();

        var less = require("../../../../../../node_modules/node-lessify/node_modules/less/dist/less.min.js");
        //update the color palette (these 5 colors will take input from channel editor when it's implemented)
        less.modifyVars({
            // "@k-bg-color": "#C4D7E3",
            // "@k-accent-color": "#5AA685",
            // "@k-headline-color": "#3A7AA2",
            // "@k-bodytext-color": "black",
            // "@k-action-color": "#FF0076"
            "@k-bg-color": my_background,
            "@k-accent-color": my_accent,
            "@k-headline-color": my_headline,
            "@k-bodytext-color": my_bodytext,
            "@k-action-color": my_action
        });

        //save the less generated css to localstorarge for reuse in later page load
        var css =  $("style[id='less:static-css-distributed-kalite-base']").text();
        if(localStorage){
            localStorage.setItem("k-css", css);
        }
    });

});


// function change_k_bg_color() {
//     $(".k-bg-color").css("background-color", "LightPink");
// }

// function change_k_accent_color() {
//     $(".k-accent-color").css({"background-color":"Crimson", "border-left":"3px solid Crimson", "border-top":"3px solid Crimson", "border-right":"3px solid Crimson"});
//     $(".k-accent-border-bottom").css("border-bottom", "6px solid Crimson");
//     $(".k-accent-hover").hover(
//         function(){
//             $(this).css("color", "Crimson");
//         },
//         function(){
//             $(this).css("color", "white");
//         }
//     );
// }

// function addCSSRule(sheet, selector, rules, index) {
//     if("insertRule" in sheet) {
//         sheet.insertRule(selector + "{" + rules + "}", index);
//     }
//     else if("addRule" in sheet) {
//         sheet.addRule(selector, rules, index);
//     }
// }
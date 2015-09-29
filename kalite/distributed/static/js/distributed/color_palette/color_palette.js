var $ = require("../base/jQuery");

$(function(){
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
        var less = require("../../../../../../node_modules/less/less.min.js");
        //need color inputs when channel editor is implemented
    }

    //for prototyping, I use a single button to trigger the less compilation
    $("#change_color_palette").click(function(){
        $('#k-local-css').html(""); //clean the localstorage, which may overwrite the less generated css

        // var less = require("../../../../../../node_modules/node-lessify/node_modules/less/lib/less-browser")();
        var less = require("../../../../../../node_modules/less/less.min.js");
        //update the color palette (these 5 colors will take input from channel editor when it's implemented)
        less.modifyVars({
            "@k-bg-color": "grey",
            "@k-accent-color": "orange",
            "@k-headline-color": "purple",
            "@k-bodytext-color": "black",
            "@k-action-color": "red"
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
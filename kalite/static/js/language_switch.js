$(function () {
    $.ajax({
        url: INSTALLED_LANGUAGES_URL,
    }).success(display_languages_to_dropdown);
});

function display_languages_to_dropdown(languages) {
    languages.forEach(function(lang, langindex) {

        var selected = "";
        if (DEFAULT_LANGUAGE === lang.code)
            selected = "selected";

        $("#language-select").append(sprintf("<option value='%(lang.code)s' %(selected)s>%(lang.name)s</option>", {lang: lang, selected: selected}));
    });
}

// what this function does: when the #language-select box choice changes, load the selected language as default immediately
$(function () {
    $("#language-select").change(function () {
        var newlang = $("#language-select").val();
        window.location = CHANGE_LANGUAGE_URL + newlang;
    });
});

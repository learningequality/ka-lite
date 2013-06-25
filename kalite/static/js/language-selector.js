// Found on the distributed server
// If new language is selected, redirect after adding django_language session key
$("#language_selector").change(function() {
    window.location = "?set_language=" + $("#language_selector").val();
});
// If user is admin, they can set currently selected language as the default
$("#make_default_language").click(function() {
    window.location = "?set_default_language=" + $("#language_selector").val();
});

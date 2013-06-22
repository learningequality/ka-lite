// Functions related to loading the page
    
var csrftoken = getCookie("csrftoken") || "";

function toggle_state(state, status){
    $("." + (status ? "not-" : "") + state + "-only").hide(); 
    $("." + (!status ? "not-" : "") + state + "-only").show(); 
}

function show_messages(messages) {
    // This function knows to loop through the server-side messages
    for (var mi in messages) {
        show_message(messages[mi]["tags"], messages[mi]["text"]);
    }
}
    
$(function(){
    // Do the AJAX request to async-load user and message data 
    $("[class$=-only]").hide();
    doRequest("/securesync/api/status").success(function(data){
        toggle_state("logged-in", data.is_logged_in);
        toggle_state("registered", data.registered);
        toggle_state("django-user", data.is_django_user);
        toggle_state("admin", data.is_admin);
        if (data.is_logged_in){
            $('#logged-in-name').text(data.username + " (Logout)");
            if (data.points!=0){
                $('#sitepoints').text("Points: " + data.points);
            }
        }
        show_messages(data.messages);
    });        
});
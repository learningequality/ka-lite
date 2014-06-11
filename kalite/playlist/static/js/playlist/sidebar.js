$(document).ready(function () {
    $('#nav-menu, #navTab').sidr({
        name: "sidr-nav",
        side: "left"
    });
});

function showNav() {
    $('#dContent').addClass('Content-SB-Left', 200);
    $('#dMenuButton').addClass('dMenuButton-hover', 200);
}

function hideNav() {
    $('#dContent').removeClass('Content-SB-Left', 200);
    $('#dMenuButton').removeClass('dMenuButton-hover', 200);
}

function toggleNav() {
    if ($('#sidr-nav').css('display') !== 'none') {
        return hideNav();
    } else {
        return showNav();
    }
}
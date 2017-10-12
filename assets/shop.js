// Scripts used across the site for basic functionality.

$(document).ready(main_shop);

function main_shop()
{
	setupToggleMenus(); // Slide sub-menus in and out when clicked
}

// This will make sub-menus slide up/down.
function setupToggleMenus()
{
	$("nav ul ul").css('display', 'none');
	// For any nested ul also inside a nav, get the anchor just before it,
	// and slideToggle the ul when the anchor is clicked.
	var a = $("nav ul ul").prev();
	a.click(function(){
			$(this).next().slideToggle();
			return(false);
			});
}

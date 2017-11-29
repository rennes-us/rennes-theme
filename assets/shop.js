// Scripts used across the site for basic functionality.

$(document).ready(mainShop);

function mainShop() {
	setupToggleMenus(); // Slide sub-menus in and out when clicked
	setupProductImageSwapping(); // Select product images from thumbnails
}

// ----------------------------------------------------------------------------
// Navigation sub-menu sliding

// This will make sub-menus slide up/down.
function setupToggleMenus() {
	$("nav ul ul").css('display', 'none');
	// For any nested ul also inside a nav, get the anchor just before it,
	// and slideToggle the ul when the anchor is clicked.
	var a = $("nav ul ul").prev();
	a.click(function(){
			$(this).next().slideToggle();
			return(false);
			});
	// Leave the current sub-menu expanded, if there is one.  This assumes
	// that the theme has already put the "current" class on the ul
	// server-side.
	$("nav ul ul.current").css('display', 'block');
}

// ----------------------------------------------------------------------------
// Product image swapping

// For swapping out product images for the main image displayed
function setupProductImageSwapping() {
	// When a small image is clicked, set it as the current image
	$('[typeof="Product"] figure aside a').click(function() {
		return swapImage(this);
	});
}

// Take the img child of the given element and replace the current main product
// img with it
function swapImage(el) {
	var img = $(el).children('img').clone();
	var current_img = $('[typeof="Product"] figure > a img');
	current_img.replaceWith(img);
	return false;
}

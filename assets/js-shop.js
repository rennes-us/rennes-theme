// Scripts used across the site for basic functionality.

$(document).ready(mainShop);

function mainShop() {
	setupToggleMenus(); // Slide sub-menus in and out when clicked
	setupProductImageSwapping(); // Select product images from thumbnails
	setupProductImageZoom(); // Full-page zoom main product img when clicked
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
	// Keep track of the thumbnail matching the current image, for use in
	// the zooming feature below.
	$(".current_thumbnail").removeClass("current_thumbnail");
	$(el).addClass("current_thumbnail");
	var img = $(el).children('img');
	var current_img = $('[typeof="Product"] figure > a img');
	current_img.replaceWith(img.clone());
	return false;
}

// ----------------------------------------------------------------------------
// Product image zoom

// For showing a zoomed version of the product images when the main image is
// clicked
function setupProductImageZoom() {
	$('[typeof="Product"] figure > a').click(zoomProductImages);
}

// Display the full list of images at large size one below the other
function zoomProductImages() {
	// We already have CSS defined for the zoomed case, so all that's
	// needed is adding the class to the element.
	$('[typeof="Product"] figure aside').addClass("zoomed");
	// Scroll to the current image.
	var current = $('[typeof="Product"] a.current_thumbnail');
	var scroll = current.length ? current.offset().top : 0;
	$('.zoomed').scrollTop(scroll);
	// Un-zoom when any of the image links is clicked on.
	$(".zoomed a").click(zoomedImageLinkClick);
	return false;
}

// Un-zoom the list of images
function zoomedImageLinkClick() {
	// Resetting the scroll is required for this to work when re-entering
	// zoom, but I don't see why.
	$(".zoomed").scrollTop(0);
	$(".zoomed").removeClass("zoomed");
	$(".zoomed a").off("click", zoomedImageLinkClick);
}

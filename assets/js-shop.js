// Scripts used across the site for basic functionality.

$(document).ready(mainShop);

function mainShop() {
	setupToggleMenus(); // Slide sub-menus in and out when clicked
	setupProductImageSwappingArrows(); // Select product images from arrows
	setupProductImageZoom(); // Full-page zoom main product img when clicked
	setupVariantCheck(); // Check if product variant chosen for "add to bag"
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

// New method: arrow clicking
function setupProductImageSwappingArrows() {
	// When an arrow is clicked, swap out for the next or previous image
	$('[typeof="Product"] figure a.arrow').click(function() {
		// What kind of arrow is this?
		// https://stackoverflow.com/a/10159062/4499968
		var classes = $(this).attr("class").split(/\s+/);
		var current_thumbnail = $(".current_thumbnail");
		// There might not actually be a next or previous element, if
		// we were already at the edge of the set of images.  In that
		// case wrap around to the first/last depending on the case.
		if (classes.indexOf("left") >= 0) {
			var elem = $(current_thumbnail).prev();
			if (elem.length == 0) {
				var elem = $("figure aside a").last();
			}
		}
		if (classes.indexOf("right") >= 0) {
			var elem = $(current_thumbnail).next();
			if (elem.length == 0) {
				var elem = $("figure aside a").first();
			}
		}
		if (elem.length > 0) {
			return swapImage(elem);
		} else {
			return false;
		}
	});
}

// Old method: thumbnail clicking
// Not currently used, see the arrows version instead.
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
	$('[typeof="Product"] figure > a[property="image"]').click(zoomProductImages);
}

// Display the full list of images at large size one below the other
function zoomProductImages() {
	// We already have CSS defined for the zoomed case, so all that's
	// needed to zoom is adding the class to the element.
	$('[typeof="Product"] figure aside').addClass("zoomed");
	// We also need to avoid double-scroolbars from the container.
	// Temporarily clipping will do that.
	$('body').css('overflow', 'hidden');
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
	// Undo the clipping on the container.
	$('body').css('overflow', 'inherit');
	return false;
}

// ----------------------------------------------------------------------------
// For ensuring a variant is picked before the item is added to the cart.
// Only set the handler if there are actually variants to choose from, though.

function setupVariantCheck() {
	if ($('article[typeof="Product"] form input[type="radio"]').length > 0)
		$('article[typeof="Product"] form button').click(function() {return addCartHandler();});
}

function addCartHandler() {
	if ($('article[typeof="Product"] form input[type="radio"]:checked').length > 0)
		return true;
	else {
      $('article[typeof="Product"] form label').last().after('<span class="pick-an-option">⬅ Pick an option first</span>');
      return false;
    }
}

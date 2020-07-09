// Scripts used across the site for basic functionality.

$(document).ready(mainShop);

function mainShop() {
  setupDebug(); // Special debug element unhiding
  setupToggleMenus(); // Slide sub-menus in and out when clicked
  setupProductImageSwappingArrows(); // Select product images from arrows
  setupProductImageZoom(); // Full-page zoom main product img when clicked
  setupVariantHandling(); // Special handling for multiple variants
  setupBagUpdate(); // Auto-click the disclaimer when just updating the cart
  setupQtyButtons(); // enable minus/plus buttons for cart quantity field
}

// ----------------------------------------------------------------------------
// Debug

// Unhide the debug element when slash is pressed.  This will only take
// effect if debug mode is enabled server-side in the theme settings.
function setupDebug() {
  console.log("setupDebug");
  $("body").keydown(function(e) {
    if (insideTextElement()) {
      return;
    }
    if (e.which == 191) {
      $(".debug").css("display", "block");
    }
  });
}

// ----------------------------------------------------------------------------
// Navigation sub-menu sliding

// This will make sub-menus slide up/down.
function setupToggleMenus() {
  console.log("setupToggleMenus");
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

// get the anchor element of either the "left" or "right" thumbnail, wrapping
// as needed.
function _getAdjacentThumbnail(arrow_class) {
  var current_thumbnail = $(".current_thumbnail");
  // There might not actually be a next or previous element, if
  // we were already at the edge of the set of images.  In that
  // case wrap around to the first/last depending on the case.
  var elem = null;
  if (arrow_class == "left") {
    elem = $(current_thumbnail).prev();
    if (elem.length == 0) {
      elem = $("figure aside a").last();
    }
  } else if (arrow_class == "right") {
    elem = $(current_thumbnail).next();
    if (elem.length == 0) {
      elem = $("figure aside a").first();
    }
  }
  return elem;
}

// Cycle through product images for arrow_class either "left" or "right"
function _swapProductImage(arrow_class) {
  var elem = _getAdjacentThumbnail(arrow_class);
  if (elem && elem.length > 0) {
    return swapImage(elem);
  } else {
    return false;
  }
}

// Swipe (as triggered via a gesture) the product image either "left" or
// "right" (in the direction the images should move, not the direction of the
// swipe).
// This acts as a wrapper around the swap function to handle the animation.
// This is pretty convoluted but has the benefit of leaving the original DOM very
// simple and semantic.
function _swipeProductImage(arrow_class) {
  // First, set up placeholders to be positioned to the left, on top of, and to
  // the right of the main image and hide content outside of the figure
  // element.  Remove the semantic stuff so these placeholders don't get
  // interpreted as the real thing.
  // This part is the same no matter the arrow_class argument.
  var figure = $('[typeof="Product"] figure');
  figure.css("overflow", "hidden");
  var img = $('[typeof="Product"] figure > a[typeof="ImageObject"]');
  var width = img.width() + "px";
  var left = _getAdjacentThumbnail("left").clone();
  var center = img.clone();
  var right = _getAdjacentThumbnail("right").clone();
  function floatit(elem) {
    elem.css("z-index", "99");
    elem.css("position", "absolute");
    elem.css("width", "100%");
    elem.css("height", "100%");
    elem.attr("property", "");
    elem.attr("typeOf", "");
    elem.addClass("-main-image");
  }
  floatit(left);
  floatit(center);
  floatit(right);
  left.css("left", "-" + width);
  right.css("right", "-" + width);

  center.insertBefore(img);
  left.insertBefore(center);
  right.insertAfter(center);
  // Slide the main image and placeholders left or right as requested and do
  // the actual image swap.  Have the placeholders remove themselves when the
  // animation stops (by which time the "real" image should be in place so it's
  // seamless).
  var animation = null;
  var selector = null;
  if (arrow_class == "right") {
    animation = {left: "-=" + width};
    selector = "figure a.right";
  } else {
    animation = {left: "+=" + width};
    selector = "figure a.left";
  }
  $(".-main-image").animate(
    properties=animation,
    duration=SHOP_CONFIG.get("product_img_swipe_speed"),
    complete=function() {$(".-main-image").remove();});
  _swapProductImage(arrow_class);
}

// Is focus currently inside of an element that takes text input?  This is not
// a perfect way to detect when it's appropriate to do something special with
// keyboard input but for our purposes it should be enough.
function insideTextElement() {
  var tagName = $(document.activeElement).prop("tagName").toUpperCase();
  var textTags = ["INPUT", "TEXTAREA"];
  return textTags.indexOf(tagName) != -1;
}

// New product image swap method: arrow clicking
function setupProductImageSwappingArrows() {
  console.log("setupProductImageSwappingArrows");
  // When an arrow is clicked, swap out for the next or previous image
  var arrows = $('[typeof="Product"] figure a.arrow');
  if (arrows.length) {
    setupProductImageSwappingArrowsClicks(arrows);
    setupProductImageSwappingArrowsKeyboard();
    setupProductImageSwappingArrowsSwipe();
  }
}

function setupProductImageSwappingArrowsClicks(arrows) {
  arrows.click(function() {
    // What kind of arrow is this?
    // https://stackoverflow.com/a/10159062/4499968
    var classes = $(this).attr("class").split(/\s+/);
    var arrow_class = null;
    if (classes.indexOf("left") >= 0) {
      arrow_class = "left";
    } else if (classes.indexOf("right") >= 0) {
      arrow_class = "right";
    } else {
      console.log("figure arrow class not recognized: " + $(this).attr("class"));
    }
    return _swapProductImage(arrow_class);
  });
}

function setupProductImageSwappingArrowsKeyboard() {
  // Handle left and right keyboard keys.
  // https://www.cambiaresearch.com/articles/15/javascript-char-codes-key-codes
  $("body").keydown(function(e) {
    // Don't swap images around if focus is in an input/textarea/etc. though.
    if (insideTextElement()) {
      return;
    }
    if (e.which == 37) {
      _swapProductImage("left");
    } else if (e.which == 39) {
      _swapProductImage("right");
    }
  });
}

function setupProductImageSwappingArrowsSwipe() {
  // Handle swipe gestures in the same way as clicking the arrow links.  Note
  // that swiping left means we're going to the right image, and swiping right
  // means the left image.
  // HammerJS works very nicely for this though it seems to interfere
  // sporadically with the native iOS Safari's zoom on the figure as soon as
  // the Hammer object is initialized.  Need to look into that more.
  // touchCallout relates to the CSS that controls how the touch-and-hold
  // behavior works.  We want the default (context menu enabled) so we'll set
  // that here.
  var hammertime = new Hammer($("figure")[0], {cssProps: {"touchCallout": "default"}});
  hammertime.on('swipeleft', function(ev) { _swipeProductImage("right"); });
  hammertime.on('swiperight', function(ev) { _swipeProductImage("left"); });
}

// Old product image swap method: thumbnail clicking
// Not currently used, see the arrows version instead.
function setupProductImageSwapping() {
  console.log("setupProductImageSwapping");
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
  var current_img = $('[typeof="Product"] figure > a[typeof="ImageObject"] img');
  current_img.replaceWith(img.clone());
  return false;
}

// ----------------------------------------------------------------------------
// Product image zoom

// For showing a zoomed version of the product images when the main image is
// clicked
function setupProductImageZoom() {
  console.log("setupProductImageZoom");
  $('[typeof="Product"] figure > a[property="image"]').click(zoomProductImages);
}

// Display the full list of images at large size one below the other
function zoomProductImages() {
  // This is only worth doing if the main product image doesn't already take up
  // most of the viewport.  We'll compare the widths to see.
  var displaywidth = Math.round($(window).width());
  var imgwidth = Math.round($('[typeof="Product"] figure').width());
  var widthpct = Math.round(imgwidth/displaywidth*100);
  var verdict = "zoom";
  if (widthpct > 65) {
    verdict = "skip";
  }
  console.log(
    "zoomProductImages: " +
    "img " + imgwidth + "px, " +
    "viewport " + displaywidth + "px " +
    "(" + widthpct + "%) -> " + verdict);
  if (verdict == "skip") {
    return false;
  }
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

// Handle variant select and switching, if there are variants to choose from.
function setupVariantHandling() {
  console.log("setupVariantHandling");
  if ($('article[typeof="Product"] form input[type="radio"]').length > 0) {
    $('input[type=radio]').change(function() {
      $("div[property=priceSpecification]").attr("data-selected-variant", "false");
      var elem = $("div[property=priceSpecification][data-variant-id=" + $(this).attr("id") + "]");
      elem.attr("data-selected-variant", "true");
    });
    $('article[typeof="Product"] form button').click(function() {return addCartHandler();});
  }
}

// For ensuring a variant is picked before the item is added to the cart.
function addCartHandler() {
  if ($('article[typeof="Product"] form input[type="radio"]:checked').length > 0)
    return true;
  else {
      $('article[typeof="Product"] span[typeof="OfferForPurchase"]').last().after('<span class="pick-an-option">⬅ Pick an option first</span>');
      return false;
    }
}

// ----------------------------------------------------------------------------
// Cart Features

// There are two buttons in the cart: Update Bag and Checkout.  With Checkout
// we want the required input check box to be checked, but we don't care for
// Update Bag.  I don't see any HTML/CSS way to make this happen so we'll just
// unset the required attributeourselves when Update Bag is clicked.
function setupBagUpdate() {
  console.log("setupBagUpdate");
  $('form[action="/cart"] button[value="update"]').click(function() {
    // NOTE we don't want to return false here, because we do want the
    // click to have its usual effect.
    $('input#checkout-warning').attr("required", false);
  });
}

// Modern browsers have built-in number spinner buttons but they don't have
// much flexibility in styling them, so we'll make our own.
function setupQtyButtons() {
  console.log("setupQtyButtons");
  // The decrement button should change the value of the element it's for to be
  // one lower than it currently is, but no lower than zero.  (This is also
  // defined in the HTML as min="0" but the javascript apparently can override
  // it.)
  $('form[action="/cart"] .decrement').click(function() {
    var input = $("#" + $(this).attr("for"));
    input.val(Math.max(0, Number(input.val()) - 1));
  });
  // The increment button should change the value of the element it's for to be
  // one higher than it currently is.
  $('form[action="/cart"] .increment').click(function() {
    var input = $("#" + $(this).attr("for"));
    input.val(Number(input.val()) + 1);
  });
}

// Mailing list signup form that appears only once per recognized visitor.
// Depends on existing element on the page to duplicate into the popup circle.

if (SHOP_CONFIG.get("mlpopup_enabled")) {
  $(document).ready(setup_popup);
}

// Schedule the mailing list popup to show after a delay.
// If the browser looks mobile or the cookie indicates it's
// been shown before, don't.
function setup_popup() {
  if (! (ismobile() || popup_cookie_exists()) && $("." + SHOP_CONFIG.get("mlpopup_classadd")).length > 0)
    setTimeout(popup, SHOP_CONFIG.get("mlpopup_delay"));
}

function ismobile() {
  return(window.matchMedia("only screen and (max-width: 760px)").matches || /Mobi/.test(navigator.userAgent));
}

// Display the mailing list popup.  Set up event handlers
// for closing the popup, and a cookie to prevent it from showing again.
function popup() {
  var mlpopup_classadd = SHOP_CONFIG.get("mlpopup_classadd");
  $("body").append($("<div class='popup'/>"));
  // clone() isn't really correct since I end up
  // with duplicated IDs, but whatever, it works out OK.
  $(".popup").append($("." + mlpopup_classadd).clone());
  $(".popup ." + mlpopup_classadd).prepend("<p style='font-size: 150%;'>★</p>");
  set_popup_cookie();
  $("body").one("click", shutdown_popup); // one = one-shot handler
  $(".popup").on("click", popup_click);
  // don't show the "X" link if they actually clicked on the input line
  $(".popup input").on("click", function(e) { e.stopPropagation(); });
  $(".popup ." + mlpopup_classadd + " form").submit(popup_form_submit);
}

// True if the cookie is found signifying the popup has occurred for this browser.
function popup_cookie_exists() {
  return(Boolean(document.cookie.match(SHOP_CONFIG.get("mlpopup_cookie"))));
}

// Set a cookie to signify that the popup has occurred for this browser.
function set_popup_cookie() {
  document.cookie = SHOP_CONFIG.get("mlpopup_cookie").concat("=True; expires=Fri, 1 Jan 2100 12:00:00 UTC; path=/");
}

// Clear the cookie (via a past expiration date)
// Nothing actually calls this here; it's just a helper for testing.
function clear_popup_cookie() {
  document.cookie = SHOP_CONFIG.get("mlpopup_cookie").concat("=True; expires=Mon, 1 Jan 1900 12:00:00 UTC; path=/");
}

// Remove the popup element,
// and the one click handler potentially remaining.
function shutdown_popup() {
  $(".popup").remove();
  $("body").unbind("click");
  return(false);
}

// When clicking inside the popup element,
// don't propagate the click up to body that would close the popup.
function popup_click(event) {
  if ($(".closebutton").length == 0) {
    $(".popup").append("<div class='closebutton'><a href='#'>✕</a></div>");
    $(".closebutton").click(shutdown_popup);
  }
  event.stopPropagation();
}

// When submitting the form, close the
// popup after a small delay to allow the browser to open the new tab.
function popup_form_submit() {
  setTimeout(shutdown_popup, 100);
}

// Minimal zoom-blocker — does NOT interfere with page scroll.
// The viewport meta (maximum-scale=1, user-scalable=no) already blocks mobile pinch.
// This script only catches a few edge cases on iOS/desktop without breaking scroll.
(function(){
  // Block Ctrl/Cmd + wheel (desktop pinch-to-zoom via trackpad)
  document.addEventListener('wheel', function(e){
    if (e.ctrlKey || e.metaKey) e.preventDefault();
  }, { passive: false });

  // Block Ctrl/Cmd +/-/0 keyboard zoom
  document.addEventListener('keydown', function(e){
    if ((e.ctrlKey || e.metaKey) && ['+','-','=','0'].indexOf(e.key) > -1) {
      e.preventDefault();
    }
  });

  // Block iOS Safari gesture events (pinch on image)
  ['gesturestart','gesturechange','gestureend'].forEach(function(evt){
    document.addEventListener(evt, function(e){ e.preventDefault(); }, { passive: false });
  });
})();

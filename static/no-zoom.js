// Block ALL zoom on mobile — pinch, double-tap, gesture, keyboard shortcuts
(function(){
  // 1. Block pinch zoom on touchstart
  document.addEventListener('touchstart',function(e){
    if(e.touches.length>1){e.preventDefault();e.stopPropagation();}
  },{passive:false,capture:true});

  // 2. Block pinch zoom on touchmove (most important for iOS)
  document.addEventListener('touchmove',function(e){
    if(e.touches.length>1){e.preventDefault();e.stopPropagation();}
    // Also block if page is already zoomed — force reset
    if(e.scale&&e.scale!==1){e.preventDefault();}
  },{passive:false,capture:true});

  // 3. Block double-tap zoom
  var lastTap=0;
  document.addEventListener('touchend',function(e){
    if(e.target.closest&&e.target.closest('.mobile-menu'))return;
    var now=Date.now();
    if(now-lastTap<350){e.preventDefault();}
    lastTap=now;
  },{passive:false});

  // 4. Block iOS gesture events (Safari specific)
  document.addEventListener('gesturestart',function(e){e.preventDefault();},{passive:false,capture:true});
  document.addEventListener('gesturechange',function(e){e.preventDefault();},{passive:false,capture:true});
  document.addEventListener('gestureend',function(e){e.preventDefault();},{passive:false,capture:true});

  // 5. Block Ctrl+scroll / Cmd+scroll zoom (desktop browsers)
  document.addEventListener('wheel',function(e){
    if(e.ctrlKey||e.metaKey){e.preventDefault();}
  },{passive:false});

  // 6. Block Ctrl+Plus/Minus keyboard zoom
  document.addEventListener('keydown',function(e){
    if((e.ctrlKey||e.metaKey)&&(e.key==='+'||e.key==='-'||e.key==='='||e.key==='0')){
      e.preventDefault();
    }
  });

  // 7. Force reset zoom if somehow triggered
  var checkZoom=setInterval(function(){
    if(window.visualViewport&&window.visualViewport.scale>1.01){
      document.body.style.transform='scale(1)';
      document.body.style.transformOrigin='0 0';
      setTimeout(function(){document.body.style.transform='';},50);
    }
  },500);

  // 8. Use visualViewport API to catch and reset zoom
  if(window.visualViewport){
    window.visualViewport.addEventListener('resize',function(){
      if(window.visualViewport.scale>1.01){
        document.querySelector('meta[name="viewport"]').setAttribute('content',
          'width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no');
      }
    });
  }
})();

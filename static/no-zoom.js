// FINAL anti-zoom — block zoom everywhere including images on iOS Safari
(function(){
  // 0. Force touch-action on html + body + everything
  document.documentElement.style.touchAction='pan-y';
  document.documentElement.style.webkitTouchCallout='none';
  document.body.style.touchAction='pan-y';
  document.body.style.webkitTouchCallout='none';

  // 1. CSS injection — block zoom on all elements, especially images
  var s=document.createElement('style');
  s.textContent=[
    'html,body{touch-action:pan-y!important;-webkit-text-size-adjust:100%!important;overscroll-behavior:none!important;}',
    '*{touch-action:pan-y!important;-ms-touch-action:pan-y!important;}',
    'img,picture,video,canvas,svg,figure{touch-action:none!important;-webkit-touch-callout:none!important;-webkit-user-select:none!important;user-select:none!important;}',
  ].join('');
  document.head.appendChild(s);

  // 2. Force viewport
  var vm=document.querySelector('meta[name="viewport"]');
  if(!vm){vm=document.createElement('meta');vm.name='viewport';document.head.appendChild(vm);}
  vm.setAttribute('content','width=device-width,initial-scale=1,minimum-scale=1,maximum-scale=1,user-scalable=no,shrink-to-fit=no');

  // 3. Track touches — block ANY multi-finger interaction
  var fingers=0;
  document.addEventListener('touchstart',function(e){
    fingers=e.touches.length;
    if(fingers>1){e.preventDefault();e.stopImmediatePropagation();return false;}
  },{passive:false,capture:true});

  document.addEventListener('touchmove',function(e){
    if(e.touches.length>1||fingers>1){e.preventDefault();e.stopImmediatePropagation();return false;}
    if(e.scale!==undefined&&e.scale!==1){e.preventDefault();e.stopImmediatePropagation();return false;}
  },{passive:false,capture:true});

  document.addEventListener('touchend',function(e){
    fingers=e.touches.length;
  },{passive:true,capture:true});

  // 4. Block double-tap zoom
  var lastTap=0;
  document.addEventListener('touchend',function(e){
    if(e.target.closest&&e.target.closest('.mobile-menu'))return;
    var now=Date.now();
    if(now-lastTap<400){e.preventDefault();}
    lastTap=now;
  },{passive:false});

  // 5. Block ALL iOS gesture events
  ['gesturestart','gesturechange','gestureend'].forEach(function(evt){
    document.addEventListener(evt,function(e){
      e.preventDefault();e.stopImmediatePropagation();return false;
    },{passive:false,capture:true});
    // Also on window level
    window.addEventListener(evt,function(e){
      e.preventDefault();e.stopImmediatePropagation();return false;
    },{passive:false,capture:true});
  });

  // 6. Intercept touch on every image directly
  function blockImageTouch(img){
    img.addEventListener('touchstart',function(e){
      if(e.touches.length>1){e.preventDefault();e.stopImmediatePropagation();}
    },{passive:false,capture:true});
    img.addEventListener('touchmove',function(e){
      e.preventDefault();e.stopImmediatePropagation();
    },{passive:false,capture:true});
    img.addEventListener('gesturestart',function(e){
      e.preventDefault();e.stopImmediatePropagation();
    },{passive:false});
  }
  // Apply to existing images
  document.querySelectorAll('img,picture,video,canvas,svg').forEach(blockImageTouch);
  // Apply to future images
  new MutationObserver(function(muts){
    muts.forEach(function(m){
      m.addedNodes.forEach(function(n){
        if(n.nodeType===1){
          if(n.matches&&n.matches('img,picture,video,canvas,svg'))blockImageTouch(n);
          if(n.querySelectorAll)n.querySelectorAll('img,picture,video,canvas,svg').forEach(blockImageTouch);
        }
      });
    });
  }).observe(document.body,{childList:true,subtree:true});

  // 7. Block keyboard/wheel zoom
  document.addEventListener('keydown',function(e){
    if((e.ctrlKey||e.metaKey)&&['+','-','=','0'].indexOf(e.key)>-1)e.preventDefault();
  });
  document.addEventListener('wheel',function(e){
    if(e.ctrlKey||e.metaKey)e.preventDefault();
  },{passive:false});

  // 8. Force-reset zoom every 150ms
  if(window.visualViewport){
    var forceReset=function(){
      if(window.visualViewport.scale>1.02){
        vm.setAttribute('content','width=device-width,initial-scale=0.999');
        setTimeout(function(){
          vm.setAttribute('content','width=device-width,initial-scale=1,minimum-scale=1,maximum-scale=1,user-scalable=no,shrink-to-fit=no');
        },50);
      }
    };
    window.visualViewport.addEventListener('resize',forceReset);
    setInterval(forceReset,150);
  }
})();

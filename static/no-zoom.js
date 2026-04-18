// Block ALL zoom everywhere — nuclear approach
(function(){
  // 0. Inject CSS that blocks touch zoom on every single element
  var s=document.createElement('style');
  s.textContent='*{touch-action:pan-x pan-y!important;-ms-touch-action:pan-x pan-y!important;}img,picture,video,canvas,svg{touch-action:none!important;pointer-events:none!important;-webkit-touch-callout:none!important;-webkit-user-select:none!important;user-select:none!important;}';
  document.head.appendChild(s);

  // 1. Force viewport on every page load
  var vm=document.querySelector('meta[name="viewport"]');
  if(vm)vm.setAttribute('content','width=device-width,initial-scale=1,minimum-scale=1,maximum-scale=1,user-scalable=no');

  // 2. Block ALL multi-touch
  document.addEventListener('touchstart',function(e){
    if(e.touches.length>1){e.preventDefault();e.stopImmediatePropagation();}
  },{passive:false,capture:true});

  document.addEventListener('touchmove',function(e){
    if(e.touches.length>1){e.preventDefault();e.stopImmediatePropagation();}
    if(e.scale&&e.scale!==1){e.preventDefault();e.stopImmediatePropagation();}
  },{passive:false,capture:true});

  // 3. Block double-tap zoom
  var lastTap=0;
  document.addEventListener('touchend',function(e){
    if(e.target.closest&&e.target.closest('.mobile-menu'))return;
    var now=Date.now();
    if(now-lastTap<400){e.preventDefault();e.stopImmediatePropagation();}
    lastTap=now;
  },{passive:false,capture:true});

  // 4. Block ALL iOS gesture events
  ['gesturestart','gesturechange','gestureend'].forEach(function(evt){
    document.addEventListener(evt,function(e){e.preventDefault();e.stopImmediatePropagation();},{passive:false,capture:true});
  });

  // 5. Block keyboard zoom
  document.addEventListener('keydown',function(e){
    if((e.ctrlKey||e.metaKey)&&['+','-','=','0'].indexOf(e.key)>-1)e.preventDefault();
  });

  // 6. Block Ctrl+wheel zoom
  document.addEventListener('wheel',function(e){
    if(e.ctrlKey||e.metaKey)e.preventDefault();
  },{passive:false});

  // 7. Monitor and force-reset zoom every 200ms
  if(window.visualViewport){
    var resetZoom=function(){
      if(window.visualViewport.scale>1.05){
        // Force viewport reset
        vm&&vm.setAttribute('content','width=device-width,initial-scale=1,minimum-scale=1,maximum-scale=1,user-scalable=no');
        // Scroll trick to reset iOS zoom
        window.scrollTo(0,window.scrollY);
      }
    };
    window.visualViewport.addEventListener('resize',resetZoom);
    window.visualViewport.addEventListener('scroll',resetZoom);
    setInterval(resetZoom,200);
  }
})();

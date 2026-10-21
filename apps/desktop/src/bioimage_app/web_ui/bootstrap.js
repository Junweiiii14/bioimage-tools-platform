'use strict';
// Runs before CSS and first paint. The desktop injects only validated preferences.
(() => {
  let values=window.__wbBootstrap?.appearance;
  if(!window.__wbBootstrap){try{values=JSON.parse(localStorage.getItem('bioimage-appearance-preview-v1'));}catch{}}
  const choices={theme:['forest','ember','iris','neutral'],density:['comfortable','compact'],motion:['expressive','gentle','reduced']};
  for(const [key,allowed] of Object.entries(choices))if(allowed.includes(values?.[key]))document.documentElement.dataset[key]=values[key];
})();

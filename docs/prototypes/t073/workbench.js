/* T073 interaction prototype. Synthetic display data only; no scientific I/O. */
(() => {
  "use strict";
  const $ = selector => document.querySelector(selector);
  const escape = value => String(value).replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
  const stages = ["配置原图", "自动裁图", "拼图排版", "灰度定量", "结果表"];
  const stageKeys = ["intake", "crop", "compose", "measure", "results"];
  const imageCache = new Map();
  const canvasCache = new Map();
  let timer = null, toastTimer = null, saveTimer = null, nextId = 3;
  let composing = false, pendingFollow = false;
  let state;
  function reset() {
    clearTimeout(timer);
    clearTimeout(saveTimer);
    pendingFollow = false;
    state = {
      figures: [{id:1,name:"Fig 1",n:4,proteins:"p-AKT\nAKT\nβ-actin"},{id:2,name:"Fig 2",n:2,proteins:"p-ERK\nERK"}],
      selected: [1,1,1,1,1,null,null,null], stage:0, active:0, phase:1, cursor:0,
      mode:"ready", follow:true, statuses:[], dirtyRows:{}, angle:-2.8, zoom:1, cropped:false, inspector:false, corrected:false, ambiguityResolved:false, positions:{},
    };
    render();
  }
  const proteins = figure => figure.proteins.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
  function rows() {
    return state.figures.flatMap(f => proteins(f).map(protein => ({figure:f,protein}))).map((row,index) => ({...row,index}));
  }
  function issue() {
    if (!state.figures.length) return "先新建一个 Fig";
    for (const f of state.figures) {
      if (!f.name.trim()) return "请填写 Fig 名称";
      if (!Number.isInteger(f.n) || f.n<1 || f.n>8) return `${f.name}：原型演示 N 范围为 1–8`;
      if (!proteins(f).length) return `${f.name} 还没有蛋白名`;
    }
    if (new Set(state.figures.map(f=>f.name.trim().toLowerCase())).size!==state.figures.length) return "Fig 名称不能重复";
    if (rows().length>8) return "示例只有 8 个采集组，请减少蛋白数";
    const missing = rows().find(r=>state.selected[r.index]==null);
    return missing ? `请为 ${missing.protein} 选择原图` : "";
  }
  function notify(text) {
    clearTimeout(toastTimer); $("#toast").textContent=text; $("#toast").hidden=false;
    toastTimer=setTimeout(()=>{$("#toast").hidden=true;},3500);
  }
  function blot(n=4,kind=1,index=0,strip=false) {
    const safeN = Math.max(1,Math.min(16,Number(n)||4));
    const twoRows=index===1 && $("#simulate-ambiguity").checked;
    const baseKey=[safeN,kind,index,twoRows].join(":");
    const position=state.positions[index] || {left:20,top:40};
    const key=[baseKey,strip,strip?position.left.toFixed(2):'',strip?position.top.toFixed(2):''].join(":");
    if(imageCache.has(key)) return imageCache.get(key);
    if(strip) {
      blot(n,kind,index,false);
      const cropped=document.createElement('canvas');cropped.width=624;cropped.height=105;
      cropped.getContext('2d').drawImage(canvasCache.get(baseKey),position.left*9.6,position.top*4.2,624,105,0,0,624,105);
      const uri=cropped.toDataURL();imageCache.set(key,uri);
      if(imageCache.size>96)imageCache.delete(imageCache.keys().next().value);
      return uri;
    }
    const canvas=document.createElement("canvas"); canvas.width=960;canvas.height=420;
    const ctx=canvas.getContext("2d"), raster=ctx.createImageData(960,420);
    for(let y=0;y<420;y++) for(let x=0;x<960;x++) {
      const yi=y-(x-480)*-.049;
      const inside=x>110&&x<870&&yi>100&&yi<315;
      let v=kind===0?238:24;
      if(inside) v=kind===2?30:213;
      if(inside) {
        for(let lane=0;lane<safeN;lane++) {
          const cx=200+(lane+.5)*(615/safeN), dx=(x-cx)/(200/safeN), dy=(yi-216)/12;
          const signal=(Math.exp(-Math.pow(dx,4)-dy*dy)+(twoRows?Math.exp(-Math.pow(dx,4)-Math.pow((yi-268)/9,2))*.8:0))* (125+20*Math.sin(lane*2+index));
          if(kind!==0) v+=kind===2?signal:-signal;
        }
        if(kind!==2) for(const my of [130,166,211,260,293]) v-=Math.exp(-Math.pow((x-150)/18,4)-Math.pow((yi-my)/7,2))*110;
      }
      v += (Math.sin(x*12.9898+y*78.233+index*7)*43758.5453%1)*2.5;
      const k=(y*960+x)*4; raster.data[k]=raster.data[k+1]=raster.data[k+2]=Math.max(0,Math.min(255,v)); raster.data[k+3]=255;
    }
    ctx.putImageData(raster,0,0);
    canvasCache.set(baseKey,canvas);
    const uri=canvas.toDataURL();imageCache.set(key,uri);return uri;
  }
  function status(index) {
    if(state.dirtyRows[index]) return ["review","未保存"];
    if(state.mode==="review"&&state.cursor===index&&state.phase===1) return ["review","需调整"];
    if(state.statuses[index]) return ["saved","已保存"];
    if(state.mode==="running"&&state.phase===1&&state.cursor===index) return ["saved","定位中"];
    return ["","待处理"];
  }
  function chrome() {
    if(!$('#stage-tabs').children.length)$('#stage-tabs').innerHTML=stages.map((title,i)=>`<button class="stage-tab" role="tab" aria-controls="content" data-stage="${i}"><span class="stage-number"></span>${title}</button>`).join('');
    $('#stage-tabs').querySelectorAll('[data-stage]').forEach((tab,i)=>{const done=state.mode==='done'||state.phase>i&&i>0;tab.classList.toggle('done',done);tab.setAttribute('aria-selected',state.stage===i);tab.querySelector('.stage-number').textContent=done?'✓':i+1;});
    $("#stage-summary").textContent=`${rows().length} 个蛋白 · ${state.figures.length} 个 Fig`;
    const primary=$("#primary-action");
    primary.disabled=state.mode==='saving'||state.mode==="ready"&&!!issue();
    primary.textContent=state.mode==="running"?"暂停处理":state.mode==="review"?"查看待处理图":state.mode==="paused"?"继续自动处理":state.mode==="done"?"导出示例表格":"开始自动处理";
    $("#new-fig").disabled=['running','saving'].includes(state.mode);
    $("#simulate-ambiguity").disabled=state.mode==='saving';
    $("#follow").hidden=state.follow||!["running","paused","review"].includes(state.mode);
    $("#save-state").textContent=state.mode==="done"?"演示已完成":state.mode==="running"?"演示运行中":"示例草稿";
    const line=$("#process-line");line.hidden=["ready","done"].includes(state.mode);
    line.classList.toggle("attention",state.mode==="review");
    const item=rows()[state.cursor];
    line.innerHTML=`<span class="process-dot"></span><span>${escape(state.mode==="review"?`${item?.figure.name} / ${item?.protein}：检测到两排信号，请选定本次目标。`:state.mode==="paused"?"处理已暂停，已保存的步骤保留。":state.phase===1?`正在定位 ${item?.figure.name} / ${item?.protein} · 已保存 ${state.statuses.filter(Boolean).length} / ${rows().length}`:state.phase===2?`正在生成 ${state.figures[state.cursor]?.name} 拼图`:`正在计算 ${state.figures[state.cursor]?.name} 灰度数据`)}</span>`;
  }
  function figureEditor() {
    let offset=0;
    return `<div class="fig-editor"><div class="fig-labels"><span>Fig 名称</span><span>泳道数 N</span><span>蛋白名 · 按顺序，每行一个</span><span>自动分配</span><span></span></div>${state.figures.map(f=>{
      const start=offset+1;offset+=proteins(f).length;
      return `<div class="fig-row"><input class="field" aria-label="${escape(f.name)} 名称" data-fig="${f.id}" data-field="name" maxlength="120" value="${escape(f.name)}"><label class="n-field"><span>N</span><input class="field" type="number" min="1" max="8" aria-label="${escape(f.name)} 泳道数 N" data-fig="${f.id}" data-field="n" value="${f.n}"></label><textarea class="field proteins" aria-label="${escape(f.name)} 蛋白名" data-fig="${f.id}" data-field="proteins" maxlength="2000">${escape(f.proteins)}</textarea><span class="group-range">${offset>=start?`采集组 ${start}–${offset}`:'待填写蛋白名'}</span><button class="icon-button" data-remove="${f.id}" aria-label="移除 ${escape(f.name)}">×</button></div>`;
    }).join("")}<div class="fig-foot"><button class="text-button" data-action="add-fig">＋ 添加 Fig</button><small>蛋白顺序跨 Fig 连续对应采集组。</small></div></div>`;
  }
  function intake() {
    return `<section class="intake-page"><div class="page-heading"><div><h1>配置本次实验</h1><p>填写 Fig 和蛋白名，再选择每个采集组用于裁剪的原图。</p></div><div class="heading-meta">8 个采集组<br>2 个参考结果</div></div>${figureEditor()}<div class="groups-heading"><h2>选择原图</h2><span>${rows().filter(r=>state.selected[r.index]!=null).length} / ${rows().length} 组已选择</span><button class="button quiet" data-action="clear-choice">取消本次选择</button></div><div id="groups">${rows().slice(0,8).map(row=>`<article class="group-row"><div class="group-identity"><h3>${escape(row.protein)}</h3><p>${escape(row.figure.name)} · 采集组 ${row.index+1} · N=${row.figure.n}</p><small class="group-selected">${state.selected[row.index]==null?'请选择原图':'已选裁剪源'}</small></div>${[0,1,2].map(kind=>`<div class="source-option"><div class="source-visual"><button class="source-choice" data-source="${kind}" data-row="${row.index}" aria-label="采集组 ${row.index+1} 原图 ${kind+1}" aria-pressed="${state.selected[row.index]===kind}"><img src="${blot(row.figure.n,kind,row.index)}" alt="采集组 ${row.index+1} 合成原图 ${kind+1}"></button></div><div class="source-caption"><span>Sample_${String(row.index+1).padStart(2,'0')} (${kind+1}).tif</span><button class="text-button" data-preview="${kind}" data-row="${row.index}" aria-label="放大采集组 ${row.index+1} 原图 ${kind+1}">放大</button></div></div>`).join('')}</article>`).join('')}</div><details class="reference-note"><summary>参考结果 · 2 个，不参与顺序分配</summary><p>历史裁剪和验证图在软件中保留原名，可随时查看；原型没有读取真实历史数据。</p></details>${issue()?`<p class="result-note" role="status">${escape(issue())}</p>`:''}</section>`;
  }
  function objectList() {
    return `<aside class="object-list" aria-label="Fig 与蛋白"><div class="list-header"><h2>本次实验</h2><small>${rows().length} 个蛋白</small></div>${state.figures.map(f=>`<div class="fig-group-label"><span>${escape(f.name)}</span><span>N=${f.n}</span></div>${rows().filter(r=>r.figure.id===f.id).map(row=>{const s=status(row.index);return `<button class="object-row" data-object="${row.index}" aria-current="${state.active===row.index}"><img src="${blot(f.n,state.selected[row.index]??1,row.index,true)}" alt=""><span><strong>${escape(row.protein)}</strong><small>${s[1]}</small></span><span class="status-dot ${s[0]}"></span></button>`;}).join('')}`).join('')}</aside>`;
  }
  function inspector(row) {
    const needs=state.mode==='review'&&state.cursor===row.index;
    const saved=!!state.statuses[row.index], dirty=!!state.dirtyRows[row.index];
    return `<aside class="inspector" aria-label="当前图像属性"><button class="button quiet close-inspector" data-action="close-inspector">关闭详情 ×</button><header><h2>${state.stage===1?'裁剪信息':'Fig 信息'}</h2><span class="status-tag ${needs?'warning':''}">${state.mode==='saving'?'保存中':dirty?'未保存':needs?'需调整':saved?'原值已保存':'待处理'}</span></header>${needs?'<div class="review-message"><strong>检测到两排信号</strong><p>拖动裁剪框，只保留本次目标。</p></div>':''}<div><h3>${escape(row.figure.name)} / ${escape(row.protein)}</h3><dl><div class="property"><dt>泳道数 N</dt><dd>${row.figure.n}</dd></div><div class="property"><dt>采集组</dt><dd>${row.index+1}</dd></div><div class="property"><dt>原图</dt><dd>Sample_${String(row.index+1).padStart(2,'0')}</dd></div></dl></div><section class="inspector-section"><h3>裁剪预览</h3><img class="strip-preview" src="${blot(row.figure.n,state.selected[row.index]??1,row.index,true)}" alt="合成裁剪显示预览"><label class="property"><span class="subtle">显示纠偏</span><span><input class="field angle-field" id="angle" ${state.mode==='saving'?'disabled':''} type="number" min="-10" max="10" step="0.1" value="${state.angle.toFixed(1)}" aria-label="显示纠偏角度"> °</span></label><details><summary>范围与检测依据</summary><p>示例展示小角度显示纠偏。正式软件的裁剪与定量使用原图坐标和原始像素，显示变换不会进入定量。</p><p>角色、目标唯一性和全部 N 个槽位须通过独立检查。</p></details></section><div class="action-foot">${needs||dirty?'<button class="button primary" data-action="resolve">保存范围并继续</button><small>只处理当前问题，随后整批自动推进。</small>':saved?'<p class="subtle">此图已保存，无需确认。</p>':'<p class="subtle">开始后自动定位，仅不确定时暂停。</p>'}</div></aside>`;
  }
  function montage(row) {
    return `<div class="montage-space"><div class="montage"><div class="lane-labels">${Array.from({length:Math.min(row.figure.n,16)},(_,i)=>`<span>${i+1}</span>`).join('')}</div>${rows().filter(r=>r.figure.id===row.figure.id).map(r=>`<div class="montage-row"><strong>${escape(r.protein)}</strong><img src="${blot(r.figure.n,state.selected[r.index]??1,r.index,true)}" alt="${escape(r.protein)} 合成拼图"></div>`).join('')}</div></div>`;
  }
  function curve(row) {
    return `<section class="curve-panel"><div class="curve-title"><strong>${escape(row.protein)} · 泳道剖面示意</strong><span class="subtle">合成曲线</span></div><svg viewBox="0 0 600 95" role="img" aria-label="合成泳道曲线，不是科学结果"><path d="M0 80H600" fill="none" stroke="#d9e2dc"/>${Array.from({length:Math.min(row.figure.n,8)},(_,i)=>{const w=600/Math.min(row.figure.n,8),x=i*w;return `<path d="M${x+5} 78 C${x+w*.25} 80 ${x+w*.25} 69 ${x+w*.36} 57 S${x+w*.45} 10 ${x+w*.5} 14 S${x+w*.55} 65 ${x+w*.7} 72 L${x+w-5} 78" fill="none" stroke="#087e71" stroke-width="1.6"/>`;}).join('')}</svg></section>`;
  }
  function workspace() {
    const all=rows(), row=all[Math.min(state.active,all.length-1)];
    if(!row) return '<div class="empty-state"><h2>先建立 Fig</h2><p>填写蛋白名后，即可选择图像。</p><button class="button primary" data-action="add-fig">新建 Fig</button></div>';
    const crop=state.stage===1;
    return `<div class="workspace ${state.inspector?'show-inspector':''}">${objectList()}<section class="image-work"><div class="image-heading"><div><h1>${escape(crop?row.protein:row.figure.name)}</h1><p>${escape(crop?`${row.figure.name} · 采集组 ${row.index+1} · Sample_${String(row.index+1).padStart(2,'0')} (${(state.selected[row.index]??1)+1}).tif`:`${proteins(row.figure).length} 个蛋白 · ${row.figure.n} 个泳道`)}</p></div><button class="button quiet mobile-inspect" data-action="inspector" aria-expanded="${state.inspector}">${state.inspector?'关闭详情':'图像详情'}</button></div><div class="canvas"><div class="canvas-top"><span>${crop?'960 × 420 px · 合成图':state.stage===2?'拼图显示预览':'Fig 图像与泳道'}</span>${crop?`<div class="segmented" role="group" aria-label="图像视图"><button data-view="original" aria-pressed="${!state.cropped}">原图</button><button data-view="crop" aria-pressed="${state.cropped}">裁剪</button></div>`:''}</div><div class="viewport">${crop?`<div class="image-frame" style="width:${state.zoom*100}%"><img src="${blot(row.figure.n,state.selected[row.index]??1,row.index,state.cropped)}" alt="${escape(row.protein)} 合成原图">${state.cropped?'':`<div class="crop-box" tabindex="0" role="group" aria-label="裁剪范围，拖动或方向键调整" style="top:${state.positions[row.index]?.top??40}%;left:${state.positions[row.index]?.left??20}%">${Array.from({length:Math.min(row.figure.n,16)},(_,i)=>`<span data-lane="${i+1}"></span>`).join('')}</div>`}</div>`:montage(row)}</div><div class="canvas-tools"><button class="icon-button" data-action="zoom-out" aria-label="缩小">−</button><button class="button" data-action="fit">${state.zoom===1?'适应窗口':Math.round(state.zoom*100)+'%'}</button><button class="icon-button" data-action="zoom-in" aria-label="放大">＋</button></div></div>${state.stage===3?curve(row):''}<div class="image-foot"><span>${crop?'拖动裁剪框 · 方向键微调 · +/- 缩放':'点击左侧蛋白，查看对应 Fig'}</span><span>原图保留 · 显示与定量分离</span></div></section>${inspector(row)}</div>`;
  }
  function results() {
    if(state.mode!=="done") return '<section class="results-page"><h1>结果表</h1><div class="empty-state"><h2>结果将在处理完成后出现</h2><p>先运行示例流程，观察自动裁剪、拼图、定量与结果汇总。</p><button class="button primary" data-action="start">运行示例流程</button></div></section>';
    const maxN=Math.max(...state.figures.map(f=>Math.min(f.n,16)));
    return `<section class="results-page"><div class="page-heading"><div><h1>本次结果</h1><p>${state.figures.length} 个 Fig 已完成。选择蛋白可返回图像与曲线。</p></div><span class="status-tag">示例流程完成</span></div><div class="result-toolbar"><strong>灰度积分</strong><span>以下是演示数值，不是实际计算结果</span><button class="button" data-action="export">导出示例 CSV</button></div><div class="table-wrap"><table><thead><tr><th>Fig</th><th>蛋白</th>${Array.from({length:maxN},(_,i)=>`<th class="number">泳道 ${i+1}</th>`).join('')}<th>状态</th></tr></thead><tbody>${rows().map(r=>`<tr><td>${escape(r.figure.name)}</td><td><button data-result="${r.index}">${escape(r.protein)}</button></td>${Array.from({length:maxN},(_,i)=>`<td class="number">${i<r.figure.n?sampleValue(r.index,i):'—'}</td>`).join('')}<td><span class="status-tag">示例</span></td></tr>`).join('')}</tbody></table></div><p class="result-note">“—” 表示该 Fig 没有这个泳道，不作为零值。正式软件保留实际计算状态与来源。</p></section>`;
  }
  function sampleValue(row,lane) { return (1882.37+row*217.18+lane*553.26+Math.sin(row+lane)*189).toFixed(2); }
  function render() {
    chrome(); $("#content").innerHTML=state.stage===0?intake():state.stage===4?results():workspace();
    $("#content").dataset.stage=stageKeys[state.stage];
    requestAnimationFrame(fitView);
  }
  function fitView() {
    const viewport=$('.viewport'), montage=$('.montage'), frame=$('.image-frame');
    if(!viewport||(!montage&&!frame))return;
    const padding=parseFloat(getComputedStyle(viewport).paddingLeft)*2;
    const width=montage?650:state.cropped?624:960;
    const height=montage?montage.offsetHeight:state.cropped?105:420;
    const scale=Math.min(1,(viewport.clientWidth-padding)/width,(viewport.clientHeight-padding)/height)*state.zoom;
    if(montage){const space=montage.parentElement;space.style.width=width*scale+'px';space.style.height=height*scale+'px';montage.style.transform=`scale(${scale})`;}
    else frame.style.width=width*scale+'px';
  }
  function interactionLocked(){return composing||drag||document.querySelector('dialog[open]')||document.activeElement?.matches('input,textarea,select,[contenteditable="true"],.crop-box');}
  function refreshProgress() {
    chrome();
    document.querySelectorAll('[data-object]').forEach(button=>{const item=status(Number(button.dataset.object));button.querySelector('small').textContent=item[1];button.querySelector('.status-dot').className='status-dot '+item[0];});
    if(!state.follow)return;
    if(interactionLocked()){pendingFollow=true;return;}
    pendingFollow=false;
    state.stage=state.mode==='done'?4:state.phase;
    state.active=state.phase===1?state.cursor:Math.max(0,rows().findIndex(r=>r.figure.id===state.figures[state.cursor]?.id));
    state.inspector=state.mode==='review';render();
  }
  function closeInspector(){state.inspector=false;render();$('.mobile-inspect')?.focus();}
  function stageCropPosition(crop){
    if(state.mode==='saving')return;
    state.corrected=true;state.positions[state.active]={top:parseFloat(crop.style.top),left:parseFloat(crop.style.left)};
    stageCropEdit();
  }
  function stageCropEdit(){
    state.follow=false;pendingFollow=false;
    state.dirtyRows[state.active]=true;state.statuses[state.active]=false;
    if(['done','running'].includes(state.mode)){clearTimeout(timer);state.mode='paused';state.phase=1;state.cursor=state.active;}
    const row=rows()[state.active];
    const preview=$('.strip-preview');if(preview)preview.src=blot(row.figure.n,state.selected[row.index]??1,row.index,true);
    const badge=$('.inspector .status-tag');if(badge)badge.textContent='未保存';
    const foot=$('.action-foot');if(foot)foot.innerHTML='<button class="button primary" data-action="resolve">保存范围并继续</button><small>当前范围尚未保存。</small>';
    chrome();
  }
  function saveCrop(){
    if(state.mode==='saving')return;
    const index=state.active;
    state.mode='saving';clearTimeout(timer);render();
    saveTimer=setTimeout(()=>{state.statuses[index]=true;delete state.dirtyRows[index];if(index===1)state.ambiguityResolved=true;const next=rows().findIndex(r=>!state.statuses[r.index]);state.phase=next<0?2:1;state.cursor=next<0?0:next;state.mode='running';state.follow=true;state.inspector=false;render();tick();},250);
  }
  function navigate(stage,manual=true) {
    if(manual){state.follow=false;pendingFollow=false;}
    state.stage=stage;state.inspector=false;render();
  }
  function start() {
    if(issue()) {navigate(0);notify(issue());return;}
    const unsaved=Object.keys(state.dirtyRows)[0];
    if(unsaved!==undefined){state.active=Number(unsaved);navigate(1);state.inspector=true;render();notify('请先保存当前裁剪范围，再继续自动处理。');return;}
    if(state.mode==='done'){exportCsv();return;}
    if(state.mode==='running'){clearTimeout(timer);state.mode='paused';render();return;}
    if(state.mode==='review'){state.active=state.cursor;navigate(1,false);state.inspector=true;render();return;}
    state.mode='running';state.follow=true;navigate(state.phase,false);tick();
  }
  function tick() {
    clearTimeout(timer);
    timer=setTimeout(()=>{
      if(state.mode!=="running")return;
      if(Object.keys(state.dirtyRows).length){state.mode='paused';refreshProgress();return;}
      if(state.phase===1&&state.cursor===1&&$("#simulate-ambiguity").checked&&!state.ambiguityResolved){
        state.mode="review";refreshProgress();return;
      }
      if(state.phase===1)state.statuses[state.cursor]=true;
      state.cursor++;
      const count=state.phase===1?rows().length:state.figures.length;
      if(state.cursor>=count){state.phase++;state.cursor=0;}
      if(state.phase>=4){state.mode="done";refreshProgress();notify("示例流程完成，结果表已就绪。");return;}
      refreshProgress();tick();
    },1100);
  }
  function addFig() {
    if(state.mode==='running')return;
    const id=nextId++;state.figures.push({id,name:`Fig ${id}`,n:2,proteins:"新蛋白"});invalidate();state.stage=0;render();
    $(`[data-fig="${id}"][data-field="name"]`)?.focus();
  }
  function invalidate(){clearTimeout(timer);clearTimeout(saveTimer);state.mode='ready';state.phase=1;state.cursor=0;state.statuses=[];state.dirtyRows={};state.ambiguityResolved=false;}
  function exportCsv() {
    if(state.mode!=="done"){notify("示例流程完成后可导出。");return;}
    const csv=['类型,Fig,蛋白,泳道,示例积分',...rows().flatMap(r=>Array.from({length:Math.min(r.figure.n,16)},(_,i)=>['示例数据',r.figure.name,r.protein,i+1,sampleValue(r.index,i)].map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')))].join('\r\n');
    const url=URL.createObjectURL(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'}));
    const link=document.createElement('a');link.href=url;link.download='BioImage-交互原型-示例数据.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  document.addEventListener('click',event=>{
    const target=event.target.closest('button');if(!target)return;
    if(state.mode==='saving'&&!['inspector','close-inspector','fit','zoom-in','zoom-out'].includes(target.dataset.action))return;
    if(target.dataset.stage!=null){navigate(Number(target.dataset.stage));return;}
    if(target.dataset.remove){state.figures=state.figures.filter(f=>f.id!==Number(target.dataset.remove));invalidate();render();return;}
    if(target.dataset.source!=null){state.selected[Number(target.dataset.row)]=Number(target.dataset.source);invalidate();render();return;}
    if(target.dataset.preview!=null){const r=rows()[Number(target.dataset.row)];$('#image-dialog-title').textContent=`采集组 ${r.index+1} · 原图 ${Number(target.dataset.preview)+1}`;$('#large-source').src=blot(r.figure.n,Number(target.dataset.preview),r.index);$('#image-dialog').showModal();return;}
    if(target.dataset.object!=null){state.active=Number(target.dataset.object);state.follow=false;state.zoom=1;render();return;}
    if(target.dataset.result!=null){state.active=Number(target.dataset.result);navigate(3);return;}
    if(target.dataset.view){state.cropped=target.dataset.view==='crop';render();return;}
    const action=target.dataset.action;
    if(action==='add-fig'||target.id==='new-fig')addFig();
    else if(action==='start'||target.id==='primary-action')start();
    else if(action==='export')exportCsv();
    else if(action==='clear-choice'){state.selected.fill(null);invalidate();render();}
    else if(action==='resolve')saveCrop();
    else if(action==='inspector'){state.inspector=!state.inspector;render();$('.close-inspector')?.focus();}
    else if(action==='close-inspector')closeInspector();
    else if(action==='zoom-in'||action==='zoom-out'||action==='fit'){state.zoom=action==='fit'?1:Math.max(.5,Math.min(3,state.zoom+(action==='zoom-in'?.25:-.25)));render();}
    else if(target.id==='follow'){if(Object.keys(state.dirtyRows).length){notify('先保存或处理未保存的范围。');return;}state.follow=true;state.active=state.phase===1?state.cursor:rows().findIndex(r=>r.figure.id===state.figures[state.cursor]?.id);navigate(state.phase,false);}
    else if(target.id==='reset-demo'){reset();notify('已恢复初始示例。');}
    else if(target.id==='settings')$('#settings-dialog').showModal();
    else if(target.id==='close-image')$('#image-dialog').close();
  });
  document.addEventListener('change',event=>{
    const input=event.target;
    if(input.dataset.fig){const f=state.figures.find(f=>f.id===Number(input.dataset.fig));f[input.dataset.field]=input.dataset.field==='n'?Number(input.value):input.value;invalidate();render();}
    else if(input.id==='simulate-ambiguity'){invalidate();render();}
    else if(input.id==='reduce-motion')document.body.classList.toggle('reduce-motion',input.checked);
    else if(input.id==='angle'){if(state.mode==='saving')return;const n=Number(input.value);if(Number.isFinite(n)&&Math.abs(n)<=10){state.angle=n;stageCropEdit();notify('显示角度已记录为原型草稿；不改变示例像素。');}else{input.value=state.angle;notify('角度范围为 −10° 至 10°。');}}
  });
  document.addEventListener('keydown',event=>{
    if(state.mode==='saving'&&event.target.closest('.crop-box,#angle')){event.preventDefault();return;}
    if(event.key==='Escape'&&state.inspector){state.inspector=false;render();$('.mobile-inspect')?.focus();}
    const crop=event.target.closest('.crop-box');
    if(crop&&['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(event.key)){
      event.preventDefault();const vertical=event.key==='ArrowUp'||event.key==='ArrowDown';const prop=vertical?'top':'left';
      const base=parseFloat(crop.style[prop]);crop.style[prop]=Math.max(0,Math.min(vertical?75:35,base+(event.key==='ArrowUp'||event.key==='ArrowLeft'?-1:1)))+'%';stageCropPosition(crop);
    }
  });
  let drag=null;
  document.addEventListener('pointerdown',event=>{
    if(state.mode==='saving')return;
    const crop=event.target.closest('.crop-box');if(!crop||event.button!==0)return;
    drag={crop,id:event.pointerId,x:event.clientX,y:event.clientY,left:parseFloat(crop.style.left),top:parseFloat(crop.style.top),rect:crop.parentElement.getBoundingClientRect()};crop.setPointerCapture(event.pointerId);crop.focus();
  });
  document.addEventListener('pointermove',event=>{if(!drag||event.pointerId!==drag.id)return;drag.crop.style.left=Math.max(0,Math.min(35,drag.left+(event.clientX-drag.x)/drag.rect.width*100))+'%';drag.crop.style.top=Math.max(0,Math.min(75,drag.top+(event.clientY-drag.y)/drag.rect.height*100))+'%';stageCropPosition(drag.crop);});
  document.addEventListener('pointerup',()=>{drag=null;});
  document.addEventListener('pointercancel',()=>{drag=null;});
  document.addEventListener('compositionstart',()=>{composing=true;});
  document.addEventListener('compositionend',()=>{composing=false;});
  document.addEventListener('focusout',()=>queueMicrotask(()=>{if(pendingFollow&&!interactionLocked())refreshProgress();}));
  document.querySelectorAll('dialog').forEach(dialog=>dialog.addEventListener('close',()=>{if(pendingFollow&&!interactionLocked())refreshProgress();}));
  window.addEventListener('resize',fitView);
  window.addEventListener('pagehide',()=>{clearTimeout(timer);clearTimeout(toastTimer);clearTimeout(saveTimer);});
  reset();
})();

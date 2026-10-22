'use strict';

// Pure markup for the batch workbench. Navigation and persistence stay in intake.js.
window.intakeViews = (() => {
  const stageLabel = status => ({pending:'等待计算',running:'正在计算',done:'已保存',needs_review:'需调整',failed:'失败',cancelled:'已取消',interrupted:'未完整提交'}[status] || '待处理');
  const resultLabel = status => ({valid:'有效',quality_review:'质量待复核',not_detected:'未检测到',invalid:'无效',excluded:'已排除',not_run:'待计算',unconfigured:'待配置',pending_review:'待复核',failed:'失败',cancelled:'已取消',interrupted:'未完整提交',result_unavailable:'结果不可用',missing_source:'缺少原图',stale:'输入已变化'}[status] || '待处理');

  // Screen-only envelope: preserve extrema in each bin, never alter the stored profile.
  function profilePoints(profile) {
    const points=[],stride=Math.max(1,Math.ceil(profile.length/256));
    for(let start=0;start<profile.length;start+=stride){
      let low=start,high=start;
      for(let i=start+1;i<Math.min(profile.length,start+stride);i++){
        if(profile[i]<profile[low])low=i;
        if(profile[i]>profile[high])high=i;
      }
      points.push(...[...new Set([start,low,high,Math.min(profile.length-1,start+stride-1)])].sort((a,b)=>a-b));
    }
    return points;
  }

  function figureList(intake, selectedId, selectedRowId) {
    return `<aside class="intake-figure-list" aria-label="Fig 与蛋白"><h2>本次实验</h2>${intake.figures.map(fig=>`
      <section class="intake-object-group"><h3>${escapeText(fig.label)} <small>N=${fig.lane_count}</small></h3>
        ${intake.proteins.filter(p=>p.figure_id===fig.figure_id).map(p=>{const status=intake.workflow.steps.find(s=>s.stage==='measure'&&s.target_id===fig.figure_id)?.status;return `<button class="source-item intake-object ${fig.figure_id===selectedId&&p.protein_id===selectedRowId?'active':''}" data-intake-measure-select="${escapeText(fig.figure_id)}" aria-pressed="${fig.figure_id===selectedId&&p.protein_id===selectedRowId}" data-intake-measure-protein="${escapeText(p.protein_id)}"><span class="source-copy"><strong>${escapeText(p.label)}</strong><small class="${status==='done'?'reviewed':''}">${stageLabel(status)}</small></span></button>`;}).join('')}
      </section>`).join('')}</aside>`;
  }

  function measurement({intake, selected, current, members, outlines, cells, busy, selectedRowId, quant}) {
    const fig=intake.figures.find(f=>f.figure_id===selected?.figure_id);
    const image=current?.image?`<div class="intake-measure-raster"><img src="${escapeText(current.image)}" alt="${escapeText(fig?.label || 'Fig')} · ${escapeText(members.map(p=>p.label).join('、'))}"><svg viewBox="0 0 ${current.width} ${current.height}" aria-label="原图测量区域映射">${outlines}</svg></div>`:`<div class="intake-measure-empty" role="status"><p>${escapeText(current?.error||(!selected?'尚无已保存的 Fig 图片':current?.loading?'正在加载 Fig 图片…':'正在读取已保存的 Fig…'))}</p>${current?.error?'<button class="button subtle" data-intake-preview-retry>重新加载图片</button>':''}</div>`;
    return `<div class="intake-measure-workspace">${figureList(intake,selected?.figure_id,selectedRowId)}
      <section class="intake-measure-main ${window.intakeQuant.previewCollapsed()?'preview-collapsed':''}" tabindex="0" aria-label="Fig 图像与曲线，向下滚动查看全部蛋白"><header class="canvas-heading"><div><h1>原像素定量</h1><p>${escapeText(fig?.label || '等待成图')} · ${members.length} 个蛋白 · ${fig?.lane_count || 0} 个泳道</p></div><label class="intake-figure-select">查看 Fig<select data-intake-measure-figure>${(intake.figuresReady||[]).map(f=>`<option value="${escapeText(f.figure_id)}" ${f===selected?'selected':''}>${escapeText(intake.figures.find(x=>x.figure_id===f.figure_id)?.label||f.figure_id)}</option>`).join('')}</select></label></header>
        <button class="text-button intake-preview-toggle" data-iq-action="toggle-preview" aria-expanded="${!window.intakeQuant.previewCollapsed()}" aria-controls="intake-fig-image">${icon(window.intakeQuant.previewCollapsed()?'chevron-down':'chevron-up')}${window.intakeQuant.previewCollapsed()?'展开 Fig 图像':'收起 Fig 图像'}</button>
        <section id="intake-fig-image" class="intake-measure-image" aria-label="当前 Fig 与测量区域"><span class="intake-measure-caption">Fig 图像与原图槽位映射</span><div class="intake-measure-viewport">${image}</div><div class="floating-tools"><button class="icon-button" data-intake-measure-zoom="out" aria-label="缩小 Fig">${icon('minus')}</button><button class="zoom-label" data-intake-measure-zoom="fit">适应窗口</button><button class="icon-button" data-intake-measure-zoom="in" aria-label="放大 Fig">${icon('plus')}</button></div></section>
        ${window.intakeQuant.figureMarkup(fig,members,quant)}<p class="intake-measure-foot">查看图像对应位置 · 显示缩放不影响原像素计算</p>
      </section>
      <aside class="intake-measure-inspector" aria-label="蛋白与测量状态"><h2>测量记录</h2>${members.map(p=>{
        const values=cells.filter(c=>c.rowId===p.protein_id);
        return `<section class="inspect-section"><h3>${escapeText(p.label)}</h3><dl class="intake-values">${values.map(c=>`<div><dt>泳道 ${c.lane}</dt><dd title="${escapeText(resultLabel(c.status)+(c.reason?'：'+c.reason:''))}">${number(c.rawIntegral)}${c.rawIntegral!=null&&c.status!=='valid'?'<sup aria-label="质量待复核">*</sup>':''}</dd></div>`).join('')||'<div><dt>等待已提交结果</dt></div>'}</dl><button class="text-button" data-intake-crop-action="source" data-id="${escapeText(p.protein_id)}" ${busy?'disabled':''}>查看原图与范围</button></section>`;
      }).join('')}<details><summary>数值说明</summary><p>显示原始灰度积分；* 表示质量待复核。缺失与失败保留为空，有效信号独立保存在完整结果记录中。</p></details></aside>
    </div>`;
  }

  function results({intake, cells, busy}) {
    if(intake.visibleTable){
      const table=intake.visibleTable,marks=new Set(table.quality.map(([r,c])=>`${r}:${c}`));
      const body=table.rows.map((row,r)=>`<tr>${row.map((v,c)=>{
        const numeric=c>=2&&c<row.length-1;
        const source=numeric?cells.find(cell=>cell.rowId===intake.proteins[r].protein_id&&cell.lane===c-1):null;
        const title=numeric?(source?resultLabel(source.status)+(source.reason?'：'+source.reason:''):'没有已提交结果'):'';
        const content=c===1?`<button class="text-button" data-intake-crop-action="source" data-id="${escapeText(intake.proteins[r].protein_id)}" ${busy?'disabled':''}>${escapeText(v)}</button>`:numeric?number(v):c===row.length-1?`<span class="result-state">${escapeText(v)}</span>`:escapeText(v);
        return `<td class="${numeric?'intake-number':''}" title="${escapeText(title)}">${content}${marks.has(`${r}:${c}`)?'<sup>*</sup>':''}</td>`;
      }).join('')}</tr>`).join('');
      return `<section class="intake-result-grid"><div class="intake-result-toolbar"><strong>原始灰度积分</strong><span>按 Fig、蛋白与泳道排列</span></div><div class="results-scroll"><table><thead><tr>${table.headers.map((h,c)=>`<th class="${c>=2&&c<table.headers.length-1?'intake-number':''}">${escapeText(h)}</th>`).join('')}</tr></thead><tbody>${body||'<tr><td>尚无已配置的蛋白</td></tr>'}</tbody></table></div><p class="intake-result-note">— 表示无已提交值；* 表示质量待复核。展开完整记录可查看有效信号与具体原因。</p></section>`;
    }
    const maxN=Math.max(0,...intake.figures.map(f=>f.lane_count||0));
    const body=intake.proteins.map(p=>{
      const fig=intake.figures.find(f=>f.figure_id===p.figure_id);
      const values=cells.filter(c=>c.rowId===p.protein_id);
      const quality=values.filter(c=>c.status!=='valid');
      const status=values.length===fig?.lane_count&&!quality.length?'已完成':quality.length?`${quality.length} 项需查看`:'待计算';
      return `<tr><td>${escapeText(fig?.label || '')}</td><td><button class="text-button" data-intake-crop-action="source" data-id="${escapeText(p.protein_id)}" ${busy?'disabled':''}>${escapeText(p.label)}</button></td>${Array.from({length:maxN},(_,i)=>{
        const c=values.find(c=>c.lane===i+1);
        return `<td class="intake-number" title="${escapeText(c?resultLabel(c.status)+(c.reason?'：'+c.reason:''):'没有已提交结果')}">${number(c?.rawIntegral)}${c?.rawIntegral!=null&&c.status!=='valid'?'<sup>*</sup>':''}</td>`;
      }).join('')}<td><span class="result-state">${status}</span></td></tr>`;
    }).join('');
    return `<section class="intake-result-grid"><div class="intake-result-toolbar"><strong>原始灰度积分</strong><span>按 Fig、蛋白与泳道排列</span></div><div class="results-scroll"><table><thead><tr><th>Fig</th><th>蛋白</th>${Array.from({length:maxN},(_,i)=>`<th class="intake-number">泳道 ${i+1}</th>`).join('')}<th>状态</th></tr></thead><tbody>${body||'<tr><td>尚无已配置的蛋白</td></tr>'}</tbody></table></div><p class="intake-result-note">— 表示无已提交值；* 表示质量待复核。展开完整记录可查看有效信号与具体原因。</p></section>`;
  }
  return {measurement,results};
})();

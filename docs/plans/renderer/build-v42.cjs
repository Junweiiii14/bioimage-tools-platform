const fs = require('node:fs');
const path = require('node:path');
const {marked} = require(process.env.MARKED_MODULE_PATH || 'marked');
const root = path.resolve(__dirname, '../../..');
const documents = ['docs/plans/research-platform-rd', 'docs/plans/workflow-development', 'docs/maintenance-plan', 'docs/plans/experiment-research-roadmap', 'docs/research/2026-11-02-wb-workflow-audit'];
const css = fs.readFileSync(path.join(__dirname, 'v42-document.css'), 'utf8');
const js = fs.readFileSync(path.join(__dirname, 'v42-document.js'), 'utf8');
const escape = text => text.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
for (const relative of documents) {
  const source = path.join(root, relative + '.md');
  const md = fs.readFileSync(source, 'utf8');
  const title = md.split('\n')[0].replace(/^#\s*/, '').trim();
  let body = marked.parse(md, {gfm:true});
  body = body.replace(/href="([^"#][^"]*)"/g, (all, href) => {
    if (/^[a-z][a-z0-9+.-]*:/i.test(href)) return all;
    let destination = path.resolve(path.dirname(source), href);
    if (documents.some(doc => destination === path.join(root, doc + '.md'))) destination = destination.replace(/\.md$/, '.html');
    return 'href="' + path.relative(path.dirname(source), destination).split(path.sep).join('/') + '"';
  });
  let heading = 0, block = 0;
  const toc = [];
  body = body.replace(/<h([2-4])>(.*?)<\/h\1>/gs, (_, level, content) => {
    const id = level === '2' ? `section-${toc.length + 1}` : `heading-${++heading}`;
    if (level === '2') toc.push({id, title:content.replace(/<[^>]*>/g, '')});
    return `<h${level} id="${id}" tabindex="-1">${content}<a class="permalink" href="#${id}" aria-label="链接到此节">§</a></h${level}>`;
  });
  body = body.replace(/<table>/g, '<div class="table-wrap" tabindex="0" role="region" aria-label="可横向滚动的数据表"><table>').replace(/<\/table>/g, '</table></div>');
  body = body.replace(/<(p|li|pre|tr)>/g, (_, tag) => `<${tag} id="block-${++block}">`);
  const navigation = toc.map(item => `<a href="#${item.id}">${escape(item.title)}</a>`).join('');
  const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(title)}</title><style>${css}</style></head><body><a class="skip" href="#document">跳到正文</a><div class="mobile-bar"><strong>科研数据平台 · 4.2</strong><button id="menu-toggle" aria-controls="navigation" aria-expanded="false">目录与检索</button></div><aside class="sidebar" id="navigation"><a class="brand" href="#document">科研数据平台</a><p class="edition">合并方案 4.2 · 2026.11.02</p><label class="search-label" for="search">查找操作、模块或维护要求</label><input class="search-box" id="search" type="search" placeholder="例如：操作 / 版本 / 审查"><p class="search-status" id="search-status" aria-live="polite">搜索全文；内容始终完整保留。</p><div id="results" class="search-results"></div><nav class="toc" aria-label="文档目录">${navigation}</nav><button class="print-button" id="print">打印 / 保存 PDF</button><p class="side-note">方案与实施状态分别标注。当前仅更新规划目录，未同步开发窗口。</p></aside><main class="page"><article class="document" id="document" tabindex="-1">${body}<footer class="document-footer">B-016 · GitHub待接入草案；不代表算法对照、产品验收或代码重构已经完成。离线可读，本地参考链接依赖对应文件。</footer></article></main><script>${js}</script></body></html>`;
  const output = path.join(root, relative + '.html');
  fs.writeFileSync(output, html);
  console.log(JSON.stringify({output, chapters:toc.length, bytes:Buffer.byteLength(html)}));
}

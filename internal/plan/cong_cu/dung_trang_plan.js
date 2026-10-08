// Dựng docs/server_plan.html từ plan theo khối (internal/plan/*.md).
// Bước của từng khối đọc thẳng từ Markdown để trang không lệch với plan.
const fs = require('fs');
const path = require('path');
// Chạy: node internal/plan/cong_cu/dung_trang_plan.js  (từ thư mục server/)
const PLAN = path.join(__dirname, '..') + '/';
const out = process.argv[2] || path.join(__dirname, '../../../docs/server_plan.html');
const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const md = s => esc(s).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');

// ---------- đọc Markdown ----------
function parseBlocks(file){
  const lines = fs.readFileSync(PLAN + file, 'utf8').split(/\r?\n/);
  const blocks = {}; let cur = null, lastBullet = null;
  for (const ln of lines){
    let m;
    if ((m = ln.match(/^### ([A-Z0-9-]+) · (.+)$/))){ cur = { id:m[1], title:m[2], info:[], steps:[], notes:[] }; blocks[cur.id] = cur; lastBullet = null; continue; }
    if (/^##? /.test(ln)){ cur = null; continue; }
    if (!cur) continue;
    if ((m = ln.match(/^- \*\*([^*]+):\*\*\s*(.*)$/))){ lastBullet = [m[1], m[2]]; cur.info.push(lastBullet); continue; }
    if ((m = ln.match(/^  - (.+)$/)) && lastBullet){ lastBullet[1] += (lastBullet[1] ? ' ' : '') + m[1]; continue; }
    if ((m = ln.match(/^\|\s*([A-Z][A-Z0-9-]*\.\d+)\s*\|(.+)\|\s*$/))){
      const cells = m[2].split(/\s\|\s/).map(s => s.trim());
      cur.steps.push({ id:m[1], what:cells[0], check:cells[cells.length - 1], wait:/⏸/.test(cells.join(' ')) });
      continue;
    }
    if ((m = ln.match(/^\*\*([^*]+):\*\*\s*(.+)$/))){ cur.notes.push([m[1], m[2]]); lastBullet = null; continue; }
    if (ln.trim() && !ln.startsWith('|') && !ln.startsWith('-')) { lastBullet = null; }
  }
  return blocks;
}
const B = Object.assign({}, parseBlocks('khoi_server.md'), parseBlocks('khoi_may.md'));

// G0 và C0 nằm dạng bảng trong hop_dong.md
function parseTable(file, prefix){
  const rows = [];
  for (const ln of fs.readFileSync(PLAN + file, 'utf8').split(/\r?\n/)){
    const m = ln.match(new RegExp('^\\|\\s*(' + prefix + '\\.\\d+)\\s*\\|(.+)\\|\\s*$'));
    if (m){ const c = m[2].split(/\s\|\s/).map(s => s.trim()); rows.push({ id:m[1], what:c[0] + (c.length > 3 ? ' — ' + c[2] : ''), check:c.length > 3 ? c[2] : c[c.length - 1], wait:/Q\d/.test(c[c.length - 1]) && prefix === 'C0' ? c[c.length - 1] : '' }); }
  }
  return rows;
}
const g0 = parseTable('hop_dong.md', 'G0').map(r => ({ ...r, what:r.what.split(' — ')[0] }));
const c0 = parseTable('hop_dong.md', 'C0').map(r => ({ id:r.id, what:r.what.split(' — ')[0], check:r.check, wait:!!r.wait, q:r.wait }));
B['G0'] = { id:'G0', title:'Cổng mật mã', steps:g0.map(r => ({ id:r.id, what:r.what, check:r.check })), info:[['Trách nhiệm','Trả lời bằng test và số đo: HPKE, Ed25519, AES-GCM của `cryptography` có đúng và đủ nhanh trên Pi thật không; long-poll qua TLS của cheroot có giữ được không. Không đạt thì dừng và hỏi user.']], notes:[] };
B['C0'] = { id:'C0', title:'Hợp đồng chung', steps:c0.map(r => ({ id:r.id, what:r.what + (r.q ? ' (' + r.q + ')' : ''), check:r.check, wait:r.wait })), info:[['Trách nhiệm','Chốt routing, gói FM1, body route agent, snapshot, loại lệnh, ngữ pháp helper, chủ sở hữu bảng, cấu hình và hàm nối. Chưa duyệt xong thì không khối nào bắt đầu code.']], notes:[] };

// ---------- thông tin không nằm trong Markdown dạng bảng ----------
const META = {
  'G0':{short:'Cổng mật mã', side:'t0', wave:0, gate:[], file:'hop_dong.md'},
  'C0':{short:'Hợp đồng chung', side:'t0', wave:0, gate:['Q8','Q1'], file:'hop_dong.md'},
  'S-DB':{short:'MySQL, migration', side:'srv', wave:1, gate:[]},
  'S-NET':{short:'TLS, hai cổng', side:'srv', wave:1, gate:['Q2','Q9'], partial:true},
  'UI-SHELL':{short:'Khung trang quản trị', side:'ui', wave:1, gate:[]},
  'S-SECA':{short:'Bảo mật A', side:'sec', wave:2, gate:[]},
  'S-FM1':{short:'Middleware FM1', side:'sec', wave:2, gate:['Q1']},
  'M-ACC':{short:'Tài khoản, quyền', side:'srv', wave:2, gate:[]},
  'M-MAC':{short:'Máy, long-poll', side:'srv', wave:2, gate:[]},
  'M-KEY':{short:'Khoá, ghép máy', side:'srv', wave:2, gate:[]},
  'M-CAT':{short:'Thư viện món', side:'srv', wave:2, gate:['Q7'], partial:true},
  'M-MENU':{short:'Menu', side:'srv', wave:3, gate:[]},
  'M-PUB':{short:'Phát menu', side:'srv', wave:3, gate:[]},
  'M-ING':{short:'Nhận dữ liệu máy', side:'srv', wave:3, gate:[]},
  'M-REP':{short:'Báo cáo', side:'srv', wave:3, gate:[]},
  'M-CMD':{short:'Hàng đợi lệnh', side:'srv', wave:3, gate:['Q3'], partial:true},
  'S-EPOCH':{short:'Khôi phục DB', side:'srv', wave:4, gate:['Q4','Q10'], partial:true},
  'A-POS':{short:'Màn bán hàng', side:'mac', wave:1, gate:['Q6']},
  'A-HOST':{short:'User, thư mục, service', side:'mac', wave:1, gate:['Q6']},
  'A-DB':{short:'Bảng agent', side:'mac', wave:1, gate:['Q6']},
  'H-LOCAL':{short:'Helper kiosk', side:'mac', wave:1, gate:['Q6']},
  'A-NET':{short:'Kênh HTTPS, FM1 máy', side:'mac', wave:2, gate:['Q6','Q1']},
  'A-APPLY':{short:'Áp menu', side:'mac', wave:3, gate:['Q6']},
  'A-STOCK':{short:'Báo tồn kho', side:'mac', wave:3, gate:['Q6']},
  'A-UP':{short:'Gửi đơn, lỗi', side:'mac', wave:3, gate:['Q6']},
  'A-RUN':{short:'Chạy lệnh', side:'mac', wave:3, gate:['Q6']},
};
for (const id in META){ if (!B[id]) throw new Error('thiếu khối trong Markdown: ' + id); Object.assign(B[id], META[id]); B[id].file = B[id].file || (id.startsWith('A-') || id.startsWith('H-') ? 'khoi_may.md' : 'khoi_server.md'); }
for (const id in B){ if (!META[id]) throw new Error('khối lạ trong Markdown: ' + id); }
const blocked = b => b.gate.length && !b.partial;           // cả khối chờ user
const sym = b => blocked(b) ? '⏸' : '○';
const IDS = Object.keys(META);
const nSteps = IDS.reduce((n, id) => n + B[id].steps.length, 0);

// ---------- sơ đồ khối (SVG tĩnh, theo sơ đồ râu của thiết kế) ----------
const POS = {
  'G0':[40,40,200,60], 'C0':[256,40,200,60],
  'S-DB':[40,330,150,64], 'S-EPOCH':[40,470,150,64],
  'M-ACC':[214,150,190,60], 'M-CAT':[214,216,190,60], 'M-MENU':[214,282,190,60], 'M-REP':[214,348,190,60], 'M-KEY':[214,414,190,60], 'M-MAC':[214,480,190,60], 'M-CMD':[214,546,190,60], 'M-PUB':[214,612,190,60], 'M-ING':[214,678,190,60],
  'S-SECA':[452,236,168,70], 'S-FM1':[452,540,168,70],
  'S-NET':[664,378,150,70],
  'UI-SHELL':[920,152,180,60],
  'A-NET':[920,430,160,70],
  'A-APPLY':[1124,330,170,60], 'A-STOCK':[1124,396,170,60], 'A-UP':[1124,462,170,60], 'A-RUN':[1124,528,170,60],
  'A-DB':[1330,426,140,64], 'A-HOST':[920,300,160,60], 'H-LOCAL':[1124,640,170,60], 'A-POS':[1330,640,140,60],
};
const W = 1500, H = 780;
const box = id => {
  const b = B[id], [x, y, w, h] = POS[id];
  const st = `${sym(b)} 0/${b.steps.length}`;
  let t = `<g class="bk ${b.side}${blocked(b) ? ' wait' : ''}"><a href="#k-${id.toLowerCase()}"><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="9"/>`;
  t += `<text class="bid" x="${x + 10}" y="${y + 18}">${id}</text><text class="bst" x="${x + w - 10}" y="${y + 18}" text-anchor="end">${st}</text>`;
  t += `<text class="bnm" x="${x + 10}" y="${y + 36}">${esc(b.short)}</text>`;
  const tag = (b.gate.length ? '⏸ ' + b.gate.join('·') + ' · ' : '') + 'đợt ' + b.wave;
  t += `<text class="bwv${b.gate.length ? ' q' : ''}" x="${x + 10}" y="${y + 52}">${esc(tag)}</text>`;
  return t + '</a></g>';
};
const mid = (id, side) => { const [x, y, w, h] = POS[id]; return side === 'r' ? [x + w, y + h / 2] : side === 'l' ? [x, y + h / 2] : side === 't' ? [x + w / 2, y] : [x + w / 2, y + h]; };
const cv = (a, b, cls) => { const [x1, y1] = a, [x2, y2] = b, mx = (x1 + x2) / 2; return `<path class="e${cls ? ' ' + cls : ''}" d="M${x1} ${y1} C${mx} ${y1} ${mx} ${y2} ${x2 - 2} ${y2}" marker-end="url(#ah)"/>`; };
const ln = (pts, cls) => `<path class="e${cls ? ' ' + cls : ''}" d="M${pts.map(p => p.join(' ')).join(' L')}" marker-end="url(#ah)"/>`;
const edges = [
  ...['M-ACC','M-CAT','M-MENU','M-REP','M-MAC','M-CMD'].map(id => cv(mid(id,'r'), [452, 271], 'a')),
  ...['M-KEY','M-MAC','M-CMD','M-PUB','M-ING'].map(id => cv(mid(id,'r'), [452, 575], 'f')),
  cv(mid('S-SECA','r'), [664, 400], 'a'), cv(mid('S-FM1','r'), [664, 426], 'f'),
  cv(mid('UI-SHELL','l'), [814, 395], 'a'),
  cv(mid('S-NET','r'), mid('A-NET','l'), 'lan'),
  ...['A-APPLY','A-STOCK','A-UP','A-RUN'].map(id => cv(mid('A-NET','r'), mid(id,'l'), 'f')),
  ...['A-APPLY','A-STOCK','A-UP','A-RUN'].map(id => cv(mid(id,'r'), [1330, 458])),
  ln([[1209, 588], [1209, 640]]),
  cv(mid('H-LOCAL','r'), mid('A-POS','l')),
  cv(mid('S-DB','r'), [214, 362], 'g'),
].join('');
const svg = `<svg class="map" viewBox="0 0 ${W} ${H}" role="img" aria-label="Sơ đồ khối. Trên cùng là tầng 0 gồm cổng mật mã G0 và hợp đồng C0. Bên trái là server: kho S-DB và S-EPOCH, chín module, hai khối bảo mật S-SECA và S-FM1, khối cổng S-NET. Giữa là LAN TLS 1.3. Bên phải là trình duyệt với UI-SHELL và máy FlexMix: A-NET, bốn module agent, A-DB, A-HOST, helper H-LOCAL và màn bán hàng A-POS. Mỗi khối ghi trạng thái, số bước, đợt và câu hỏi đang chờ.">
<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ahp" d="M0,0 L10,5 L0,10 z"/></marker></defs>
<rect class="zone t0" x="24" y="16" width="448" height="100" rx="12"/><text class="zt" x="40" y="32">TẦNG 0 · LÀM TRƯỚC MỌI KHỐI</text>
<rect class="zone" x="24" y="124" width="808" height="640" rx="14"/><text class="zt" x="40" y="142">SERVER MẸ</text>
<text class="ch" x="115" y="166" text-anchor="middle">KHO</text><text class="ch" x="309" y="142" text-anchor="middle">MODULE</text><text class="ch" x="536" y="214" text-anchor="middle">BẢO MẬT</text><text class="ch" x="739" y="368" text-anchor="middle">CỔNG</text>
<rect class="lanband" x="846" y="124" width="52" height="640" rx="8"/><text class="lant" transform="translate(878 444) rotate(-90)" text-anchor="middle">LAN · TLS 1.3 · CA NỘI BỘ</text>
<rect class="zone" x="906" y="124" width="208" height="96" rx="12"/><text class="zt" x="920" y="142">TRÌNH DUYỆT</text>
<rect class="zone" x="906" y="236" width="578" height="528" rx="14"/><text class="zt" x="920" y="254">MÁY FLEXMIX · PI</text>
<rect class="zone2" x="912" y="270" width="566" height="338" rx="10"/><text class="zt2" x="1124" y="318">AGENT · USER flexmix-agent</text>
<rect class="zone2" x="1110" y="620" width="368" height="136" rx="10"/><text class="zt2" x="1124" y="744">USER KIOSK · flexxource</text>
${edges}${IDS.map(box).join('')}</svg>`;

// ---------- thứ tự làm theo đợt ----------
const WAVE_NAME = ['Tầng 0 · hợp đồng và cổng mật mã', 'Đợt 1 · chỉ cần hợp đồng', 'Đợt 2 · cần khối nền chạy thật', 'Đợt 3 · module nghiệp vụ', 'Đợt 4 · khối cắt ngang'];
const chip = id => { const b = B[id]; return `<li class="chip ${b.side}${blocked(b) ? ' wait' : ''}"><a href="#k-${id.toLowerCase()}"><span class="st">${sym(b)}</span><b>${id}</b> ${esc(b.short)} <span class="cnt">0/${b.steps.length}</span>${b.gate.length ? `<span class="cq">${b.gate.join(' · ')}</span>` : ''}</a></li>`; };
const waves = WAVE_NAME.map((n, w) => `<div class="wave"><div class="wh">${esc(n)}</div><ul class="chips">${IDS.filter(id => B[id].wave === w).map(chip).join('')}</ul></div>`).join('');

// ---------- ráp và triển khai (đọc từ rap_trien_khai.md) ----------
const rapSrc = fs.readFileSync(PLAN + 'rap_trien_khai.md', 'utf8');
const RAPS = [];
for (const sec of rapSrc.split(/\r?\n### /).slice(1)){
  const L = sec.split(/\r?\n/); const m = L[0].match(/^(R\d|X\d) · (.+)$/); if (!m) continue;
  const r = { id:m[1], title:m[2], info:[], head:null, rows:[], notes:[] }; let last = null;
  for (let i = 1; i < L.length; i++){
    const l = L[i]; let k;
    if (/^\|/.test(l)){
      if (/^\|\s*-/.test(l)) continue;
      const cells = l.replace(/^\|\s*|\s*\|\s*$/g, "").split(/\s\|\s/);
      if (L[i + 1] && /^\|\s*-/.test(L[i + 1])) r.head = cells; else r.rows.push(cells);
      continue;
    }
    if ((k = l.match(/^- \*\*([^*]+):\*\*\s*(.*)$/))){ last = [k[1], k[2]]; r.info.push(last); continue; }
    if ((k = l.match(/^  - (.+)$/)) && last){ last[1] += (last[1] ? " " : "") + k[1]; continue; }
    if ((k = l.match(/^\*\*([^*]+):\*\*\s*(.+)$/))){ r.notes.push([k[1], k[2]]); last = null; continue; }
    if (l.trim() && !/^#/.test(l)) { r.notes.push(["", l.trim()]); last = null; }
  }
  RAPS.push(r);
}
const rapCard = r => `<article class="rap" id="${r.id.toLowerCase()}"><header><span class="ph-id">${r.id}</span><h3>${esc(r.title)}</h3><span class="pill">○ chưa làm</span></header>${r.info.length ? `<dl class="io">${r.info.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${md(v)}</dd></div>`).join("")}</dl>` : ""}${r.rows.length ? `<div class="tbl"><table>${r.head ? `<thead><tr>${r.head.map(h => `<th>${md(h)}</th>`).join("")}</tr></thead>` : ""}<tbody>${r.rows.map(c => `<tr>${c.map(x => `<td>${md(x)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>` : ""}${r.notes.map(([k, v]) => `<p class="note">${k ? `<b>${esc(k)}:</b> ` : ""}${md(v)}</p>`).join("")}</article>`;
const raps = RAPS.filter(r => r.id[0] === 'R').map(rapCard).join('');
const xs = RAPS.filter(r => r.id[0] === 'X').map(rapCard).join('');

// ---------- thẻ từng khối ----------
const card = id => { const b = B[id];
  return `<article class="blk ${b.side}" id="k-${id.toLowerCase()}">
  <header><span class="ph-id">${id}</span><div><h3>${esc(b.title)}</h3><div class="src">Đợt ${b.wave}${b.gate.length ? ' · Chờ: ' + b.gate.map(q => `<a href="#${q.toLowerCase()}">${q}</a>`).join(', ') : ''} · Chi tiết: <a href="../internal/plan/${b.file}"><code>internal/plan/${b.file}</code></a></div></div><span class="pill${blocked(b) ? ' h' : ''}">${blocked(b) ? '⏸ chờ ' + b.gate.join(', ') : '○ chưa làm'}</span></header>
  ${b.info.length ? `<dl class="io">${b.info.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${md(v)}</dd></div>`).join('')}</dl>` : ''}
  <div class="tbl"><table><thead><tr><th>Bước</th><th>Việc</th><th>Kiểm</th></tr></thead><tbody>${b.steps.map(s => `<tr><td class="sid">${s.wait ? '⏸' : sym(b)} ${s.id}</td><td>${md(s.what)}</td><td>${md(s.check)}</td></tr>`).join('')}</tbody></table></div>
  ${b.notes.map(([k, v]) => `<p class="note"><b>${esc(k)}:</b> ${md(v)}</p>`).join('')}
</article>`; };
const groups = [['Tầng 0', ['G0','C0']], ['Nền và khung server', ['S-DB','S-NET','UI-SHELL']], ['Bảo mật', ['S-SECA','S-FM1']], ['Module server', ['M-ACC','M-MAC','M-KEY','M-CAT','M-MENU','M-PUB','M-ING','M-REP','M-CMD']], ['Cắt ngang', ['S-EPOCH']], ['Nền của máy', ['A-POS','A-HOST','A-DB','H-LOCAL']], ['Kênh và module của máy', ['A-NET','A-APPLY','A-STOCK','A-UP','A-RUN']]];
const cards = groups.map(([n, ids]) => `<h3 class="grp">${esc(n)}</h3>${ids.map(card).join('')}`).join('');

// ---------- bảng mối nối, câu hỏi: đọc từ index.md ----------
const idx = fs.readFileSync(PLAN + 'index.md', 'utf8');
const tableAfter = (heading, cols) => {
  const part = idx.split(heading)[1].split(/\r?\n##+ /)[0];
  return part.split(/\r?\n/).filter(l => /^\|/.test(l) && !/^\|\s*-/.test(l)).slice(1).map(l => l.replace(/^\|\s*|\s*\|\s*$/g, '').split(/\s\|\s/));
};
const joints = tableAfter('## Mối nối giữa các khối');
const qs = tableAfter('## Câu hỏi chờ user');

const css = fs.readFileSync(path.join(__dirname, 'plan_page.css'), 'utf8');
const html = `<!doctype html>
<html lang="vi">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Server mẹ · Kế hoạch theo khối</title>
<meta name="description" content="Kế hoạch xây dựng server mẹ FlexMix bản 2 theo khối: ${IDS.length} khối, ${nSteps} bước, 6 lần ráp và 6 bước triển khai.">
<link rel="stylesheet" href="cryptography/fonts.css">
<style>
${css}
</style>
<body>
<div class="page">
  <header class="masthead">
    <div style="display:grid;gap:10px">
      <div class="eyebrow">Kế hoạch xây dựng · theo khối · bản 2</div>
      <h1>Server mẹ FlexMix: xây dựng theo từng khối</h1>
      <p class="lead">Mỗi khối là một ô trong sơ đồ tổng quan của thiết kế: một trách nhiệm, hợp đồng vào ra rõ ràng, test riêng bằng stub. Có ${IDS.length} khối với ${nSteps} bước, rồi 6 lần ráp và 6 bước triển khai. Trang này đọc trực tiếp từ các file Markdown ở <code>internal/plan/</code>.</p>
    </div>
    <div class="meta">
      <span><b>Trạng thái:</b> chưa thực hiện, chưa có dòng code nào</span>
      <span><b>Thiết kế:</b> <a href="server_architect.html">server_architect.html</a></span>
      <span><b>Plan chi tiết:</b> <a href="../internal/plan/index.md"><code>internal/plan/index.md</code></a></span>
      <span><b>Lập ngày:</b> 08/10/2026</span>
    </div>
  </header>
  <div class="shell">
    <aside class="toc" aria-label="Mục lục"><nav>
      <div class="lbl">Mục lục</div>
      <a href="#can-biet">1. Bạn cần biết</a>
      <a href="#so-do">2. Sơ đồ khối</a>
      <a href="#thu-tu">3. Thứ tự làm</a>
      <a href="#moi-noi">4. Mối nối</a>
      <a href="#rap">5. Ráp khối</a>
      <a href="#trien-khai">6. Triển khai</a>
      <a href="#cau-hoi">7. Câu hỏi chờ bạn</a>
      <a href="#tung-khoi">8. Từng khối</a>
      ${groups.map(([n, ids]) => `<div class="sub"><a href="#k-${ids[0].toLowerCase()}">${esc(n)}</a></div>`).join('')}
      <a href="#quy-uoc">9. Khi nào khối xong</a>
    </nav></aside>
    <main>
      <section id="can-biet">
        <div class="sec-head"><span class="sec-no">Mục 1</span><h2>Bạn cần biết</h2></div>
        <div class="need"><ol>
          <li><b>Xây từng khối, rồi ráp.</b> Mỗi khối làm xong và test xong một mình, dùng stub thay cho khối bên kia. Sáu lần ráp R1–R6 mới nối các khối thật với nhau và chạy kịch bản đầu–cuối.</li>
          <li><b>Hợp đồng làm trước.</b> Tầng 0 chốt routing, gói FM1, body route agent, snapshot menu, loại lệnh, ngữ pháp helper và bảng nào do khối nào ghi. Có hợp đồng thì hai đầu một mối nối làm song song được.</li>
          <li><b>G0 vẫn là cổng chặn.</b> HPKE của <code>cryptography</code> không liên thông byte-exact, hoặc chưa có số đo trên Pi thật, thì dừng lại hỏi bạn.</li>
          <li><b>Lỗi khi ráp quay về khối.</b> Lỗi tìm thấy lúc ráp được ghi về khối gây lỗi; khối đó thêm test tái hiện rồi sửa. Không vá tại chỗ trong bước ráp.</li>
          <li><b>Mọi khối phía máy đang chờ Q6</b> (nhánh <code>version1.0</code> hay <code>version1.1</code>). Bước đầu tiên chờ Q8 (git init). Các câu khác chỉ chặn đúng khối cần tới.</li>
        </ol></div>
      </section>

      <section id="so-do">
        <div class="sec-head"><span class="sec-no">Mục 2</span><h2>Sơ đồ khối và trạng thái</h2></div>
        <p class="prose">Bố cục theo sơ đồ "râu" ở mục 1 của thiết kế. Mỗi ô ghi trạng thái, số bước đạt trên tổng số, đợt nên làm và câu hỏi đang chờ. Bấm vào ô để tới thẻ của khối.</p>
        <div class="legend" aria-label="Chú giải">
          <span><i class="sym">○</i>chưa làm</span><span><i class="sym run">→</i>đang làm hoặc review</span><span><i class="sym ok">✓</i>đạt</span><span><i class="sym bad">✗</i>chưa đạt</span><span><i class="sym wait">⏸</i>cả khối chờ bạn chốt</span>
          <span><i class="sw srv"></i>khối server</span><span><i class="sw sec"></i>bảo mật</span><span><i class="sw ui"></i>trình duyệt</span><span><i class="sw mac"></i>khối máy</span><span><i class="ln a"></i>qua Bảo mật A</span><span><i class="ln f"></i>qua FM1</span>
        </div>
        <figure class="dg">
          <p class="hint">Sơ đồ rộng: kéo ngang để xem hết.</p>
          <div class="dg-scroll">${svg}</div>
          <figcaption>Đọc từ hai đầu vào giữa. Server: module đi qua Bảo mật A (đường vàng) hoặc FM1 (đường cam) rồi ra S-NET. Máy: A-NET nhận gói qua LAN rồi giao cho bốn module agent; việc cần quyền kiosk đi qua H-LOCAL.</figcaption>
        </figure>
      </section>

      <section id="thu-tu">
        <div class="sec-head"><span class="sec-no">Mục 3</span><h2>Thứ tự làm</h2></div>
        <p class="prose">Thứ tự gợi ý khi chỉ có một coder. Trong cùng một đợt, khối làm theo thứ tự nào cũng được; có nhiều người thì làm song song. Nhãn vàng là câu hỏi khối đó cần.</p>
        <div class="waves">${waves}</div>
      </section>

      <section id="moi-noi">
        <div class="sec-head"><span class="sec-no">Mục 4</span><h2>Mối nối giữa các khối</h2></div>
        <p class="prose">Mỗi mối nối có hợp đồng ở <code>hop_dong.md</code>. Hai khối hai đầu test bằng stub của nhau; cột cuối là lần ráp nối thật.</p>
        <div class="tbl"><table><thead><tr><th>Mối nối</th><th>Hợp đồng</th><th>Ráp</th></tr></thead><tbody>${joints.map(r => `<tr>${r.map(c => `<td>${md(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>
      </section>

      <section id="rap">
        <div class="sec-head"><span class="sec-no">Mục 5</span><h2>Ráp khối</h2></div>
        <p class="prose">Một lần ráp chỉ bắt đầu khi mọi khối trong đó đã đạt. Mỗi lần ráp có kịch bản đầu–cuối và bằng chứng ghi ở <code>internal/plan/bang_chung/</code>.</p>
        <div class="raps">${raps}</div>
      </section>

      <section id="trien-khai">
        <div class="sec-head"><span class="sec-no">Mục 6</span><h2>Triển khai</h2></div>
        <p class="prose">Sau R6: kiểm định theo các mã lỗi ở mục 11 của thiết kế, thử mất điện và tải, rồi chuyển từng máy sang server mẹ và xoá admin_gui khỏi máy.</p>
        <div class="raps">${xs}</div>
      </section>

      <section id="cau-hoi">
        <div class="sec-head"><span class="sec-no">Mục 7</span><h2>Câu hỏi chờ bạn chốt</h2></div>
        <div class="tbl"><table><thead><tr><th>ID</th><th>Câu hỏi</th><th>Chặn</th></tr></thead><tbody>${qs.map(([id, q, c]) => `<tr id="${id.toLowerCase()}"><td class="sid">${esc(id)}</td><td>${md(q)}</td><td>${md(c)}</td></tr>`).join('')}</tbody></table></div>
      </section>

      <section id="tung-khoi">
        <div class="sec-head"><span class="sec-no">Mục 8</span><h2>Từng khối</h2></div>
        <p class="prose">Mỗi thẻ ghi trách nhiệm, khối cung cấp gì, cần gì, stub dùng khi test riêng và các bước kèm phép kiểm. Bước có ⏸ là bước chờ bạn chốt.</p>
        <div class="blks">${cards}</div>
      </section>

      <section id="quy-uoc">
        <div class="sec-head"><span class="sec-no">Mục 9</span><h2>Khi nào một khối được tính là xong</h2></div>
        <div class="need"><ol>
          <li>Mọi bước của khối có phép kiểm và phép kiểm đạt.</li>
          <li>Test riêng của khối chạy bằng stub, không cần khối khác chạy thật: <code>pytest tests/&lt;khối&gt; -q</code> đạt.</li>
          <li>Khối chỉ gọi khối khác qua hợp đồng ở <code>hop_dong.md</code>, không import thẳng vào ruột khối khác.</li>
          <li>Bảng DB khối ghi đúng bảng chủ sở hữu C0.8: mỗi bảng một khối ghi.</li>
          <li>Reviewer đã duyệt; khối có mật mã hoặc phân quyền thì thêm cybersecurity. Chỉ khi đủ năm điều mới đổi ○ thành ✓.</li>
        </ol></div>
      </section>
    </main>
  </div>
</div>
</body>
</html>
`;
fs.writeFileSync(out, html);
console.log('ok', IDS.length, 'khối', nSteps, 'bước', RAPS.length, 'ráp/triển khai', joints.length, 'mối nối', qs.length, 'câu hỏi');

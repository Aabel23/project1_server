// Chạy: node internal/plan/cong_cu/check_trang_plan.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const repo = path.resolve(__dirname, '../../..');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'flexmix-plan-'));
try {
  const output = path.join(temp, 'plan.html');
  execFileSync(process.execPath, [path.join(__dirname, 'dung_trang_plan.js'), output]);
  const html = fs.readFileSync(output, 'utf8');
  assert(!html.includes('chưa có dòng code nào'));
  assert(!html.includes('0/3'));
  assert(html.includes('SQLite tạm'));
  assert(!html.includes('id="q8"'));
  for (const id of ['g0', 'c0', 's-db', 's-net', 'ui-shell']) {
    const card = html.match(new RegExp(`<article class="blk [^"]+" id="k-${id}">([\\s\\S]*?)</article>`));
    assert(card, `Thiếu khối: ${id}`);
    assert.match(card[1], /<span class="pill">→/);
  }
  assert(html.includes('href="../internal/plan/bang_chung/REVIEW_CODEX.md"'));
  for (const [, href] of html.matchAll(/href="([^"]+)"/g)) {
    if (href.startsWith('#') || /^[a-z]+:/i.test(href)) continue;
    assert(fs.existsSync(path.resolve(repo, 'docs', href.split('#')[0])), `Link thiếu: ${href}`);
  }
  assert.equal(html, fs.readFileSync(path.join(repo, 'docs/server_plan.html'), 'utf8'),
    'Trang HTML chưa được dựng lại từ Markdown');
  console.log('Plan: trạng thái, bằng chứng, link và HTML đồng bộ đạt');
} finally {
  fs.rmSync(temp, { recursive: true });
}

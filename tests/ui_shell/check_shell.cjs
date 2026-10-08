// Chạy: node tests/ui_shell/check_shell.cjs. Stub API và DOM, không cần npm.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { randomUUID } = require('node:crypto');
const code = fs.readFileSync(path.join(__dirname, '../../server/static/shell/admin-guard.js'), 'utf8');

function element() {
  return { children: [], attributes: {}, textContent: '',
    append(child) { this.children.push(child); },
    replaceChildren(...children) { this.children = children; },
    setAttribute(key, value) { this.attributes[key] = value; },
    addEventListener(key, handler) { this[key] = handler; },
  };
}

async function check() {
  const calls = [];
  const redirects = [];
  const window = { crypto: { randomUUID }, location: { replace: url => redirects.push(url) },
    fetch: async (url, options) => {
      calls.push({ url, options });
      return { ok: true, status: 200, json: async () => ({ ok: true }) };
    },
  };
  const document = { createElement: element, getElementById: () => null };
  vm.runInNewContext(code, { window, document, AbortController, setTimeout, clearTimeout });
  assert.match(window.newRequestKey(), /^[0-9a-f-]{36}$/);
  const target = element();
  window.setText(target, '<script>alert(1)</script>');
  assert.equal(target.textContent, '<script>alert(1)</script>');
  assert.equal(target.children.length, 0);
  const mount = element();
  const chosen = [];
  const select = window.machinePicker(mount, [{ machine_id: 4, name: '<img onerror=bad>' }], id => chosen.push(id));
  assert.equal(select.children[0].textContent, '<img onerror=bad>');
  assert.equal(select.attributes['aria-label'], 'Chọn máy');
  select.value = '4'; select.change();
  assert.deepEqual(chosen, ['4']);
  assert.equal(window.machinePicker(element(), []).disabled, true);
  await window.api('/api/menu/save', { request_key: 'giữ-key' });
  assert.equal(calls[0].options.credentials, 'same-origin');
  assert.equal(calls[0].options.headers['X-FM-Req'], '1');
  assert.equal(JSON.parse(calls[0].options.body).request_key, 'giữ-key');
  assert.equal(calls[0].options.headers.Authorization, undefined);
  await assert.rejects(window.api('https://other.test/api/a'));

  let finish;
  window.fetch = async (url, options) => {
    calls.push({ url, options });
    if (url === '/api/slow') return new Promise(resolve => { finish = resolve; });
    return { ok: false, status: 401 };
  };
  const slow = window.api('/api/slow');
  const slowRejected = assert.rejects(slow, /hết hạn/);
  await assert.rejects(window.api('/api/expired'), /hết hạn/);
  assert.equal(calls[calls.length - 2].options.signal.aborted, true);
  finish({ ok: true, status: 200, json: async () => ({ stale: true }) });
  await slowRejected;
  assert.deepEqual(redirects, ['login.html']);
  const count = calls.length;
  await assert.rejects(window.api('/api/no-retry'));
  assert.equal(calls.length, count);
  assert.equal(/sessionStorage|innerHTML|Bearer /.test(code), false);
  // whoami trả dữ liệu ngay trước 401: continuation initPage không được vẽ phiên cũ.
  let resolveIdentity, resolveExpired;
  const raceWindow = { crypto: { randomUUID }, location: { replace() {} },
    fetch: url => url === '/api/admin/whoami'
      ? Promise.resolve({ ok: true, status: 200,
        json: () => new Promise(resolve => { resolveIdentity = resolve; }) })
      : new Promise(resolve => { resolveExpired = resolve; }),
  };
  vm.runInNewContext(code, { window: raceWindow, document, AbortController, setTimeout, clearTimeout });
  const init = raceWindow.AdminAuth.initPage('machines');
  const expiredRequest = assert.rejects(raceWindow.api('/api/expired'), /hết hạn/);
  await new Promise(setImmediate);
  resolveIdentity({ ok: true, user: 'phiên cũ', pages: ['machines'] });
  resolveExpired({ status: 401 });
  await expiredRequest;
  assert.equal(await init, false);
  assert.equal(raceWindow.AdminAuth.getSession(), null);
  process.stdout.write('UI-SHELL: đạt cookie, text an toàn, picker và hủy request khi 401\n');
}

check().catch(error => { console.error(error); process.exitCode = 1; });

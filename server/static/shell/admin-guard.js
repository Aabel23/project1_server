/* Khung quản trị: cookie phiên → API, thanh bên và bộ chọn máy.
   Quyền thực tế luôn được server kiểm trên từng request. */
(function (global) {
  'use strict';
  const pending = new Set();
  let expired = false;
  let session = null;
  const NAV = [
    ['machines', 'Máy'], ['menu', 'Quản lý Menu'], ['home', 'Trang chủ'],
    ['recipe-editor', 'Thư viện món'], ['ingredients', 'Nguyên liệu'],
    ['refill', 'Nạp kho'], ['mode', 'Chế độ vận hành'], ['display', 'Màn hình'],
    ['report', 'Báo cáo'], ['tickets', 'Vé QR'], ['errors', 'Nhật ký lỗi'],
    ['bin', 'Thùng rác'], ['users', 'Người dùng'],
  ];

  function setText(element, value) {
    element.textContent = value == null ? '' : String(value);
    return element;
  }

  function newRequestKey() {
    // Gọi một lần khi mở form; giữ nguyên key khi người dùng gửi lại form đó.
    return global.crypto.randomUUID();
  }

  function endSession() {
    if (expired) return;
    expired = true;
    session = null;
    for (const controller of pending) controller.abort();
    pending.clear();
    global.location.replace('login.html');
  }

  async function api(path, body) {
    if (expired) throw new Error('Phiên đã hết hạn.');
    if (typeof path !== 'string' || !path.startsWith('/api/')) {
      throw new Error('API phải là đường dẫn /api/ cùng server.');
    }
    const controller = new AbortController();
    const options = { credentials: 'same-origin', cache: 'no-store', signal: controller.signal };
    if (body !== undefined) {
      options.method = 'POST';
      options.headers = { 'Content-Type': 'application/json', 'X-FM-Req': '1' };
      options.body = JSON.stringify(body);
    }
    pending.add(controller);
    try {
      const response = await global.fetch(path, options);
      if (response.status === 401) {
        endSession();
        throw new Error('Phiên đã hết hạn.');
      }
      const result = response.status === 204 ? null : await response.json();
      // Response cũ không được cập nhật màn hình sau khi request khác nhận 401.
      if (expired) throw new Error('Phiên đã hết hạn.');
      if (!response.ok) {
        const error = new Error((result && result.error) || 'Yêu cầu chưa thành công.');
        error.status = response.status;
        throw error;
      }
      return result;
    } finally {
      pending.delete(controller);
    }
  }

  function showToast(message, kind) {
    let toast = document.querySelector('.toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.setAttribute('role', 'status');
      document.body.append(toast);
    }
    toast.className = 'toast ' + (kind === 'warn' ? 'warn' : '') + ' show';
    setText(toast, message);
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => toast.classList.remove('show'), 2200);
  }

  function machinePicker(mount, machines, onChange) {
    const label = document.createElement('label');
    setText(label, 'Máy ');
    const select = document.createElement('select');
    select.setAttribute('aria-label', 'Chọn máy');
    for (const machine of machines) {
      const option = document.createElement('option');
      option.value = String(machine.machine_id);
      setText(option, machine.name || ('Máy ' + machine.machine_id));
      select.append(option);
    }
    select.disabled = machines.length === 0;
    if (onChange) select.addEventListener('change', () => onChange(select.value));
    label.append(select);
    mount.replaceChildren(label);
    return select;
  }

  function paintShell(active) {
    const mount = document.getElementById('sidebar-mount');
    if (!mount) return;
    const brand = document.createElement('div');
    brand.className = 'brand';
    setText(brand, 'FlexMix · Quản trị');
    const nav = document.createElement('nav');
    nav.className = 'nav';
    nav.setAttribute('aria-label', 'Quản trị');
    const pages = Array.isArray(session.pages) ? session.pages : [];
    for (const [page, title] of NAV) {
      if (!pages.includes(page)) continue;
      const link = document.createElement('a');
      link.href = page + '.html';
      setText(link, title);
      if (page === active) {
        link.className = 'active';
        link.setAttribute('aria-current', 'page');
      }
      nav.append(link);
    }
    const footer = document.createElement('div');
    footer.className = 'side-foot';
    setText(footer, session.display_name || session.user || '');
    mount.replaceChildren(brand, nav, footer);
    const identity = document.getElementById('current-user');
    if (identity) setText(identity, session.display_name || session.user || '');
  }

  async function initPage(active) {
    try {
      const identity = await api('/api/admin/whoami');
      if (expired) return false;
      session = identity;
      if (!session || !session.ok) throw new Error('Không xác định được tài khoản.');
      paintShell(active);
      if (active && (!Array.isArray(session.pages) || !session.pages.includes(active))) {
        showToast('Tài khoản không có quyền mở trang này.', 'warn');
        return false;
      }
      return true;
    } catch (error) {
      if (!expired) showToast(error.message, 'warn');
      return false;
    }
  }

  const shell = { api, newRequestKey, setText, machinePicker, initPage };
  global.AdminShell = shell;
  global.AdminAuth = { initPage, getSession: () => session,
    NAV_ORDER: NAV.map(([page]) => ({ page, href: page + '.html' })) };
  Object.assign(global, { api, newRequestKey, setText, machinePicker, showToast });
})(window);

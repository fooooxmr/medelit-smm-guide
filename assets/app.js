(function () {
  'use strict';

  var $ = function (s, root) { return (root || document).querySelector(s); };
  var $$ = function (s, root) { return Array.prototype.slice.call((root || document).querySelectorAll(s)); };

  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } }
  };

  /* ---------- theme ---------- */
  $('#theme-btn').addEventListener('click', function () {
    var next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    store.set('theme', next);
  });

  /* ---------- mobile menu ---------- */
  var sidebar = $('#sidebar');
  var overlay = $('#overlay');
  var menuBtn = $('#menu-btn');

  function setMenu(open) {
    sidebar.classList.toggle('open', open);
    overlay.hidden = !open;
    menuBtn.setAttribute('aria-expanded', String(open));
    document.body.style.overflow = open ? 'hidden' : '';
  }
  menuBtn.addEventListener('click', function () { setMenu(!sidebar.classList.contains('open')); });
  overlay.addEventListener('click', function () { setMenu(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });
  $$('#toc a, .brand').forEach(function (a) {
    a.addEventListener('click', function () { if (window.innerWidth <= 1000) setMenu(false); });
  });

  /* ---------- scrollspy ---------- */
  var links = $$('#toc a');
  var byId = {};
  links.forEach(function (a) { byId[a.getAttribute('href').slice(1)] = a; });
  var sections = $$('main section[id]').filter(function (s) { return byId[s.id]; });

  function updateActive() {
    var offset = 120;
    var current = sections[0];
    for (var i = 0; i < sections.length; i++) {
      if (sections[i].getBoundingClientRect().top - offset <= 0) current = sections[i];
    }
    if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) current = sections[sections.length - 1];
    links.forEach(function (a) { a.classList.remove('active'); });
    if (current && window.scrollY > 200) {
      var link = byId[current.id];
      link.classList.add('active');
      if (!sidebar.classList.contains('open')) {
        var r = link.getBoundingClientRect();
        var sr = sidebar.getBoundingClientRect();
        if (r.top < sr.top + 60 || r.bottom > sr.bottom - 120) {
          sidebar.scrollTop = link.offsetTop - sidebar.clientHeight / 2;
        }
      }
    }
  }

  /* ---------- progress & to-top ---------- */
  var bar = $('#progress-bar');
  var toTop = $('#to-top');
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (h > 0 ? (window.scrollY / h) * 100 : 0) + '%';
      toTop.hidden = window.scrollY < 600;
      updateActive();
      ticking = false;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  toTop.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
  onScroll();

  /* ---------- checklist ---------- */
  var boxes = $$('.checklist input[type="checkbox"]');
  var KEY = 'medelit-guide-checklist';
  var saved = {};
  try { saved = JSON.parse(store.get(KEY) || '{}'); } catch (e) { saved = {}; }

  function renderChecklist() {
    var done = boxes.filter(function (b) { return b.checked; }).length;
    $('#checklist-total').textContent = done + ' из ' + boxes.length;
    $('#checklist-meter').style.width = (boxes.length ? (done / boxes.length) * 100 : 0) + '%';
  }
  boxes.forEach(function (b) {
    b.checked = !!saved[b.dataset.id];
    b.addEventListener('change', function () {
      saved[b.dataset.id] = b.checked;
      store.set(KEY, JSON.stringify(saved));
      renderChecklist();
    });
  });
  renderChecklist();

  /* ---------- copy templates ---------- */
  var toast = $('#toast');
  var toastTimer;
  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.classList.remove('show'); }, 1800);
  }
  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }
  $$('.copy-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var el = document.getElementById(btn.dataset.copy);
      var text = el.innerText.trim();
      var done = function () { showToast('Скопировано'); };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done, function () { if (fallbackCopy(text)) done(); });
      } else if (fallbackCopy(text)) {
        done();
      }
    });
  });

  /* ---------- Q&A ---------- */
  var qas = $$('details.qa');
  $('#qa-open').addEventListener('click', function () { qas.forEach(function (d) { d.open = true; }); });
  $('#qa-close').addEventListener('click', function () { qas.forEach(function (d) { d.open = false; }); });

  /* ---------- print ---------- */
  var openedForPrint = [];
  $('#print-btn').addEventListener('click', function () { window.print(); });
  window.addEventListener('beforeprint', function () {
    openedForPrint = qas.filter(function (d) { return !d.open; });
    openedForPrint.forEach(function (d) { d.open = true; });
  });
  window.addEventListener('afterprint', function () {
    openedForPrint.forEach(function (d) { d.open = false; });
    openedForPrint = [];
  });

  /* ---------- search ---------- */
  var input = $('#search');
  var results = $('#search-results');
  function textOf(root) {
    var parts = [];
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    while (w.nextNode()) parts.push(w.currentNode.nodeValue);
    return parts.join(' ').replace(/\s+/g, ' ').replace(/\s+([.,;:!?»)])/g, '$1').trim();
  }
  var index = $$('main section[id]').map(function (s) {
    var h = s.querySelector('h1, h2');
    return { el: s, title: h ? h.textContent.trim() : '', text: textOf(s) };
  });

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function clearMarks() {
    $$('mark[data-search]').forEach(function (m) {
      var parent = m.parentNode;
      parent.replaceChild(document.createTextNode(m.textContent), m);
      parent.normalize();
    });
  }

  function markIn(root, query) {
    var q = query.toLowerCase();
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        if (!n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        var p = n.parentNode;
        if (p && (p.closest('button') || p.closest('script') || p.closest('summary'))) return NodeFilter.FILTER_REJECT;
        return n.nodeValue.toLowerCase().indexOf(q) !== -1 ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    var first = null;
    nodes.forEach(function (node) {
      var text = node.nodeValue;
      var lower = text.toLowerCase();
      var frag = document.createDocumentFragment();
      var pos = 0, i;
      while ((i = lower.indexOf(q, pos)) !== -1) {
        frag.appendChild(document.createTextNode(text.slice(pos, i)));
        var m = document.createElement('mark');
        m.dataset.search = '1';
        m.textContent = text.slice(i, i + q.length);
        frag.appendChild(m);
        if (!first) first = m;
        pos = i + q.length;
      }
      frag.appendChild(document.createTextNode(text.slice(pos)));
      node.parentNode.replaceChild(frag, node);
    });
    return first;
  }

  function openDetailsAround(el) {
    var d = el && el.closest('details');
    if (d) d.open = true;
  }

  function search(query) {
    var q = query.trim();
    if (q.length < 2) { results.hidden = true; results.innerHTML = ''; return; }
    var ql = q.toLowerCase();
    var hits = index.filter(function (it) { return it.text.toLowerCase().indexOf(ql) !== -1; });
    if (!hits.length) {
      results.innerHTML = '<div class="empty">Ничего не нашлось</div>';
      results.hidden = false;
      return;
    }
    results.innerHTML = hits.map(function (it, n) {
      var i = it.text.toLowerCase().indexOf(ql);
      var start = Math.max(0, i - 40);
      var snippet = (start > 0 ? '…' : '') + it.text.slice(start, i + q.length + 60) + '…';
      var safe = escapeHtml(snippet).replace(new RegExp(escapeHtml(q).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'), function (m) { return '<mark>' + m + '</mark>'; });
      return '<button type="button" data-hit="' + n + '"><b>' + escapeHtml(it.title) + '</b>' + safe + '</button>';
    }).join('');
    results.hidden = false;
    $$('button', results).forEach(function (btn) {
      btn.addEventListener('click', function () {
        var it = hits[Number(btn.dataset.hit)];
        clearMarks();
        var first = markIn(it.el, q);
        openDetailsAround(first);
        if (window.innerWidth <= 1000) setMenu(false);
        (first || it.el).scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
    });
  }

  var searchTimer;
  input.addEventListener('input', function () {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function () {
      if (!input.value.trim()) clearMarks();
      search(input.value);
    }, 120);
  });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      var firstBtn = $('button', results);
      if (firstBtn) firstBtn.click();
    }
    if (e.key === 'Escape') { input.value = ''; clearMarks(); search(''); }
  });
  document.addEventListener('keydown', function (e) {
    if ((e.key === '/' || (e.key.toLowerCase() === 'k' && (e.metaKey || e.ctrlKey))) && document.activeElement !== input) {
      e.preventDefault();
      if (window.innerWidth <= 1000) setMenu(true);
      input.focus();
    }
  });
})();

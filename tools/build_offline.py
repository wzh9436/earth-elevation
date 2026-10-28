#!/usr/bin/env python3
"""从网页版生成单文件离线版：index.html → earth-offline-zh.html，en.html → earth-offline-en.html。

把 <script src="lib/..."> 内联，把 ASSETS 里的数据文件路径替换为 base64 内嵌数据，
并删除只适用于网页版的 <!--WEB-ONLY--> 段落。修改 index.html / lib / data 后重新运行：

    python3 tools/build_offline.py
"""
import base64, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIME = {'.jpg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}


def read(path, mode='r'):
    with open(os.path.join(ROOT, path), mode, **({} if 'b' in mode else {'encoding': 'utf-8'})) as f:
        return f.read()


def build(src_name, out_name):
    html = read(src_name)

    # 1. 外部脚本内联（"</script" 转义，防止提前结束标签）
    def inline_script(m):
        code = read(m.group(1)).replace('</script', '<\\/script')
        return '<script>' + code + '</script>'
    html, n = re.subn(r'<script src="(lib/[^"]+)"></script>', inline_script, html)
    assert n == 2, f'expected 2 lib scripts, got {n}'

    # 2. 数据文件内嵌
    m = re.search(r'const ASSETS = \{(.*?)\};', html, re.S)
    assert m, 'ASSETS block not found'
    entries = []
    for key, path in re.findall(r"(\w+):\s*'([^']+)'", m.group(1)):
        if path.endswith('.json'):
            value = json.dumps(json.loads(read(path)), separators=(',', ':'), ensure_ascii=False)
        else:
            b64 = base64.b64encode(read(path, 'rb')).decode()
            value = "'data:%s;base64,%s'" % (MIME[os.path.splitext(path)[1]], b64)
        entries.append('  %s: %s' % (key, value))
    html = html[:m.start()] + 'const ASSETS = {\n' + ',\n'.join(entries) + '\n};' + html[m.end():]

    # 3. 删除网页版专用段落（如"下载离线版"按钮）
    html, n = re.subn(r'[ \t]*<!--WEB-ONLY-->.*?<!--/WEB-ONLY-->\r?\n', '', html, flags=re.S)
    for a, b in LOADING_TEXT:
        html = html.replace(a, b)

    out = os.path.join(ROOT, out_name)
    with open(out, 'w', encoding='utf-8', newline='') as f:
        f.write(html)
    print('wrote %s (%.1f MB)' % (out, os.path.getsize(out) / 1e6))


LOADING_TEXT = [('正在加载程序与离线数据（约 8 MB）', '正在装入内嵌离线数据'),
                ('Loading app and offline data (~8 MB)', 'Loading embedded offline data')]

for src_name, out_name in [('index.html', 'earth-offline-zh.html'), ('en.html', 'earth-offline-en.html')]:
    if os.path.exists(os.path.join(ROOT, src_name)):
        build(src_name, out_name)

# ── 回访缓存：生成 sw.js（Service Worker），网页版第二次打开直接用本地缓存 ──
SW_TEMPLATE = r"""/* 自动生成（tools/build_offline.py），请勿手工修改。
   策略：lib/、data/ 里的大文件缓存优先（文件内容变化时 VER 变化，旧缓存自动清除）；
   网页本身网络优先（3 秒内取不到就用缓存），所以更新能及时到达，断网时也能打开。 */
const VER = '__VER__';
const CACHE = 'earth-' + VER;
const ASSETS = __ASSETS__;
const PAGES = ['./', 'index.html', 'zh.html', 'en.html'];
const abs = p => new URL(p, self.registration.scope).href;

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    // 多数文件已在浏览器的 HTTP 缓存里，这里通常不会重复下载
    await Promise.all([...ASSETS, ...PAGES].map(p => c.add(abs(p)).catch(() => {})));
    await self.skipWaiting();
  })());
});
self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k.startsWith('earth-') && k !== CACHE) await caches.delete(k);
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin || !url.href.startsWith(self.registration.scope)) return;
  if (req.mode === 'navigate') { e.respondWith(networkFirst(req)); return; }
  const rel = url.href.slice(self.registration.scope.length);
  if (ASSETS.includes(rel)) e.respondWith(cacheFirst(req));
});
async function cacheFirst(req) {
  const c = await caches.open(CACHE), hit = await c.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok && res.status === 200) c.put(req, res.clone());
  return res;
}
async function networkFirst(req) {
  const c = await caches.open(CACHE);
  try {
    const res = await Promise.race([fetch(req), new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), 3000))]);
    if (res.ok) c.put(req, res.clone());
    return res;
  } catch (err) {
    return (await c.match(req, { ignoreSearch: true })) || (await c.match(abs('index.html'))) || Response.error();
  }
}
"""


def build_sw():
    import hashlib
    files = sorted(os.path.join(d, f).replace(os.sep, '/') for d in ('lib', 'data') for f in os.listdir(os.path.join(ROOT, d)))
    h = hashlib.sha1()
    for f in files:
        h.update(f.encode()); h.update(read(f, 'rb'))
    js = SW_TEMPLATE.replace('__VER__', h.hexdigest()[:10]).replace('__ASSETS__', json.dumps(files))
    with open(os.path.join(ROOT, 'sw.js'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(js)
    print('wrote sw.js (cache version %s, %d files)' % (h.hexdigest()[:10], len(files)))


build_sw()

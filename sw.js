/* 自动生成（tools/build_offline.py），请勿手工修改。
   策略：lib/、data/ 里的大文件缓存优先（文件内容变化时 VER 变化，旧缓存自动清除）；
   网页本身网络优先（3 秒内取不到就用缓存），所以更新能及时到达，断网时也能打开。 */
const VER = '778690625a';
const CACHE = 'earth-' + VER;
const ASSETS = ["data/countries.json", "data/ext.webp", "data/land.jpg", "data/mask.png", "data/sea.jpg", "lib/OrbitControls.js", "lib/three.min.js"];
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

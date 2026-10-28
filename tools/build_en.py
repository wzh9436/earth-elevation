#!/usr/bin/env python3
"""从中文网页版 index.html 生成英文网页版 en.html。

做法：按下面的对照表做精确替换（每条都必须在源文件中找到，否则构建失败），
再替换国家或地区中文名表、地标表、快捷地点和搜索别名；
最后检查生成结果中除注释与少数白名单外不再含有中文，防止漏译。

修改 index.html 的界面文字后，请同步更新下方对照表，然后运行：

    python3 tools/build_en.py        # 生成 en.html
    python3 tools/build_offline.py   # 生成中英文两个单文件离线版
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 界面文字对照表：(中文原文, 英文)，原文必须与 index.html 中完全一致 ──
PAIRS = [
    ('<html lang="zh-CN">', '<html lang="en">'),
    ('<title>全球海拔与海深离线查询系统 · SRTM / GEBCO</title>', '<title>Global Elevation &amp; Ocean Depth Explorer · Offline</title>'),
    ("'错误：文件加载失败 '", "'Error: failed to load '"),
    ("'（请刷新；仍失败请截图反馈）'", "' (please refresh; if it keeps failing, send a screenshot)'"),
    ("'错误：'+(e.message||'脚本错误')+'（请截图反馈）'", "'Error: '+(e.message||'script error')+' (please send a screenshot)'"),
    ("'错误：程序未能启动，网页文件可能不完整（当前约 '+mb+' MB），请刷新后重试'",
     "'Error: the app did not start; the page may be incomplete (about '+mb+' MB received). Please refresh.'"),
    ('<h1>全球<em>海拔</em>与<em>海深</em>离线查询系统</h1>', '<h1>Global <em>Elevation</em> &amp; <em>Ocean Depth</em> Explorer</h1>'),
    ('<div class="en">Global Elevation &amp; Bathymetry Offline Query System</div>', '<div class="en">Offline 3D globe · land elevation and ocean depth worldwide</div>'),
    ('<a class="lang" href="en.html" hreflang="en">English</a>', '<a class="lang" href="zh.html" hreflang="zh-CN">中文</a>'),
    ('定位控制台 · NAVIGATE', 'NAVIGATE'),
    ('title="收起控制台"', 'title="Hide panel"'),
    ('placeholder="🔍 搜索国家或地区、地标"', 'placeholder="🔍 Search countries, regions, landmarks"'),
    ('aria-label="搜索国家或地区、地标"', 'aria-label="Search countries, regions, landmarks"'),
    ('<label>纬度 LAT<small>单位：度 ° · 北正南负</small></label>', '<label>Latitude<small>Degrees ° · north +, south −</small></label>'),
    ('<label>经度 LON<small>单位：度 ° · 东正西负</small></label>', '<label>Longitude<small>Degrees ° · east +, west −</small></label>'),
    ('⌖ 跳转到该坐标', '⌖ Go to coordinates'),
    ('>复位视角<', '>Reset view<'),
    ('坐标微调 · NUDGE（每次 0.01°）', 'NUDGE (0.01° per step)'),
    ('title="向西"', 'title="West"'), ('title="向北"', 'title="North"'),
    ('title="向南"', 'title="South"'), ('title="向东"', 'title="East"'),
    ('图层叠加 · LAYERS', 'LAYERS'),
    ('class="tg">国界线<input', 'class="tg">Borders<input'),
    ('class="tg">国家或地区标注<input', 'class="tg">Country &amp; region labels<input'),
    ('class="tg">陆地地形分层设色<input', 'class="tg">Land elevation colors<input'),
    ('class="tg">海洋深度渐变蓝色<input', 'class="tg">Ocean depth shading<input'),
    ('class="tg">大气辉光<input', 'class="tg">Atmosphere glow<input'),
    ('手机竖握时横屏显示<input', 'Landscape layout when held upright<input'),
    ('地形立体夸张度 <span', 'Terrain exaggeration <span'),
    ('href="earth-offline-zh.html" download="全球海拔与海深离线查询系统.html">⬇ 下载单文件离线版（约 10.6 MB）',
     'href="earth-offline-en.html" download="Global-Elevation-Explorer-offline.html">⬇ Download offline version (~10.6 MB)'),
    ('" target="_blank" rel="noopener">备用：从 GitHub 下载',
     '" target="_blank" rel="noopener">Alternative: download from GitHub'),
    ('📦 离线数据 · OFFLINE DATA', '📦 OFFLINE DATA'),
    ('移动鼠标探测地表', 'Move the mouse over the globe'),
    ('海拔 / 海深<b', 'Elevation / depth<b'),
    ('海拔海深标尺 · LEGEND', 'ELEVATION LEGEND'),
    ('海平面 0 m', 'Sea level 0 m'),
    ('+8848 珠峰', '+8848 Everest'),
    ('操作说明 · HELP', 'HELP'),
    ('🖱 拖拽旋转 · 滚轮缩放 · 悬停探测海拔/海深与国家或地区', '🖱 Drag to rotate · scroll to zoom · hover to read elevation / depth and country or region'),
    ('📍 双击选点 · <b>方向键</b>微调选点 0.01° · <b>Esc</b> 清除选点', '📍 Double-click to pick a point · <b>Arrow keys</b> nudge 0.01° · <b>Esc</b> clear'),
    ('数据来源：AWS Terrain Tiles · GEBCO · Natural Earth · 完全离线 · © wzh · <a href="#" class="licOpen">数据与许可</a>',
     'Data: AWS Terrain Tiles · GEBCO · Natural Earth · fully offline · © wzh · <a href="#" class="licOpen">Data &amp; License</a>'),
    ('© 2026 wzh · CC BY-NC 4.0 · <a href="#" class="licOpen">数据与许可</a><br>商用请联系作者 · github.com',
     '© 2026 wzh · CC BY-NC 4.0 · <a href="#" class="licOpen">Data &amp; License</a><br>Commercial use: please contact the author · github.com'),
    ('title="打开控制台"', 'title="Open panel"'),
    ('📱 请横握手机，体验与电脑端一致', '📱 Turn your phone sideways for the full layout'),
    ('正在加载程序与离线数据（约 8 MB），网速较慢时需要稍等…', 'Loading app and offline data (~8 MB). This may take a moment on slow connections…'),
    ("'单击查看海拔，双击选点'", "'Tap to read elevation, double-tap to pick'"),
    ("label:'地形海拔 0 ~ 8850 m'", "label:'Land elevation 0 ~ 8850 m'"),
    ("label:'海洋深度 0 ~ -11000 m'", "label:'Ocean depth 0 ~ -11000 m'"),
    ("label:'高精度海陆掩膜'", "label:'High-resolution land/sea mask'"),
    ("label:'Natural Earth 国家或地区边界', sub:'10m 精细版'", "label:'Natural Earth boundaries', sub:'1:10m detail'"),
    ("label:'极值网格：所在网格最高 / 最深', sub:'约 20 km 一格，源数据约 600 m'", "label:'Cell extremes: highest / deepest', sub:'~20 km cells, from ~600 m source data'"),
    ("label:'经典位置参考值', sub:'34 处高峰、海沟、洼地'", "label:'Landmark reference values', sub:'34 peaks, trenches and depressions'"),
    ("label:'three.js 三维引擎', sub:'本地加载，无需联网'", "label:'three.js 3D engine', sub:'Loaded locally, no internet needed'"),
    ("{ loading:'… 加载中', ok:'✓ 已加载', fail:'✗ 失败' }", "{ loading:'… loading', ok:'✓ loaded', fail:'✗ failed' }"),
    ("'数据文件加载失败：'+(src.startsWith('data:')?'内嵌数据':src)", "'Failed to load data file: '+(src.startsWith('data:')?'embedded data':src)"),
    ("'数据文件加载失败：'+src+'（HTTP '+r.status+'）'", "'Failed to load data file: '+src+' (HTTP '+r.status+')'"),
    ("'数据文件不完整：'+src+'（下载被中断，请刷新）'", "'Data file incomplete: '+src+' (download interrupted, please refresh)'"),
    ("'地形数据尺寸不符（应为 '+2*W+'×'+2*H+'）'", "'Unexpected terrain data size (expected '+2*W+'×'+2*H+')'"),
    ("'正在加载地形数据…'", "'Loading terrain data…'"),
    ("'正在上传贴图到显卡…'", "'Uploading textures to the GPU…'"),
    ("'正在建立查询网格…'", "'Building the query grid…'"),
    ("'正在加载国界…'", "'Loading boundaries…'"),
    ("'正在加载极值网格…'", "'Loading the extremes grid…'"),
    ("`正在下载地形数据 ${(g/1e6).toFixed(1)} / ${(t/1e6).toFixed(1)} MB`", "`Downloading terrain data ${(g/1e6).toFixed(1)} / ${(t/1e6).toFixed(1)} MB`"),
    ("'国家或地区数据加载中…'", "'Loading country / region data…'"),
    ("'查询网格建立中，稍后可查询'", "'The query grid is being built…'"),
    ("console.warn('国界解析失败：',e)", "console.warn('Boundary parsing failed:',e)"),
    ("'就绪 · 完全离线 · 拖动旋转 / 双指缩放 / 单击查看 / 双击选点'", "'Ready · fully offline · drag to rotate / pinch to zoom / tap to read / double-tap to pick'"),
    ("'就绪 · 完全离线 · 拖拽旋转 / 滚轮缩放 / 悬停探测'", "'Ready · fully offline · drag to rotate / scroll to zoom / hover to read'"),
    ("t.textContent = '错误：'+msg;", "t.textContent = 'Error: '+msg;"),
    ("'约 +'+v+' m' : '约 '+v+' m（低于海平面）'", "'≈ +'+v+' m' : '≈ '+v+' m (below sea level)'"),
    ("'约 '+v+' m（海深）' : '约 0 m（近岸浅海）'", "'≈ '+v+' m (depth)' : '≈ 0 m (shallow coastal water)'"),
    ("`📍 ${pl.n}（参考值）`+(el?` · 格网估算 ${fmtM(el.v)}`:'')", "`📍 ${pl.n} (reference)`+(el?` · gridded estimate ${fmtM(el.v)}`:'')"),
    ("`格网估算（约 ${GRID_KM} km）`", "`Gridded estimate (~${GRID_KM} km)`"),
    ("` · 所在网格（约 ${EXT.km} km）${el.isSea?'最深':'最高'} ${fmtM(ex)}`", "` · cell (~${EXT.km} km) ${el.isSea?'deepest':'highest'} ${fmtM(ex)}`"),
    ("'未识别国家或地区' : '海洋'", "'Unidentified country or region' : 'Ocean'"),
    ("'纬度格式不对：应在 -90~90 度之间，如 30.57、30°34′12″N；正负号与 N/S 不能同时用'",
     "'Invalid latitude: use -90 to 90, e.g. 30.57 or 30°34′12″N; do not combine a sign with N/S'"),
    ("'经度格式不对：应在 -180~180 度之间，如 104.07、104°4′12″E；正负号与 E/W 不能同时用'",
     "'Invalid longitude: use -180 to 180, e.g. 104.07 or 104°4′12″E; do not combine a sign with E/W'"),
    ("`已定位 ${r.zh}，红点为其中心位置`", "`Showing ${r.zh}. The red dot marks its center.`"),
    ("${r.type==='region'?'国家或地区':'地标'}", "${r.type==='region'?'Country / region':'Landmark'}"),
    ("'未找到「'+q.replace(/[<>&\"]/g,'')+'」，目前只收录国家或地区及内置地标'",
     "'No match for “'+q.replace(/[<>&\"]/g,'')+'”. Only countries, regions and built-in landmarks are included.'"),
    ("fail('显卡内存不足，3D 画面已中断，请关闭其他标签页后刷新')", "fail('Graphics memory ran out and the 3D view stopped. Close other tabs and refresh.')"),
]
# 出现多次、需全部替换的短语
ALL = [
    ('/^错误/', '/^Error/'),
    ("'停止旋转'", "'Stop rotation'"), ('>停止旋转<', '>Stop rotation<'),
    ("'自动旋转'", "'Auto-rotate'"),
    ('也支持度分秒，如 30°34′12″N', 'DMS also accepted, e.g. 30°34′12″N'),
    ("'国家或地区数据不可用'", "'Country / region data unavailable'"),
]

# ── 地标英文名与说明（与 index.html 的 PLACES 一一对应） ──
PLACE_EN = {
    '珠穆朗玛峰': ('Mount Everest', '2020 China–Nepal survey'), '乔戈里峰 K2': ('K2', ''),
    '干城章嘉峰': ('Kangchenjunga', ''), '洛子峰': ('Lhotse', ''), '马卡鲁峰': ('Makalu', ''),
    '卓奥友峰': ('Cho Oyu', ''), '道拉吉里峰': ('Dhaulagiri', ''), '马纳斯卢峰': ('Manaslu', ''),
    '南迦帕尔巴特峰': ('Nanga Parbat', ''), '安纳布尔纳峰': ('Annapurna I', ''),
    '加舒尔布鲁木 I 峰': ('Gasherbrum I', ''), '布洛阿特峰': ('Broad Peak', ''),
    '加舒尔布鲁木 II 峰': ('Gasherbrum II', ''), '希夏邦马峰': ('Shishapangma', ''),
    '公格尔峰': ('Kongur Tagh', ''), '贡嘎山': ('Minya Konka', ''), '慕士塔格峰': ('Muztagh Ata', ''),
    '阿空加瓜山': ('Aconcagua', 'Highest in South America'), '德纳里峰': ('Denali', 'Highest in North America'),
    '乞力马扎罗山': ('Kilimanjaro', 'Highest in Africa'), '厄尔布鲁士山': ('Mount Elbrus', 'Highest in Europe'),
    '文森山': ('Vinson Massif', 'Highest in Antarctica'), '查亚峰': ('Puncak Jaya', 'Highest in Oceania'),
    '勃朗峰': ('Mont Blanc', ''), '马特洪峰': ('Matterhorn', ''),
    '冒纳凯阿火山': ('Mauna Kea', 'Over 10,000 m from its base on the seafloor'),
    '玉山': ('Yushan', 'Highest in Taiwan'), '富士山': ('Mount Fuji', ''),
    '科修斯科山': ('Mount Kosciuszko', 'Highest on mainland Australia'), '泰山 玉皇顶': ('Mount Tai', 'Jade Emperor Peak'),
    '死海': ('Dead Sea', 'Lake surface, falling every year'), '艾丁湖': ('Ayding Lake', 'Lowest point in China'),
    '挑战者深渊': ('Challenger Deep', 'Mariana Trench, deepest point on Earth'), '地平线深渊': ('Horizon Deep', 'Tonga Trench'),
}
SPOTS_EN = """const spots=[   // 3 per row: peaks / oceans / landforms / other
  ['Everest',27.9881,86.9250],['K2',35.8825,76.5133],['Kilimanjaro',-3.0758,37.3533],
  ['Mariana Trench',11.3733,142.5917],['Tonga Trench',-23.2617,-174.7267],['Dead Sea',31.5,35.5],
  ['Grand Canyon',36.06,-112.14],['Rift Valley',-0.77,36.40],['Tibet Plateau',33.0,88.0],
  ['Amazon Basin',-3.47,-62.21],['Iceland',64.96,-19.02],['Barrier Reef',-18.29,147.70]];"""
ALIAS_EN = """const ALIAS={   // common short names and alternative names
    'Mount Everest':['Qomolangma','Chomolungma','Sagarmatha'],'Kilimanjaro':['Mount Kilimanjaro'],
    'Denali':['Mount McKinley','McKinley'],'Minya Konka':['Gongga','Gongga Shan'],'Mount Tai':['Taishan','Jade Emperor Peak'],
    'Yushan':['Jade Mountain'],'Puncak Jaya':['Carstensz'],'Mount Elbrus':['Elbrus'],'Mount Fuji':['Fuji','Fujisan'],
    'Challenger Deep':['Mariana'],'Horizon Deep':['Tonga'],
    'Grand Canyon':['Colorado'],'Rift Valley':['Great Rift Valley','East African Rift'],'Tibet Plateau':['Tibetan Plateau','Qinghai-Tibet'],
    'Amazon Basin':['Amazon'],'Barrier Reef':['Great Barrier Reef'],
    'United States of America':['USA','US','America','United States'],'United Kingdom':['UK','Britain','England'],
    'China':['PRC'],'South Korea':['Korea'],'North Korea':['DPRK'],'United Arab Emirates':['UAE'],
    'Dem. Rep. Congo':['DR Congo','DRC','Democratic Republic of the Congo'],'Congo':['Republic of the Congo'],
    'Czechia':['Czech Republic'],'Bosnia and Herz.':['Bosnia and Herzegovina'],'Central African Rep.':['Central African Republic'],
    'Dominican Rep.':['Dominican Republic'],'Eq. Guinea':['Equatorial Guinea'],'S. Sudan':['South Sudan'],
    'Solomon Is.':['Solomon Islands'],'eSwatini':['Eswatini','Swaziland'],'Macedonia':['North Macedonia'],
    "Côte d'Ivoire":['Ivory Coast','Cote dIvoire'],
  };"""
# 中文仅允许留在：坐标解析（兼容中文方位/度分秒输入）与语言切换链接
WHITELIST = [r"HEMI_RE='[^']*'", r"\(\?:°\|度\)", r"\(\?:′\|\\x27\|分\)", r"\(\?:″\|\"\|\\x27\\x27\|秒\)",
             r"'NS北南'", r"'S南W西'", r'>中文</a>']


LIC_EN = """<!--LIC-->
<div id="licBox" role="dialog" aria-modal="true" aria-label="Data and license">
  <div class="lic-card">
    <div class="lic-h"><span>DATA &amp; LICENSE</span><button id="licClose" aria-label="Close">✕</button></div>
    <div class="lic-b" id="licBody">
      <h3>THIS PROJECT</h3>
      <p>Interface, program and integration © 2026 wzh, licensed under <a href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank" rel="noopener">CC BY-NC 4.0</a> (Attribution-NonCommercial): free to use, share and adapt with attribution and an indication of changes; commercial use is not permitted. <b>For commercial use, please contact the author</b> (GitHub: <a href="https://github.com/wzh9436" target="_blank" rel="noopener">@wzh9436</a>).</p>
      <p>The third-party data and libraries below keep their own licenses; the non-commercial restriction applies only to the original parts of this project.</p>
      <h3>THIRD-PARTY DATA</h3>
      <p><b>Terrain and ocean depth (display)</b>: AWS Terrain Tiles (Terrarium format, zoom 5): land from GMTED2010, ocean from ETOPO1; polar edges beyond 84° latitude reuse the project's original material.<br>
      <span class="en">GMTED2010 data courtesy of the U.S. Geological Survey. ETOPO1: DOC/NOAA/NESDIS/NCEI. Terrain Tiles: Tilezen / Mapzen, hosted on AWS Open Data.</span></p>
      <p><b>Extremes grid</b> (cell highest / deepest): also Terrain Tiles (zoom 8): land from SRTM, GMTED2010 north of 60°N, NRCan CDEM for Canada, ocean from ETOPO1.<br>
      <span class="en">SRTM data courtesy of the U.S. Geological Survey. Canada: contains information licensed under the Open Government Licence – Canada. Attribution list: <a href="https://github.com/tilezen/joerd/blob/master/docs/attribution.md" target="_blank" rel="noopener">tilezen/joerd</a>.</span></p>
      <p><b>Land/sea mask</b>: land/sea boundary data based on GEBCO (the project's original material).<br>
      <span class="en">GEBCO Grid: GEBCO Compilation Group. Not for navigation.</span></p>
      <p><b>Boundaries</b>: <a href="https://www.naturalearthdata.com/" target="_blank" rel="noopener">Natural Earth</a> (public domain), prepared via world-atlas and simplified with topojson-simplify.</p>
      <p><b>Landmark reference values</b>: from public sources, e.g. Mount Everest 8848.86 m (2020 China–Nepal survey).</p>
      <p><b>3D engine</b>: three.js (MIT license, © 2010-2023 three.js authors); the copyright notice is kept in the file.</p>
      <h3>NOTES</h3>
      <p>Elevation and depth are estimates from a ~10 km grid, and "cell highest / deepest" is a statistic over a ~20 km cell. For reference only: not for navigation, safety at sea, engineering or surveying.</p>
      <p>Country and region names and boundaries come from Natural Earth and are for geographic reference only; they do not express any position.</p>
      <p>This page runs fully offline and sends no data to any server.</p>
    </div>
  </div>
</div>
<!--/LIC-->"""


def main():
    src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8', newline='').read()
    crlf = '\r\n' in src
    s = src.replace('\r\n', '\n')
    missing = []
    for zh, en in PAIRS:
        n = s.count(zh)
        if n != 1:
            missing.append(f'{n}× {zh[:70]}')
        s = s.replace(zh, en)
    for zh, en in ALL:
        if zh not in s:
            missing.append(f'0× {zh[:70]}')
        s = s.replace(zh, en)
    # 国家或地区：直接用 Natural Earth 英文名
    s, nl = re.subn(r'<!--LIC-->.*?<!--/LIC-->', lambda _: LIC_EN, s, count=1, flags=re.S)
    if nl != 1:
        missing.append('数据与许可页（<!--LIC--> 段落）替换失败')
    s, n1 = re.subn(r'const ZH = \{.*?\};', 'const ZH = {};', s, count=1, flags=re.S)
    # 地标
    m = re.search(r'const PLACES = (\[.*?\]);', s, re.S)
    places = json.loads(m.group(1)) if m else []
    for p in places:
        if p['n'] not in PLACE_EN:
            missing.append('地标未翻译：' + p['n'])
            continue
        p['n'], p['note'] = PLACE_EN[p['n']]
    if m:
        s = s[:m.start(1)] + json.dumps(places, ensure_ascii=False) + s[m.end(1):]
    s, n2 = re.subn(r'const spots=\[.*?\]\];', lambda _: SPOTS_EN, s, count=1, flags=re.S)
    s, n3 = re.subn(r'const ALIAS=\{.*?\n  \};', lambda _: ALIAS_EN, s, count=1, flags=re.S)
    if not (n1 and m and n2 and n3):
        missing.append('数据表替换失败（ZH / PLACES / spots / ALIAS）')
    if missing:
        sys.exit('英文版构建失败，以下原文在 index.html 中找不到或数量不对（请更新 tools/build_en.py）：\n  ' + '\n  '.join(missing))

    # 防漏译：去掉注释与白名单后不应再有中文
    chk = re.sub(r'/\*.*?\*/|<!--.*?-->', '', s, flags=re.S)
    chk = re.sub(r'(?m)(?<![:\'"])//[^\n]*$', '', chk)
    for w in WHITELIST:
        chk = re.sub(w, '', chk)
    left = sorted({ln.strip()[:100] for ln in chk.split('\n') if re.search(r'[一-鿿　-〿＀-￯]', ln)})
    if left:
        sys.exit('英文版仍含中文（请补充对照表）：\n  ' + '\n  '.join(left))

    # 中文网页版的 zh.html：与 index.html 内容相同（index.html 是网站默认入口），文件名与 en.html 对应
    with open(os.path.join(ROOT, 'zh.html'), 'w', encoding='utf-8', newline='') as f:
        f.write(src)
    out = os.path.join(ROOT, 'en.html')
    with open(out, 'w', encoding='utf-8', newline='') as f:
        f.write(s.replace('\n', '\r\n') if crlf else s)
    print('wrote %s (%.1f KB)' % (out, os.path.getsize(out) / 1e3))


if __name__ == '__main__':
    main()

# 全球海拔与海深离线查询系统

- **总描述**：在三维地球上点一下，就能查询任意位置的海拔或海深。数据全部内置在页面里，断网也能用；支持国家或地区、地标搜索，另外会给出该位置所在网格内的最高点或最深点。
- **中文**：[在线使用](https://wzh9436.github.io/earth-elevation/) · [下载离线版（约 10.6 MB，双击即用）](https://github.com/wzh9436/earth-elevation/raw/main/earth-offline-zh.html)
- **English**: [Open online](https://wzh9436.github.io/earth-elevation/en.html) · [Download offline version (~10.6 MB, double-click to use)](https://github.com/wzh9436/earth-elevation/raw/main/earth-offline-en.html)

## 文件结构

| 路径 | 说明 |
|---|---|
| `index.html` / `zh.html` | 中文网页版（界面与程序），数据从下面的文件加载；`index.html` 是网站默认入口，`zh.html` 是同内容的副本（由 `tools/build_en.py` 生成） |
| `sw.js` | 回访缓存（Service Worker）：第二次打开直接读本地缓存，断网也能打开已访问过的页面；由 `tools/build_offline.py` 生成 |
| `en.html` | 英文网页版，由 `tools/build_en.py` 从 `index.html` 生成 |
| `lib/three.min.js`、`lib/OrbitControls.js` | three.js 三维引擎 |
| `data/land.jpg`、`data/sea.jpg` | 陆地海拔 / 海洋深度贴图（sqrt 编码，约 5 km 网格） |
| `data/mask.png` | 海陆掩膜 |
| `data/ext.webp` | 极值网格：每格（约 20 km）最高点 / 最深点，16 位无损 |
| `data/countries.json` | Natural Earth 10m 国界（TopoJSON） |
| `earth-offline-zh.html` / `earth-offline-en.html` | 由构建脚本生成的中文 / 英文单文件离线版（所有文件内嵌） |
| `tools/build_en.py` | 生成英文网页版（翻译对照表 + 防漏译检查） |
| `tools/build_offline.py` | 生成中英文单文件离线版的脚本 |

## 修改后重新生成英文版与离线版

修改 `index.html`、`lib/` 或 `data/` 后依次运行（需要 Python 3）：

```
python3 tools/build_en.py        # 生成英文网页版 en.html
python3 tools/build_offline.py   # 生成中英文两个单文件离线版
```

如果改动了界面文字，`build_en.py` 会提示哪些原文在对照表里找不到或仍有中文未翻译，按提示补充 `tools/build_en.py` 中的对照表即可。

## 数据来源

- 显示用地形 / 海深：AWS Terrain Tiles 第 5 级（陆地 GMTED2010，海洋 ETOPO1）；南北纬 84° 以外的极区边缘沿用项目原有素材
- 极值网格：AWS Terrain Tiles 第 8 级（SRTM；北纬 60° 以北 GMTED2010；加拿大 NRCan CDEM；海洋 ETOPO1）
- 海陆掩膜：基于 GEBCO（项目原有素材）
- 国界：Natural Earth 10m（经 world-atlas）
- 经典位置：各高峰、海沟等的官方测量值

## 许可
界面、程序与整合方式 © 2026 wzh，采用 [CC BY-NC 4.0](LICENSE)（署名-非商业性使用）：可免费使用、分享、改编，须署名并注明改动，不得用于商业目的。**商用请联系作者**：wzh9436@protonmail.com（一般问题请提 [Issue](https://github.com/wzh9436/earth-elevation/issues)；GitHub：[@wzh9436](https://github.com/wzh9436)）。

第三方数据与程序库保持各自的原许可（SRTM、GMTED2010、ETOPO1、NRCan CDEM、GEBCO、Natural Earth、three.js 等），署名清单见页面内「数据与许可」，非商业限制只适用于本项目的原创部分。

---

Copyright © 2026 wzh. Licensed under [CC BY-NC 4.0](LICENSE) — free for non-commercial use with attribution; for commercial use please contact the author at wzh9436@protonmail.com (general questions: [Issues](https://github.com/wzh9436/earth-elevation/issues); GitHub: [@wzh9436](https://github.com/wzh9436)). Third-party data and libraries keep their own licenses (see "Data & License" in the app).


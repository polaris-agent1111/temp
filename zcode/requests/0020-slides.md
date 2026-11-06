status: done
priority: 2
assignee: zcode
created: 2026-11-05 20:20

# 0020 — 把答辩大纲做成可直接放映的幻灯片

## 背景

`report/答辩大纲.md`（0011 产出，17 KB）已经有 12–15 页大纲、8 分钟逐页讲稿、10 条预判问答和一页纸极简版。但截止 11/20–22 厦门现场答辩前还需要**真的能放**的幻灯片文件。你不需要生成 pptx，只要输出「可放映且可打印」的两种格式即可。

## 目标产出

### 1. `report/答辩-幻灯片.md`（Marp 格式）

- 文件头加 Marp frontmatter：
  ```
  ---
  marp: true
  theme: default
  paginate: true
  header: '赛博coder · 六载穿柜'
  ---
  ```
- 每页用 `---` 分隔，页数与 `答辩大纲.md` 对齐（12–15 页 + 1 页封底）。
- 每页正文精简到「一屏能读完」：标题 + 3–5 个要点 + 图表占位符（如 `![w:900](figures/fig2_per_file.png)`，指向 `report/figures/` 里已有的三张图）。
- **讲稿不放进幻灯片正文**，统一放到文末附录（按页编号列出，方便打印）。
- 不要编造数据：所有数字从 `report/技术报告-v3.md`、`report/答辩大纲.md`、`report/官方探测分析.md` 取。

### 2. `report/答辩-幻灯片.html`（自包含，可直接双击打开/打印成 PDF）

- 单个 HTML 文件，内联 CSS 与 JS，**不依赖任何外部 CDN**（现场没网也能放）。
- 键盘 ←/→ 翻页、F 全屏、P 打印；一页一张卡片，打印时每页分页（`@media print { .slide { page-break-after: always; } }`）。
- 图片用相对路径 `figures/fig1_config_compare.png` 等（与 md 同目录层级），若担心路径问题可在 `report/目录另存说明` 里注明。
- 字号要够大（正文 ≥ 24px），标题 ≥ 40px；深色标题栏 + 浅色正文，投影清晰。
- 页面内容与 md 完全一致。

### 3. `report/答辩-讲稿-附录.md`（可选，若 md 附录已够则跳过）

## 校验（必须做）

- 用 Python 打开两个文件做静态检查：md 页数（`---` 分隔符计数）、html 里 `<section class="slide">` 数量，两者页数必须一致且 ≥12。
- 逐个 grep 数字，确认与 `技术报告-v3.md` 一致（至少检查：133.086、245.995、243.958、127.01、121.6、112.36、126.965、52%）。
- 确认 html 里没有 `http://` 或 `https://` 开头的外部资源引用。

## 禁止

不提交、不登录、不碰云主机、不改 `runs/`；不写真实凭据。

## 交付

`report/答辩-幻灯片.md` + `report/答辩-幻灯片.html` + `zcode/reports/0020-slides.md`（1 页摘要：页数、检查结果、还有哪些图待补）。完成后把本文件头改成 `status: done`。

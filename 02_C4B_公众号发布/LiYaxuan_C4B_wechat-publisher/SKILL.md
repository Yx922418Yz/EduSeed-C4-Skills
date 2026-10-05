---
name: wechat-publisher
description: >
  把 Markdown/Word 文章转换为微信公众号兼容的排版 HTML，支持 5 套主题
  （blue/orange/green/gray/purple）、callout 提示框、自动目录、元信息栏、
  关注页脚与内容密度检查。当用户说"转公众号格式"、"排版成公众号文章"、
  "convert to WeChat article"、"生成公众号 HTML"、"帮我把这篇发公众号"，
  或需要把 .md/.docx 文章转成可直接粘贴进 mp.weixin.qq.com 编辑器的格式时使用。
  也适用于任何"需要严格遵循平台标签/CSS 限制输出文章 HTML"的排版任务。
---

# WeChat Publisher（公众号文章排版技能）

## Purpose

把一篇 Markdown（或 Word）文章转成**公众号编辑器可直接粘贴**的 HTML：
所有样式内联、无 class/id、无 script/style 块，粘贴进 mp.weixin.qq.com 不丢格式。

本技能基于 `c4b-wechat-publisher-starter` 定制，通过 skill-creator 流程开发，
新增 5 项能力：**主题系统 / callout 提示框 / 自动目录 / 元信息栏 / 内容密度检查**。

## Prerequisites

```bash
python -m pip install markdown beautifulsoup4 python-docx lxml
```

## Workflow

### 1. 写文章（Markdown 源文件）

- 用 `##` 作为章节标题（公众号顶级标题是 h2，`#` 会被自动转 h2）
- 需要提示框时写 `> [!note] 内容` / `> [!tip] 内容` / `> [!warning] 内容`
- 需要代码时用 ``` ``` ``` 围栏代码块
- 参考 `examples/` 里的示例文章结构

### 2. 选择主题

| 场景 | 主题 |
|------|------|
| 技术教程/学习分享 | `blue`（默认） |
| 活动/生活 | `orange` |
| 健康/校园 | `green` |
| 职场/长文 | `gray` |
| 创意/年轻化 | `purple` |

配色明细见 `references/theme_palettes.md`。

### 3. 转换

```bash
python scripts/convert_to_wechat.py article.md output.html \
    --theme blue --toc --meta --footer
```

- `--toc`：文首生成编号目录
- `--meta`：标题/作者/日期/字数/阅读时长元信息栏
- `--footer`：关注引导 + 版权 + AI 辅助声明页脚
- 转换后自动输出**内容密度检查报告**（段落 ≤120 字、列表 ≤7 项等，规则见 `references/wechat_restrictions.md`）

### 4. 发布

1. 浏览器打开 `output.html` 预览（手机宽度预览）
2. Ctrl+A → Ctrl+C 全选复制
3. 公众号后台新建图文 → Ctrl+V 粘贴
4. 替换页脚中的"公众号名片二维码"占位（媒体库上传图片后插入）
5. 手机预览 → 发布

## Input / Output

- **输入**：`.md` / `.docx` / `.html` 文章文件
- **输出**：公众号兼容 HTML 文件（inline styles only）+ 终端密度检查报告

## 内容规范（写作时遵守）

- 段落 ≤ 120 中文字符，一句话一换行，手机端可扫读
- 列表 ≤ 7 项，超出拆成小节
- 全文至少 3 个 `##` 章节
- 代码块 ≤ 40 行
- 使用 callout 突出关键提示，别滥用（每 500 字 ≤ 1 个）

## 限制（公众号平台约束）

- 禁止 `<h1>`/`<div>`/`<script>`/`<style>`/`<iframe>`/SVG 内联图
- 禁止 class/id/事件属性；CSS 全部内联
- 目录无法点击跳转（无 id 锚点），以编号列表呈现
- 完整限制清单见 `references/wechat_restrictions.md`

## Edge Cases

| 情况 | 处理 |
|------|------|
| 文章无 `##` 章节 | 密度检查提示"章节过少" |
| 未知主题名 | 报错并列出可用主题 |
| 输入为 .html | 直接净化（sanitize）后再排版 |
| 未安装依赖 | 脚本自动 pip install |
| 图片 SVG | 剥离（公众号无法托管 SVG） |

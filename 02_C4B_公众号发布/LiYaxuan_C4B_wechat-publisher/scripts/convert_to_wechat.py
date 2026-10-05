#!/usr/bin/env python3
"""
WeChat Publisher — Convert Markdown/Word to WeChat-compatible HTML.

基于 c4b-wechat-publisher-starter 的 convert_to_wechat.py 升级：
  + 5 套主题系统（--theme: blue/orange/green/gray/purple）
  + Callout 提示框（> [!note] / [!tip] / [!warning]）
  + 自动目录 TOC（--toc，生成编号章节列表）
  + 元信息栏（--meta：标题/作者/日期/阅读时长）
  + 关注页脚（--footer：公众号名片位/版权/声明）
  + 内容密度检查（信息密度规则：段落字数/列表长度/标题层级）

用法:
    python convert_to_wechat.py article.md output.html [--theme blue] [--toc] [--meta] [--footer]
    python convert_to_wechat.py report.docx output.html --theme green

然后: 用浏览器打开 output.html → Ctrl+A → Ctrl+C → 粘贴到公众号编辑器。
"""

import sys
import os
import re
import json
from pathlib import Path

try:
    import markdown
    from bs4 import BeautifulSoup
    from docx import Document
except ImportError:
    print("缺少依赖，正在安装 markdown beautifulsoup4 python-docx lxml ...", file=sys.stderr)
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "markdown", "beautifulsoup4", "python-docx", "lxml", "-q"])
    import markdown
    from bs4 import BeautifulSoup
    from docx import Document

# ============================================================
# 主题系统（5 套主题，新增能力 1）
# ============================================================
THEMES = {
    "blue": {   # 简约蓝（默认）
        "name": "简约蓝",
        "h2": "#1a73e8", "h3": "#1a73e8",
        "accent": "#1a73e8", "accent_bg": "#f0f7ff",
        "blockquote_bg": "#f0f7ff", "blockquote_border": "#1a73e8",
        "th_bg": "#1a73e8", "th_color": "#ffffff",
        "code_bg": "#f6f8fa", "code_color": "#d73a49",
        "link": "#0366d6", "meta_bg": "#f0f7ff",
    },
    "orange": {  # 暖阳橙
        "name": "暖阳橙",
        "h2": "#e65100", "h3": "#e65100",
        "accent": "#ff9800", "accent_bg": "#fff8e1",
        "blockquote_bg": "#fff8e1", "blockquote_border": "#ff9800",
        "th_bg": "#e65100", "th_color": "#ffffff",
        "code_bg": "#fdf6ec", "code_color": "#c25e00",
        "link": "#e65100", "meta_bg": "#fff8e1",
    },
    "green": {   # 清新绿
        "name": "清新绿",
        "h2": "#2e7d32", "h3": "#2e7d32",
        "accent": "#4caf50", "accent_bg": "#e8f5e9",
        "blockquote_bg": "#e8f5e9", "blockquote_border": "#4caf50",
        "th_bg": "#2e7d32", "th_color": "#ffffff",
        "code_bg": "#f1f8e9", "code_color": "#33691e",
        "link": "#2e7d32", "meta_bg": "#e8f5e9",
    },
    "gray": {    # 高级灰
        "name": "高级灰",
        "h2": "#37474f", "h3": "#546e7a",
        "accent": "#78909c", "accent_bg": "#f4f6f7",
        "blockquote_bg": "#f4f6f7", "blockquote_border": "#78909c",
        "th_bg": "#37474f", "th_color": "#ffffff",
        "code_bg": "#eceff1", "code_color": "#37474f",
        "link": "#455a64", "meta_bg": "#f4f6f7",
    },
    "purple": {  # 活力紫
        "name": "活力紫",
        "h2": "#6a1b9a", "h3": "#6a1b9a",
        "accent": "#9c27b0", "accent_bg": "#f3e5f5",
        "blockquote_bg": "#f3e5f5", "blockquote_border": "#9c27b0",
        "th_bg": "#6a1b9a", "th_color": "#ffffff",
        "code_bg": "#f5f0f8", "code_color": "#8e24aa",
        "link": "#6a1b9a", "meta_bg": "#f3e5f5",
    },
}

CALLOUT_STYLES = {
    "note":    {"label": "💡 小贴士", "bg": "#f0f7ff", "border": "#1a73e8", "color": "#333"},
    "tip":     {"label": "✅ 实用技巧", "bg": "#e8f5e9", "border": "#4caf50", "color": "#333"},
    "warning": {"label": "⚠️ 注意", "bg": "#fff8e1", "border": "#ff9800", "color": "#333"},
}

# 信息密度规则（新增能力 5：内容密度检查）
DENSITY_RULES = {
    "max_paragraph_cn": 120,   # 段落最长（中文字符）
    "max_list_items": 7,       # 单个列表最多条目
    "max_h3_under_h2": 5,      # 单个 H2 下 H3 数量
    "min_sections": 3,         # 至少 3 个章节
    "max_code_block_lines": 40,# 代码块最大行数
}

# 公众号允许的标签/CSS（沿用 starter 规则）
ALLOWED_TAGS = {'p', 'h2', 'h3', 'ul', 'ol', 'li', 'span', 'img', 'a',
                'table', 'tr', 'th', 'td', 'br'}
FORBIDDEN_TAGS = {'script', 'style', 'iframe', 'h1', 'div'}
ALLOWED_CSS = {
    'color', 'background-color', 'font-size', 'font-weight',
    'line-height', 'text-align', 'font-style', 'margin',
    'padding', 'border', 'border-left', 'border-collapse',
    'text-decoration', 'border-radius',
}

CALLOUT_RE = re.compile(r"^\[!(note|tip|warning)\]\s*(.*)$", re.IGNORECASE)


# ============================================================
# 输入读取
# ============================================================

def read_markdown(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    html = markdown.markdown(content, extensions=[
        'extra', 'fenced_code', 'nl2br', 'sane_lists',
    ])
    return html


def read_docx(filepath):
    doc = Document(filepath)
    parts = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style_name = para.style.name if para.style else ''
        if style_name.startswith('Heading'):
            level = style_name.replace('Heading ', '')
            tag = 'h2' if level in ('1', '2') else 'h3'
            parts.append(f'<{tag}>{text}</{tag}>')
        else:
            p_html = '<p>'
            for run in para.runs:
                t = run.text
                if not t:
                    continue
                if run.bold and run.italic:
                    p_html += f'<span style="font-weight:bold;font-style:italic;">{t}</span>'
                elif run.bold:
                    p_html += f'<span style="font-weight:bold;">{t}</span>'
                elif run.italic:
                    p_html += f'<span style="font-style:italic;">{t}</span>'
                else:
                    p_html += t
            p_html += '</p>'
            parts.append(p_html)
    return '\n'.join(parts)


# ============================================================
# 净化器（沿用 starter + 新增 callout 支持）
# ============================================================

def sanitize(html, theme):
    soup = BeautifulSoup(html, 'lxml')

    for tag_name in ('script', 'style', 'iframe'):
        for el in soup.find_all(tag_name):
            el.decompose()

    for h1 in soup.find_all('h1'):
        h1.name = 'h2'

    for div in soup.find_all('div'):
        div.name = 'p'

    # 代码块 → 样式化 p
    for pre in soup.find_all('pre'):
        code = pre.find('code')
        code_text = code.get_text() if code else pre.get_text()
        p = soup.new_tag('p')
        p.string = code_text
        p['style'] = (
            f'background-color: {theme["code_bg"]}; color: {theme["code_color"]}; '
            'font-size: 14px; line-height: 1.6; padding: 16px; margin: 10px 0; '
            'font-family: Menlo, Consolas, monospace; white-space: pre-wrap;'
        )
        pre.replace_with(p)

    # 行内代码
    for code in soup.find_all('code'):
        span = soup.new_tag('span')
        span.string = code.get_text()
        span['style'] = (
            f'background-color: {theme["code_bg"]}; color: {theme["code_color"]}; '
            'font-size: 14px; padding: 2px 4px; border-radius: 3px;'
        )
        code.replace_with(span)

    # blockquote → 样式化 p（新增：callout 支持，含多行正文）
    for bq in soup.find_all('blockquote'):
        raw = bq.get_text().strip()
        m = CALLOUT_RE.match(raw)
        kind = None
        rest = ""
        if m:
            kind, rest = m.group(1).lower(), m.group(2).strip()
        else:
            # 多行 callout：首行为 "[!xxx]"，其余为正文
            lines = raw.split("\n", 1)
            first_line = lines[0].strip()
            hm = re.match(r"^\[!(note|tip|warning)\]\s*$", first_line, re.IGNORECASE)
            if hm:
                kind = hm.group(1).lower()
                rest = lines[1].strip() if len(lines) > 1 else ""
        if kind:
            cs = CALLOUT_STYLES.get(kind, CALLOUT_STYLES["note"])
            # 主题色覆盖 callout 主色
            p = soup.new_tag('p')
            label = cs["label"]
            p.string = f'{label}　{rest}' if rest else label
            p['style'] = (
                f'background-color: {cs["bg"]}; color: {cs["color"]}; font-size: 15px; '
                f'line-height: 1.7; padding: 12px 14px; margin: 12px 0; '
                f'border-left: 4px solid {cs["border"]}; border-radius: 4px;'
            )
            bq.replace_with(p)
        else:
            p = soup.new_tag('p')
            p.string = raw
            p['style'] = (
                f'background-color: {theme["blockquote_bg"]}; color: #666; font-size: 15px; '
                f'line-height: 1.7; padding: 12px 14px; margin: 12px 0; '
                f'border-left: 4px solid {theme["blockquote_border"]}; border-radius: 4px;'
            )
            bq.replace_with(p)

    # strong/b/em/i → styled span
    for tag in soup.find_all(['strong', 'b']):
        span = soup.new_tag('span')
        span.string = tag.get_text()
        span['style'] = 'font-weight: bold;'
        tag.replace_with(span)
    for tag in soup.find_all(['em', 'i']):
        span = soup.new_tag('span')
        span.string = tag.get_text()
        span['style'] = 'font-style: italic;'
        tag.replace_with(span)

    return soup


# ============================================================
# 主题样式应用
# ============================================================

def apply_styles(soup, theme):
    style_map = {
        'h2': f'font-size: 22px; font-weight: bold; line-height: 1.6; color: {theme["h2"]}; margin: 20px 0 10px 0;',
        'h3': f'font-size: 18px; font-weight: bold; line-height: 1.6; color: {theme["h3"]}; margin: 15px 0 8px 0;',
        'p': 'font-size: 16px; line-height: 1.75; color: #333; margin: 10px 0;',
        'li': 'font-size: 16px; line-height: 1.75; color: #333; margin: 5px 0;',
        'table': 'border-collapse: collapse; margin: 10px 0; font-size: 14px; width: 100%;',
        'th': (f'background-color: {theme["th_bg"]}; color: {theme["th_color"]}; '
               'font-weight: bold; padding: 8px; text-align: left; border: 1px solid #ddd;'),
        'td': 'padding: 8px; border: 1px solid #ddd; color: #333;',
        'a': f'color: {theme["link"]}; text-decoration: underline;',
    }
    for tag_name, style in style_map.items():
        for el in soup.find_all(tag_name):
            existing = el.get('style', '')
            if existing:
                continue
            el['style'] = style
    return soup


def clean_attributes(soup):
    for tag in soup.find_all(True):
        for attr in ('class', 'id'):
            if attr in tag.attrs:
                del tag.attrs[attr]
        if tag.name not in ALLOWED_TAGS and tag.name not in ('html', 'head', 'body', '[document]'):
            tag.unwrap()
    return soup


# ============================================================
# 新增能力 2~5：目录 / 元信息 / 页脚 / 密度检查
# ============================================================

def build_toc(soup):
    """从 h2 生成带编号的目录（ul/li，公众号兼容）。"""
    h2s = soup.find_all('h2')
    if len(h2s) < 2:
        return None
    items = []
    for i, h2 in enumerate(h2s, 1):
        title = h2.get_text().strip()
        items.append(f'<li style="font-size: 15px; line-height: 1.8; margin: 6px 0; '
                     f'color: #333;"><span style="font-weight: bold; color: {THEMES[active_theme]["accent"]}; '
                     f'margin-right: 6px;">{i:02d}</span>{title}</li>')
    return ('<p style="font-size: 17px; font-weight: bold; color: #333; margin: 16px 0 8px 0;">'
            '📑 本文目录</p><ul style="padding-left: 20px; margin: 10px 0;">'
            + ''.join(items) + '</ul>')


def build_meta_bar(title, author, date, word_count):
    """文章头部元信息栏：标题/作者/日期/字数/阅读时长。"""
    read_min = max(1, round(word_count / 400))
    def esc(s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return (
        f'<p style="font-size: 20px; font-weight: bold; line-height: 1.5; color: #333; '
        f'margin: 10px 0 6px 0;">{esc(title)}</p>'
        f'<p style="font-size: 13px; color: #888; margin: 4px 0 14px 0;">'
        f'👤 {esc(author)}　📅 {date}　📝 {word_count} 字　⏱ 约 {read_min} 分钟</p>'
    )


def build_footer(article_title, author, theme):
    """文章尾部：关注引导 + 版权 + 声明（公众号名片位留待发布时替换）。"""
    return (
        '<p style="border-top: 1px solid #eee; margin: 24px 0 12px 0;"></p>'
        f'<p style="background-color: {theme["meta_bg"]}; font-size: 14px; color: #666; '
        f'line-height: 1.8; padding: 12px 14px; margin: 12px 0; border-radius: 4px;">'
        f'📮 <span style="font-weight: bold; color: #333;">关注我们</span>：'
        f'（此处替换为你的公众号名片二维码，公众号后台「素材管理 → 图片」上传后插入）<br>'
        f'本文由 {author} 撰写，使用 <span style="font-weight: bold;">wechat-publisher 技能</span> '
        f'自动排版为公众号格式。</p>'
        f'<p style="font-size: 13px; color: #aaa; text-align: center; margin: 8px 0;">'
        f'© {date_part()} {author} ｜ 本文使用 AI 辅助写作，已通过 wechat-publisher 技能格式校验</p>'
    )


def date_part():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


# ============================================================
# 内容密度检查（新增能力 5）
# ============================================================

def lint_content(soup, source_text):
    """按信息密度规则检查，返回问题清单。"""
    issues = []

    # 段落长度
    for p in soup.find_all('p'):
        text = p.get_text().strip()
        cn_len = len(re.findall(r'[\u4e00-\u9fff]', text))
        if cn_len > DENSITY_RULES["max_paragraph_cn"]:
            issues.append(f'段落过长（{cn_len} 中文字符 > {DENSITY_RULES["max_paragraph_cn"]}）："{text[:24]}..."')

    # 列表长度
    for ul in soup.find_all('ul'):
        items = ul.find_all('li')
        if len(items) > DENSITY_RULES["max_list_items"]:
            issues.append(f'列表条目过多（{len(items)} > {DENSITY_RULES["max_list_items"]}），建议拆分')

    # H2 下 H3 数量
    for h2 in soup.find_all('h2'):
        siblings = []
        nxt = h2.find_next_sibling()
        while nxt is not None and nxt.name != 'h2':
            if nxt.name == 'h3':
                siblings.append(nxt)
            nxt = nxt.find_next_sibling()
        if len(siblings) > DENSITY_RULES["max_h3_under_h2"]:
            issues.append(f'章节 "{h2.get_text()[:16]}" 下子标题过多（{len(siblings)} > {DENSITY_RULES["max_h3_under_h2"]}）')

    # 章节数量
    n_h2 = len(soup.find_all('h2'))
    if n_h2 < DENSITY_RULES["min_sections"]:
        issues.append(f'章节过少（{n_h2} < {DENSITY_RULES["min_sections"]}），建议至少 3 个 H2 章节')

    # 代码块行数
    for p in soup.find_all('p'):
        style = p.get('style', '')
        if 'white-space: pre-wrap' in style:
            n_lines = p.get_text().count('\n') + 1
            if n_lines > DENSITY_RULES["max_code_block_lines"]:
                issues.append(f'代码块过长（{n_lines} 行 > {DENSITY_RULES["max_code_block_lines"]}），建议精简')

    return issues


# ============================================================
# 主转换
# ============================================================

def convert(input_path, output_path, theme_name="blue", toc=False, meta=False, footer=False):
    global active_theme
    theme = THEMES.get(theme_name)
    if not theme:
        print(f"❌ 未知主题: {theme_name}，可用: {', '.join(THEMES)}", file=sys.stderr)
        return False
    active_theme = theme_name

    path = Path(input_path)
    if not path.exists():
        print(f"❌ 文件不存在: {input_path}", file=sys.stderr)
        return False

    ext = path.suffix.lower()
    if ext == '.md':
        html = read_markdown(input_path)
    elif ext == '.docx':
        html = read_docx(input_path)
    elif ext in ('.html', '.htm'):
        with open(input_path, 'r', encoding='utf-8') as f:
            html = f.read()
    else:
        print(f"❌ 不支持的格式: {ext}（支持 .md / .docx / .html）", file=sys.stderr)
        return False

    soup = sanitize(html, theme)
    soup = apply_styles(soup, theme)
    soup = clean_attributes(soup)

    body = soup.find('body')
    content = '\n'.join(str(child) for child in body.children if str(child).strip()) if body else str(soup)

    # 标题与字数
    h2_first = soup.find('h2')
    article_title = h2_first.get_text().strip() if h2_first else Path(input_path).stem
    word_count = len(re.sub(r'\s', '', soup.get_text()))

    # 组装（目录 + 元信息 + 正文 + 页脚）
    sections = []
    if toc:
        toc_html = build_toc(soup)
        if toc_html:
            sections.append(toc_html)
    if meta:
        sections.append(build_meta_bar(article_title, "LiYaxuan", date_part(), word_count))
    sections.append(content)
    if footer:
        sections.append(build_footer(article_title, "LiYaxuan", theme))
    body_html = '\n'.join(s for s in sections if s)

    output_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{article_title} — WeChat Preview</title>
</head>
<body style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', Roboto, sans-serif;">
{body_html}
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_html)

    # 密度检查报告
    issues = lint_content(soup, html)
    print(f"\n📊 内容密度检查（主题: {theme['name']}）:")
    if issues:
        for it in issues:
            print(f"   ⚠️ {it}")
    else:
        print("   ✅ 全部通过")

    size_kb = os.path.getsize(output_path) / 1024
    print(f"\n✅ 完成! {output_path} ({size_kb:.1f} KB, {word_count} 字)")
    print("📋 发布步骤:")
    print("   1. 浏览器打开 output.html 预览")
    print("   2. Ctrl+A → Ctrl+C 全选复制")
    print("   3. mp.weixin.qq.com → 新建图文 → Ctrl+V 粘贴")
    print("   4. 替换页脚中的公众号名片二维码")
    print("   5. 手机预览 → 发布")
    return True


def main():
    if len(sys.argv) < 3:
        print("WeChat Publisher（升级版）")
        print("=" * 40)
        print("用法: python convert_to_wechat.py <input> <output> [选项]")
        print("选项:")
        print("  --theme <name>   主题: " + " / ".join(THEMES.keys()) + f"（默认 blue）")
        print("  --toc            生成目录")
        print("  --meta           生成标题/作者/日期元信息栏")
        print("  --footer         生成关注引导页脚")
        print("示例: python convert_to_wechat.py article.md out.html --theme green --toc --meta --footer")
        sys.exit(1)

    args = sys.argv[1:]
    input_path, output_path = args[0], args[1]
    theme_name = "blue"
    toc = meta = footer = False
    i = 2
    while i < len(args):
        if args[i] == "--theme" and i + 1 < len(args):
            theme_name = args[i + 1]
            i += 2
        elif args[i] == "--toc":
            toc = True; i += 1
        elif args[i] == "--meta":
            meta = True; i += 1
        elif args[i] == "--footer":
            footer = True; i += 1
        else:
            i += 1

    success = convert(input_path, output_path, theme_name, toc, meta, footer)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

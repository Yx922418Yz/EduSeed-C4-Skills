# WeChat Publisher — Style Reference（升级版）

公众号文章的内联 CSS 样式规范。所有样式必须内联在标签 `style=""` 中，
禁止使用 class/id/`<style>` 块（公众号会剥离）。配色请优先参考
`theme_palettes.md`（5 套主题）。

## 排版基础（各主题通用）

### H2（章节标题 — 公众号的顶级标题）
```
font-size: 22px; font-weight: bold; line-height: 1.6;
color: <主题色>; margin: 20px 0 10px 0;
```

### H3（子标题）
```
font-size: 18px; font-weight: bold; line-height: 1.6;
color: <主题色>; margin: 15px 0 8px 0;
```

### 正文（段落）
```
font-size: 16px; line-height: 1.75; color: #333; margin: 10px 0;
```

### 列表项
```
font-size: 16px; line-height: 1.75; color: #333; margin: 5px 0;
```

### 行内代码
```
background-color: <主题代码底色>; color: <主题代码色>; font-size: 14px;
padding: 2px 4px; border-radius: 3px;
```

### 代码块（用 <p> + pre-wrap 模拟）
```
background-color: <主题代码底色>; color: <主题代码色>; font-size: 14px;
line-height: 1.6; padding: 16px; margin: 10px 0;
font-family: Menlo, Consolas, monospace; white-space: pre-wrap;
```

## Callout 提示框（C4B 新增能力）

Markdown 源文件写 `> [!note]` / `> [!tip]` / `> [!warning]` 前缀，转换器自动生成彩色提示框：

| 类型 | 触发写法 | 标签 | 背景 | 左边框 |
|------|----------|------|------|--------|
| note | `> [!note] 内容` | 💡 小贴士 | `#f0f7ff` | `4px solid #1a73e8` |
| tip | `> [!tip] 内容` | ✅ 实用技巧 | `#e8f5e9` | `4px solid #4caf50` |
| warning | `> [!warning] 内容` | ⚠️ 注意 | `#fff8e1` | `4px solid #ff9800` |

示例输出（note）：
```html
<p style="background-color: #f0f7ff; color: #333; font-size: 15px; line-height: 1.7;
          padding: 12px 14px; margin: 12px 0; border-left: 4px solid #1a73e8;
          border-radius: 4px;">💡 小贴士　这里是内容</p>
```

## 结构元素

### 目录（C4B 新增能力，--toc）
公众号不支持 id 锚点跳转，目录以「编号章节列表」形式置于文首：

```html
<p style="font-size: 17px; font-weight: bold; color: #333; margin: 16px 0 8px 0;">📑 本文目录</p>
<ul style="padding-left: 20px; margin: 10px 0;">
  <li style="font-size: 15px; line-height: 1.8; margin: 6px 0; color: #333;">
    <span style="font-weight: bold; color: #1a73e8; margin-right: 6px;">01</span>章节标题</li>
</ul>
```

### 元信息栏（C4B 新增能力，--meta）
标题（20px bold）+ 作者/日期/字数/阅读时长（13px 灰）。

### 引用块
```
background-color: <主题引用底色>; color: #666; font-size: 15px; line-height: 1.7;
padding: 12px 14px; margin: 12px 0; border-left: 4px solid <主题强调色>;
border-radius: 4px;
```

### 表格
```
table:  border-collapse: collapse; margin: 10px 0; font-size: 14px; width: 100%;
th:     background-color: <主题表头色>; color: #fff; font-weight: bold; padding: 8px;
        text-align: left; border: 1px solid #ddd;
td:     padding: 8px; border: 1px solid #ddd; color: #333;
```

### 链接
```
color: <主题链接色>; text-decoration: underline;
```

## 移动端考虑（沿用 starter）

- 正文字号最低 16px（手机可读下限）
- 最大宽度 ~375px（多数手机阅读宽度）
- 行高 1.75 是中文字体阅读甜点
- 避免纯黑 #000，用 #333 更护眼
- 图片必须 `max-width: 100%` 防溢出

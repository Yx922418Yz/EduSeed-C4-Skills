# 主题调色板（Theme Palettes）

C4B 升级能力之一：5 套主题，通过 `--theme` 切换。所有颜色均为公众号编辑器支持的
内联 CSS 值（RGB/HEX），不依赖外部字体与 CSS 类。

## 调色板总览

| 主题 | 名称 | H2/H3 标题色 | 强调色 | 提示框底色 | 表头背景 | 代码色 |
|------|------|-------------|--------|-----------|---------|--------|
| `blue` | 简约蓝（默认） | `#1a73e8` | `#1a73e8` | `#f0f7ff` | `#1a73e8`（白字） | `#d73a49` |
| `orange` | 暖阳橙 | `#e65100` | `#ff9800` | `#fff8e1` | `#e65100`（白字） | `#c25e00` |
| `green` | 清新绿 | `#2e7d32` | `#4caf50` | `#e8f5e9` | `#2e7d32`（白字） | `#33691e` |
| `gray` | 高级灰 | `#37474f` | `#78909c` | `#f4f6f7` | `#37474f`（白字） | `#37474f` |
| `purple` | 活力紫 | `#6a1b9a` | `#9c27b0` | `#f3e5f5` | `#6a1b9a`（白字） | `#8e24aa` |

## 每套主题的实际效果（blue 示例）

```
H2 章节标题: 22px bold, color #1a73e8
H3 子标题:   18px bold, color #1a73e8
正文:        16px, line-height 1.75, color #333
引用块:      背景 #f0f7ff, 左边框 4px solid #1a73e8
表格表头:    背景 #1a73e8, 白字, bold
链接:        color #0366d6, underline
代码:        背景 #f6f8fa, 文字 #d73a49
```

## 选择建议

| 场景 | 推荐主题 |
|------|----------|
| 技术教程 / 学习分享 | `blue`（简约蓝） |
| 活动宣传 / 生活分享 | `orange`（暖阳橙） |
| 健康 / 环保 / 校园 | `green`（清新绿） |
| 职场 / 深度长文 | `gray`（高级灰） |
| 创意 / 娱乐 / 年轻化 | `purple`（活力紫） |

## 新增主题方法

编辑 `scripts/convert_to_wechat.py` 中的 `THEMES` 字典，按现有字段格式添加一组颜色即可：

```python
"my_theme": {
    "name": "我的主题",
    "h2": "#000000", "h3": "#000000",
    "accent": "#111111", "accent_bg": "#fafafa",
    "blockquote_bg": "#fafafa", "blockquote_border": "#111111",
    "th_bg": "#111111", "th_color": "#ffffff",
    "code_bg": "#f4f4f4", "code_color": "#b71c1c",
    "link": "#111111", "meta_bg": "#fafafa",
}
```

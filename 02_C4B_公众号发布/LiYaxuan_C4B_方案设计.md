# C4B 方案设计：公众号文章生成技能（LiYaxuan_C4B_wechat-publisher）

## 一、挑战要求与目标

C4B 挑战：**用 skill-creator 把 starter kit（c4b-wechat-publisher-starter）改造成自己的公众号文章生成技能，并用它产出一篇真实公众号文章**。

我的目标：
1. 保留 starter 已验证的转换管线（read → sanitize → style → clean）；
2. 新增 5 项能力，补足 starter 缺失（主题/目录/元信息/页脚/密度检查/callout）；
3. 诚实适配"侧边栏"需求 → 公众号平台不支持侧边栏，改为文首元信息栏；
4. 用技能生成一篇真实风格文章（2345 字）并转换验证。

## 二、架构

```
Markdown / Word
   │  read_markdown() / read_docx()
   ▼
原始 HTML（markdown 库 / python-docx 提取）
   │  sanitize()：剥 script/style/iframe、h1→h2、div→p、代码/加粗/斜体转 inline span
   │  callout 支持：> [!note/tip/warning] → 彩色提示框（单行 + 多行正文）
   ▼
合规 HTML
   │  apply_theme()：5 套主题 inline CSS（h2/h3/引用/表格/代码/链接/元信息底色）
   │  + --toc 文首编号目录
   │  + --meta 标题/作者/日期/字数/阅读时长
   │  + --footer 关注引导 + 版权
   ▼
copy-paste ready HTML（无 <style>/class/div/h1/script/iframe）
```

## 三、能力设计决策

| 新增能力 | 设计 | 理由 |
|----------|------|------|
| 5 套主题 | blue/orange/green/gray/purple，`--theme` 切换 | 公众号编辑器只认 inline CSS，主题即调色板替换 |
| Callout 提示框 | `> [!note/tip/warning]` markdown 语法触发 | 知识/技巧/警告三类高频排版元素 |
| 自动目录 | `--toc`，从 h2 生成编号章节列表 | 长文必备，手动维护目录易错 |
| 元信息栏 | `--meta`，标题/作者/日期/字数/阅读时长 | 公众号编辑器没有原生"作者栏" |
| 关注页脚 | `--footer`，名片位 + 版权 + AI 声明 | 实际发布必需，避免重复手写 |
| 内容密度检查 | 段落字数/列表长度/标题层级规则 | 防止流水账，提升文章质量分 |
| 侧边栏（starter 想要的） | **诚实拒绝并适配为文首元信息栏** | 公众号平台剥 div、禁侧栏，硬做必坏 |

## 四、与平台约束的对齐（references/wechat_restrictions.md）

| 平台约束 | 本技能处理 |
|----------|-----------|
| 只接受 inline CSS | 全部样式写在 `style=""` 属性 |
| 禁 h1 | sanitize 时 h1 → h2 |
| 禁 div | div → p |
| 禁 script/iframe | 直接删除 |
| SVG 会消失 | 不产出 SVG，图片留 img 标签走公众号 CDN |
| class 被剥 | 全程零 class |

## 五、验证方案

| 验证项 | 方法 |
|--------|------|
| 功能测试 | 最终文章（2345 字）跑 green 主题 + toc/meta/footer |
| Callout | 3 类 callout（note/tip/warning）各 1 个，单行+多行正文 |
| 合规性 | 正则扫描输出：无 style/class/div/h1/script/iframe |
| 密度检查 | 内置规则全过 |
| 发布路径 | 浏览器预览 → Ctrl+A/C → 公众号编辑器粘贴（SOP 已写入文章链接文档） |

## 六、诚实边界

- **公众号真实发布**依赖用户本人的账号操作（实名认证），本环境无法代做；已交付完整发布 SOP 与预览产物，发布后回填链接（见 LiYaxuan_C4B_文章链接.md）。
- 数学公式（LaTeX→PNG）未实现：本文章不含公式，列为后续迭代方向。

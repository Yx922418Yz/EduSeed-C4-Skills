# LiYaxuan C4B AI 日志

> 挑战：C4B 公众号文章生成技能
> 记录：AI 怎么用的、迭代了几轮、踩了什么坑、我做了什么。

## 一、使用的 AI 工具

| 工具 | 用途 |
|------|------|
| 豆包（当前会话 Agent） | 主开发：代码生成、调试、文档撰写 |
| skill-creator-for-work 技能 | 按官方流程创建/定制技能（C4B 硬性要求） |
| starter kit 自带说明 | c4b-wechat-publisher-starter 的 SKILL.md / styles / restrictions / sample |

## 二、开发流程（遵循 skill-creator 六步）

### Step 1 理解技能（具体例子）
- 读了 starter 的 sample_article.md：作者用 md 写文章 → 转换器转 HTML → 粘贴公众号；
- 明确了用户会说的话："帮我把这篇转成公众号格式"、"生成公众号 HTML"。

### Step 2 规划可复用内容
- 复用 starter：转换器管线（read → sanitize → style → clean）、限制清单、样式参考；
- 新增：主题调色板（5 套）、callout 渲染、TOC 生成、元信息栏、页脚、密度检查函数。

### Step 3 初始化技能（skill-creator init_skill.py）
- 按 skill-creator 要求，技能应创建在 `workspace/.user_skills` 下；
- **我的处理**：挑战要求交付物按 C4B 命名规范放在提交文件夹，因此技能先在工作区
  `.user_skills` 初始化并开发，交付时按挑战规范复制为 `LiYaxuan_C4B_wechat-publisher/`，
  同时在 `.skill` 包内保留完整结构（SKILL.md + scripts + references）。

### Step 4 编辑技能
- 编写升级版 `convert_to_wechat.py`（在 starter 基础上增加 5 项能力）；
- 编写 `references/theme_palettes.md`（新增）、升级 `wechat_styles.md`、`wechat_restrictions.md`；
- 用 `quick_validate.py` 风格自查：SKILL.md 有 name/description frontmatter、资源目录齐全。

### Step 5 定稿
- 删除 placeholder、测试临时文件；
- 用示例文章 + callout 测试转换器，逐项验证。

### Step 6 迭代
- 实测发现 2 个 bug（见下），修复后重新验证。

## 三、AI 使用方式与我的动作

| 环节 | 我做了什么（非 AI） | AI 做了什么 |
|------|---------------------|-------------|
| 需求定义 | 定出 5 项新能力清单（主题/callout/目录/元信息/密度检查） | 无 |
| 代码生成 | 审阅接口设计、确认复用 starter 管线 | 生成升级版 convert_to_wechat.py |
| 调试 | 构造测试用例（含 callout 的文章） | 定位正则问题 |
| 文档 | 撰写教学说明/方案取舍 | 生成 SKILL.md 骨架与参考文档初稿 |
| 验证 | 逐项核对输出 HTML（TOC/META/FOOTER/CALLOUT/禁标签） | 无 |

## 四、迭代记录（3 轮 bug 修复）

**第 1 轮（callout 不生效）：**
- 现象：`> [!tip]` 没有变成提示框；
- 根因 1：正则带了 markdown 的 `>` 前缀，但解析后的文本没有 `>` → 改为 `^\[!...\]`；
- 根因 2：`get_text()` 返回带前导换行，`^` 匹配失败 → 先 `.strip()` 再匹配；
- 修复后：tip/note/warning 三类 callout 全部转换成功（单行正文场景）。

**第 2 轮（真实文章发布测试时发现——多行 callout 失效）：**
- 现象：用最终文章（`> [!note]` 与正文分两行写）转换时，`[!note]` 原样残留、未变提示框；
- 根因：`CALLOUT_RE` 的 `(.*)$` 是单行匹配（`.` 不跨 `\n`），多行正文的 callout 整体不匹配，落入普通引用样式分支；
- 修复：新增多行分支——首行为 `[!xxx]`、其余行为正文；单行分支保留；
- 修复后：最终文章 3 个 callout（note/tip/warning）全部转换成功，无原样标记残留。

**第 3 轮（预防性自检）：**
- 预览 HTML 无 `<div>/<h1>/<script>/<style>/class=`，通过禁标签自检。

## 五、验证结果

| 验证项 | 结果 |
|--------|------|
| 5 主题切换 | ✅ 各主题颜色字段生效（green 测试通过） |
| Callout（tip/note/warning） | ✅ 单行 + 多行正文均生效 |
| 最终文章转换（2345 字） | ✅ 15.9 KB，TOC/META/FOOTER/CALLOUT 全齐 |
| TOC 目录 | ✅ 文首编号列表 |
| 元信息栏 | ✅ 标题/作者/日期/字数/阅读时长 |
| 页脚 | ✅ 关注引导 + 版权 + AI 声明 |
| 密度检查 | ✅ 示例文章全部通过 |
| 禁标签自检 | ✅ 无 div/h1/script/style/class |
| .skill 打包 | ✅ tar.gz 结构完整 |

## 六、反思

1. **正则要匹配"解析后"的文本而不是"源文本"**——同一份内容在 md 层和 HTML 层形态不同，调 bug 时先打印 `repr()` 看真实字符；
2. **skill-creator 的"克制"原则很对**：SKILL.md 只写工作流和触发，细节放 references，AI 用起来才不会上下文爆炸；
3. **公众号限制清单是知识资产**：这些坑（SVG 会消失、class 会被剥）不查文档根本不知道，放进技能比让 AI 现场猜靠谱得多。

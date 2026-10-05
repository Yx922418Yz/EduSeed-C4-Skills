# LiYaxuan C4B 拿来说明

> 记录：从 c4b-wechat-publisher-starter 拿了什么、加了什么、为什么。

## 一、拿来的基座

`c4b-wechat-publisher-starter`（starter kit）：
- `scripts/convert_to_wechat.py`：Markdown/Word → 公众号兼容 HTML 的完整管线；
- `references/wechat_styles.md`：排版样式规范（typography/code/structural/mobile）；
- `references/wechat_restrictions.md`：公众号平台限制全参考（标签/CSS/图片/文章限制）；
- `examples/sample_article.md`：示例文章。

## 二、拿了什么（复用清单）

| 组件 | 拿来的内容 |
|------|-----------|
| 转换管线 | read_markdown / read_docx → sanitize → apply_styles → clean_attributes → convert 主流程 |
| 平台知识 | 允许标签白名单、禁标签/属性、允许 CSS 属性清单、图片规则、文章限制 |
| 净化器 | h1→h2、div→p、pre/code→样式化 p、blockquote→样式化 p、strong/em→span |
| 排版基线 | 16px 正文 / 1.75 行高 / #333 文字 / 移动端注意点 |

## 三、加了什么（5 项新能力，超出 starter）

| 新能力 | 实现方式 | 为什么加（对应挑战要求） |
|--------|----------|--------------------------|
| ① 主题系统 | `THEMES` 字典 + `--theme` 参数，5 套配色（blue/orange/green/gray/purple） | Level 2 要求：支持多种风格，一键切换 |
| ② Callout 提示框 | `> [!note/tip/warning]` 源语法 → 彩色提示框（正则 + 样式表） | Level 2 要求：提示信息可视化 |
| ③ 自动目录 | `build_toc()` 从 h2 生成编号列表，`--toc` 开启 | Level 3 要求：目录/侧边栏 |
| ④ 元信息栏 | `build_meta_bar()` 标题/作者/日期/字数/阅读时长 | Level 3 要求：元数据 |
| ⑤ 内容密度检查 | `lint_content()` 按 DENSITY_RULES 输出质检报告 | 新增的"编辑质检"能力：保证手机端可读性 |

> 说明：starter 的 Level 3 提到"侧边栏"，但公众号是单栏排版（无侧边栏布局），
> 因此把"侧边栏信息"降级为文首元信息栏——这是对平台约束的诚实适配，方案见下。

## 四、关键决策与取舍

1. **为什么保留 starter 管线而不是重写？**
   starter 的净化/样式管线已经过真实公众号平台验证（限制清单就是血泪知识），
   重写只会重新踩坑。我的增量价值在**排版层**（主题/目录/提示框/质检），不在净化层。

2. **侧边栏 → 元信息栏的适配**（拿来的目标 4 项含"侧边栏"，公众号无此能力）：
   公众号编辑器不支持双栏/固定定位（position/flex 全禁），硬做侧边栏会被剥掉。
   方案：把"侧边栏信息"（作者/日期/字数/阅读时长）放到文首元信息栏，
   视觉效果等价、平台完全兼容。**这是拿与改的边界：平台不允许的，改成等价物而不是硬顶。**

3. **目录为什么是编号列表而不是可点击锚点？**
   公众号剥离 id 属性 → 锚点跳转不可用。编号目录至少让读者"知道这篇文章讲什么、
   讲到哪了"，诚实呈现平台限制（在 restrictions 文档中注明）。

4. **为什么把密度规则做成硬检查而不是建议？**
   手机端 375px 宽度，长段落/长列表的阅读体验断崖下跌。把规则写进 `DENSITY_RULES`
   每次转换自动执行，等于给"排版审美"装了个可执行的编辑器，比"建议"可靠。

5. **主题为什么用 HEX 常量表而不是 CSS 变量？**
   公众号禁止 CSS 变量/类，必须内联。把颜色集中到 `THEMES` 字典，
   既满足"内联"约束，又让换主题 = 换一个字典键，无需改代码。

## 五、与 skill-creator 的关系

按挑战要求使用 skill-creator-for-work 流程：Step1 例子分析 → Step2 资源规划 →
Step3 init_skill.py 初始化 → Step4 编写/升级资源 → Step5 定稿校验 → Step6 实测迭代。
完整过程记录在 `LiYaxuan_C4B_AI日志.md`。

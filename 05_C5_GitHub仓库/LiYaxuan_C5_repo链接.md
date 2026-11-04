# LiYaxuan C5 仓库链接

- **仓库全名**：Yx922418Yz/EduSeed-C4-Skills
- **URL**：https://github.com/Yx922418Yz/EduSeed-C4-Skills
- **分支**：main（Public 公开）

## 一句话说明

> 输入一个真实任务（技能评审 / 公众号排版 / 作业求解 / 本地 Agent），
> 输出一套可直接安装的 `.skill` 技能包 + 可复现运行证据与完整文档。

本仓库是 EduSeed Elite20 **C4 技能 → C5 开源仓库** 的作品集，
把 C4 完成的四个技能整理成别人能看懂、能复现、能协作贡献的开源项目。

## 仓库内已通过 API 推送并 GET 验证存在的文件

| 文件 | 说明 |
|------|------|
| `README.md` | 规范开源项目 README（一句话输入/输出、快速开始、示例、项目结构、技术栈、AI 说明、借鉴来源、License） |
| `LICENSE` | MIT，版权行 2026 李亚轩 / Li Yaxuan |
| `AI_LOG.md` | 仓库级 AI 协作日志 |
| `ATTRIBUTION.md` | 拿来说明（借鉴来源） |
| `CHANGELOG.md` | 版本记录 |
| `CONTRIBUTING.md` | 贡献指南 |
| `.gitignore` | 既有，保留 |
| `01_C4A_技能评审/` ~ `04_C4D_本地Agent/` | 四个 C4 技能文件夹及其内容（完整保留，未删除） |

## 验证方式

- 上传：`gh_helper upload ... --branch main`（GitHub REST API /contents 接口，产生真实 commit）。
- 验证：`gh_helper list` 根目录 + `gh_helper get <file>` 逐个 GET，均返回 200 且内容正确。
- 截图：headless Edge 打开线上仓库页（见 `LiYaxuan_C5_readme截图.png`），
  可见 main 分支 28 commits、文件树、MIT license 与渲染后的中文 README。

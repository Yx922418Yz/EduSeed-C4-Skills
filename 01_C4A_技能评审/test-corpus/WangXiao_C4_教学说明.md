# 技能X光分析器 —— 教学说明

## 上手步骤
1. 安装：把 .skill 文件拖入 Claude 技能目录（或使用安装命令）
2. 运行：对 Claude 说"扫描 ~/Documents/WeChat Files/Elite20群"
3. 查看输出：聊天中的 Markdown 表格 + 下载 Excel

## 常见坑
- 文件夹路径必须存在，否则会报错
- 中文文件名使用 UTF-8，乱码时检查系统编码

## 优化技巧
- 修改 references/challenges.yaml 可新增挑战定义，无需改代码

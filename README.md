# web-to-skill-pipeline

把**用户给的网页/论文列表/学者主页/文档站** → 提炼成方法论 → 落成可复用 skill 的工作流。

## 核心主张

> 提炼出来的是**方法**，不是**这个人的资源条件**。前者能写进 skill，后者只能写进"不要照抄"。

## 目录结构

```
web-to-skill-pipeline/
├── SKILL.md                          S0–S7 主流程、返工触发表、分工表
├── MY_RULES.md                       执行规范与硬边界
├── ATTRIBUTION.md                    流程来源、实测问题对照表、准确性边界
├── README.md
├── skill.json
├── references/
│   ├── fetch-resilience.md           取证链、降级顺序、拦截识别（含两条实测规则）
│   ├── source-tiering.md             A/B/C/D 分级与推理约束
│   ├── method-extraction.md          结构反推四步、内核门槛、规则翻译
│   ├── portability-test.md           方法 vs 资源条件、五问检验、"不该照抄"写法
│   ├── house-conventions.md          落盘目录探测、frontmatter、去重、命名
│   └── artifact-testing.md           合成数据自检、典型 bug、文档-代码同步
├── templates/
│   ├── extraction_brief.md           抽取简报
│   ├── source_ledger.md              来源台账与分级
│   ├── method_matrix.md              作品拆解矩阵与频次统计
│   ├── skill_skeleton.md             落盘前的结构草稿
│   └── attribution_block.md          ATTRIBUTION.md 骨架
└── scripts/
    └── fetch_probe.py                批量探测 URL 可用性并分类
```

## 快速开始

1. 写 `templates/extraction_brief.md`（明确提炼什么、不提炼什么）
2. 用脚本探测来源可用性 → 按降级顺序取证
3. 填 `templates/source_ledger.md`（A/B/C/D 分级）
4. 填 `templates/method_matrix.md`（≥8 篇，60% 门槛）
5. 过 S4 五问 → 写出"不该照抄"章节
6. 探测落盘目录与既有 skill → 写分工表
7. 按 `templates/skill_skeleton.md` 撰写
8. 体检：脚本自检 + 文档-代码同步 + 归属声明 + 清理

## 脚本用法

```bash
# 批量探测（联网）
python scripts/fetch_probe.py https://a.com https://b.com
python scripts/fetch_probe.py --file urls.txt

# 离线分类已保存的 HTML（可复现，便于回归测试）
python scripts/fetch_probe.py --html-dir ./saved_pages
```

分类枚举：`ok` / `captcha` / `forbidden` / `ratelimit` / `timeout` / `conn_error` /
`js_shell` / `paywall` / `login` / `soft404` / `robots` / `too_large` / `error`，
每条附降级路径建议，完整结果写入 `probe_report.json`。

## 已知限制

- 站点特征库是经验性启发式，会过时也会误判；输出是线索而非结论
- 「拦截与客户端相关」基于单次实测，不构成绕过限制的依据
- 脚本只探测不绕过：检测到验证码/付费墙时如实报告并换路径
- 内核判定样本 < 8 篇时必须标注置信度低

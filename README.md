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

## 工作流演示（虚构示例）

> 以下为**虚构演示**：所有名称、网站、人物均为占位符，不指向任何真实网站或真人。
> 用途是让你看到这个工作流每一步的产出物长什么样。

**场景**：用户给了一条指令——"读一下这个数据产品官网和他（某学者）的 Google Scholar 主页，把他们的方法论提炼成一个 skill"。

| 阶段 | 这一步做什么 | 演示产出 |
|---|---|---|
| S0 抽取简报 | 明确提炼什么、不提炼什么 | 提炼"数据看板产品的方法论"；判据＝可检查要素（数据接入 / 指标口径 / 可视化取舍）；不提炼＝团队规模、融资、人脉 |
| S1 取证链 | 官网抓取成功；Scholar 被验证码拦截 → 换路径 | 官网全文 ✅；Scholar ⚠️ 未读取（D 级）；改从其个人学术站补论文清单 |
| S2 来源台账 | 标注实际读到了什么 | 官网 A 级（读到全文）；个人学术站 B 级（仅标题）；Scholar D 级（未抓到，如实记录） |
| S3 结构反推 | 8+ 篇作品拆要素、数频次 | 要素 X 出现 9/10 篇 → 方法内核；要素 Y 出现 3/10 篇 → 边界条件 |
| S4 可迁移性检验 | 方法与资源条件分离 | "他有专有用户数据" → 进"不该照抄"，替代路径＝公开同类指标 + 测量验证 |
| S5 落盘规范与去重 | 探测本机目录与既有 skill | 命名 `data-product-methodology`（能力命名，不用人名）；与既有 skill 写分工表 |
| S6 撰写 | 骨架 → description → references → templates → scripts | 产出完整 skill 目录 |
| S7 产物体检 | 合成数据自检 + 文档-代码同步 + 归属声明 | 脚本用已知 ground truth 数据跑通；文档命令与代码参数逐一核对；ATTRIBUTION 记录抓到/未抓到 |

看完这一行，你就知道每个模板（`extraction_brief` / `source_ledger` / `method_matrix` / `skill_skeleton` / `attribution_block`）应该在什么时候填、填成什么样。

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

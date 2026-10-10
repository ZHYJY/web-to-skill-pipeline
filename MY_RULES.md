# MY_RULES — web-to-skill-pipeline

## Scope

证据 → 方法 → skill 落盘的管线。
**不覆盖** skill 的 eval 与触发优化（归 `skill-creator`）和措辞打磨（归 `writing-skills`）。

## Default workflow

```
S0 抽取简报      明确提炼什么方法、判据是什么、不提炼什么
S1 取证链        抓不到就换路径，不降级成编造
S2 来源台账      A/B/C/D 分级，A 级才能支撑"怎么做"
S3 结构反推      ≥8 篇成组作品，内核门槛 60%
S4 可迁移性检验  分离方法与资源条件，产出"不该照抄"章节
S5 落盘规范与去重 探测目录与既有 skill，写分工表
S6 撰写          骨架 → description → references → templates → scripts
S7 产物体检      合成数据自检 + 文档-代码同步 + 归属声明 + 清理
```

## Standards

- 作品数 < 8 → 标注"内核判定置信度低"
- 要素出现率 < 60% → 不进主流程
- 规则必须三要素齐全：做什么 / 为什么 / 判据
- 规则措辞必须可被检查（"念给同事听，他能判断违反了它吗"）
- 每条方法都要过 S4 五问；不过则进"不该照抄"并给替代路径
- 来源未抓到 → 显式记为 D 级，交付时明说
- 二手来源不得用于推断方法细节

## Anti-patterns（本 skill 专门拦截）

- 第一个 URL 失败就用训练记忆填补
- 只凭标题推断方法设计（越级推断）
- 把"他有专有数据"当成方法提炼给用户
- 只写"照做就行"，不写适用边界
- 未探测落盘目录就写文件
- 与既有 skill 大量重叠却不写分工表
- 脚本从未运行就交付
- 文档写了代码里没有的参数

## Hard boundaries

- 不绕过 CAPTCHA、付费墙或登录墙
- 不伪造抓取结果；未核实就标注"未核实"
- 不把训练记忆当作来源
- 抓取失败必须明说，并给出降级路径

## Division of labour

- `skill-creator`：从意图到 skill + eval + 触发优化
- `writing-skills` / `skill-refiner`：skill 的 TDD 纪律与措辞
- `deep-research` / `finance-scholar-deep-research` / `research-lit`：检索与综述本身
- `summarize`：单 URL 摘要，不做方法提炼
- `find-skills`：安装检索

**判据**：用户已有材料、要沉淀方法 → 本 skill；还在找材料 → 先 deep-research。

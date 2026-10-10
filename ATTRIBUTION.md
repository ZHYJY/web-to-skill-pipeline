# ATTRIBUTION

## 方法来源

本 skill 的流程结构提炼自一次真实工作流的复盘：从两个公开网页（一位学者的机构主页与
Google Scholar 个人主页）提炼其发表方法论，产出 `finance-top-journal-cao-pipeline` skill。

那次实践中暴露出的六个具体故障，构成本 skill 的核心内容：

| 实测问题 | 对应本 skill 的条款 |
|---|---|
| Google Scholar 返回人机验证，主源中断 | S1 取证链降级顺序 |
| 同一 URL 换客户端又能拿到页面，且是 JS 渲染 | S1 规则一、规则二 |
| 只有部分论文读到摘要，其余仅标题 | S2 A/B/C/D 分级 |
| 履历页显示的方法与该学者的资源条件混在一起 | S4 可迁移性检验 |
| 本机已有 15+ 同域 finance skill，需避免重复 | S5 去重与分工表 |
| 产出脚本存在"成本越高净值越高"等语义 bug | S7 合成数据自检 |

## 引用来源

| 来源 | URL | 用途 | 抓取结果 |
|---|---|---|---|
| UMD Smith 教师页 | https://www.rhsmith.umd.edu/directory/sean-cao | 方法论原始素材 | ✅ 成功 |
| 个人学术站 | https://sites.google.com/view/seancao/home | 论文清单补全 | ✅ 成功 |
| Google Scholar | https://scholar.google.com/citations?user=vIECdakAAAAJ&hl=en | 论文元数据 | ⚠️ 抓取工具被拦截；标准 HTTP 客户端可拿到页面但论文列表为 JS 渲染，内容不可用 |

## 准确性边界

- 本 skill 提炼的是**工作流结构**，不包含被观察者的方法论内容本身。
- `scripts/fetch_probe.py` 的站点特征库（`MARKERS`、`JS_RENDERED_HINTS`）是**经验性启发式**，
  会过时，也会误判。脚本输出是**线索而非结论**，最终判断必须由人确认。
- 分类阈值（可见文本 500 字符、HTML 20000 字节、3MB 上限）为经验值，非通用标准。
- 「拦截与客户端相关」这一观察基于单次实测，可能随时间、IP、地区而变化，
  不应作为绕过限制的依据。

## 版权声明

- 未复制任何来源网页的正文内容。
- URL 与站点名称属事实性引用。
- 引用的论文标题仅为说明信息来源，属事实性引用。

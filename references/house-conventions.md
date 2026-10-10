# S5 落盘规范探测与去重

## 目录

- [1. 为什么要先探测](#1-为什么要先探测)
- [2. 探测四件事](#2-探测四件事)
- [3. 目录结构规范](#3-目录结构规范)
- [4. frontmatter 约定](#4-frontmatter-约定)
- [5. 去重：最容易被跳过的一步](#5-去重最容易被跳过的一步)
- [6. 命名规则](#6-命名规则)
- [7. 验证](#7-验证)

---

## 1. 为什么要先探测

同一个机器上可能存在**多个 skill 目录**，且约定不同：

```
~/.agents/skills/          ← 用户级，可能被多个 agent 加载
<dataDir>/skills/          ← 运行时级
<dataDir>/.builtin-skills/ ← 内置，只读
<dataDir>/v2/plugin-cache/ ← 插件附带
```

写错目录的后果：新 skill 不被加载；或与内置 skill 同名冲突。

**更隐蔽的后果**：不探测同级 skill 的结构，你会用一套自创格式写，而旁边的 skill 用另一套——用户维护成本翻倍。

---

## 2. 探测四件事

### 2.1 skill 装在哪

```
1. 列出各候选目录下的 SKILL.md
2. 确认哪些目录是用户可写的
3. 确认新 skill 放哪里才会被加载
```

**快速判定**：加载一个同级 skill，看它返回的 `Location:` 路径，那个位置就是生效目录。

### 2.2 同级 skill 的目录结构

看 2–3 个同级 skill 的文件构成，选一个作为格式参照。常见结构：

```
skill-name/
├── SKILL.md          （必需）
├── MY_RULES.md       （执行规范）
├── ATTRIBUTION.md    （来源与版权）
├── README.md
├── skill.json
├── references/       （深度内容，按需加载）
├── templates/        （需要用户填的表单）
├── scripts/          （确定性可复用逻辑）
└── prompts/ / examples/ / assets/
```

### 2.3 frontmatter 字段

对齐同级 skill 常用字段：

```yaml
---
name: skill-name
description: "Use when ...（写触发场景，不写工作流内容）"
license: MIT
platforms: [windows, linux, macos]
version: "1.0.0"
---
```

### 2.4 内容语言

中文 skill 内部通常中文为主、论文/代码类术语保留英文。看同级 skill 的实际写法再定。

---

## 3. 目录结构规范

### 渐进式披露（三层加载）

| 层 | 内容 | 常驻？ | 体量建议 |
|---|---|---|---|
| 1 | frontmatter（name + description） | 总是 | ~100 词 |
| 2 | SKILL.md 正文 | 触发时 | < 500 行 |
| 3 | references / scripts / templates | 按需 | 无限 |

**规则**：SKILL.md 只放**路由 + 原则 + 判据**，深度内容外置到 references，并明确写"什么时候读它"。

**反面模式**：把 3000 行参考资料塞进 SKILL.md，导致触发时占用大量上下文，且真正需要的部分被淹没。

---

## 4. frontmatter 约定

### description 是触发机制

- 模型**倾向于不用 skill**，所以描述要**推力足**
- 写清：做什么 + 什么时候用 + 用户会说的原话
- **不要**总结工作流内容（那是正文的事）
- 控制在 500 字符内更稳妥

**好例**：
> Use when the user gives a URL / 网页 / 论文列表 and asks to turn it into a skill —— 例如『读这个网页给我做一个 skill』。覆盖取证链搭建、被验证码拦截时的降级路径、来源可靠性分级、方法反推。用户提到 网页提取、方法论提炼、沉淀成 skill 时都应使用。

**坏例**：
> A skill that helps you research things and write skills.（模型无法判断何时触发）

---

## 5. 去重：最容易被跳过的一步

同域 skill 堆积到十几个时，**缺的不是新 skill，是路由表**。

### 去重三步

1. **列出可能重叠的 skill**：按领域关键词搜（如 `finance`、`research`、`paper`）
2. **逐个读它们的 description**，判断边界
3. **写分工表**放进新 skill 的 SKILL.md

### 分工表模板

```markdown
## 与其他 skill 的分工

- `A`：负责 X。本 skill 覆盖它之前的 Y 环节
- `B`：负责 Z。本 skill 与它互补，典型分工是……

**分工判据**：<一句话说清什么时候用哪个>
```

### 什么时候不该新建 skill

| 情况 | 该做 |
|---|---|
| 已有 skill 覆盖 90%，只差一点 | 改已有 skill |
| 只是某个已有 skill 的一个阶段 | 在已有 skill 里加一节 |
| 同域已有 5+ 个 skill | 优先写路由表，而非新增 |
| 需求一次性的 | 不建 skill，直接做 |

---

## 6. 命名规则

| 规则 | 说明 |
|---|---|
| 用**能力**命名 | `behavioral-finance-top-journal` 而非 `cao-pipeline` |
| 方法确由某人定义时**可带出处** | 如 `finance-top-journal-cao-pipeline`，但须在 ATTRIBUTION 写清 |
| 小写 + 连字符 | 无括号、无空格、无特殊字符 |
| 避免与既有 skill 高度重合 | 加载列表会变得难扫 |
| 名字与 description 呼应 | 看到名字能猜出大致用途 |

---

## 7. 验证

落盘后逐项确认：

```
[ ] 目录放对了位置（对照一个已加载的同级 skill）
[ ] 文件结构与同级 skill 一致
[ ] frontmatter 能被解析（name / description 齐全）
[ ] SKILL.md 中引用的每个文件真实存在
[ ] scripts 能通过 --help / 语法检查
[ ] 与既有 skill 的分工表已写入
[ ] 没有测试产物、缓存、临时文件残留
```

**最有效的一条**：在会话中实际加载一次新 skill。若能加载并返回完整内容，说明路径与格式都对。

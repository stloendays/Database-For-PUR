# Database-For-PUR

面向聚氨酯（PU/PUR/HMPUR）研究的可追溯结构化知识数据库，重点整合中文论文、硕博论文、中国专利、标准、企业技术资料、行业报告，以及已整理的英文论文/专利/开放数据。

本仓库的目标不是“收集 PDF”，而是把公开资料中的 **配方（Formulation）→ 原料（Material）→ 工艺（Process）→ 测试条件（Condition）→ 性能（Measurement）→ 原始证据（Evidence）** 标准化，供 SQL、RAG、机器学习和 inverse design 使用。

## 当前底座

由既有 HMPUR 数据库迁移而来，当前已包含：

- Sources: 21
- Standardized formulations: 85
- Formulation components: 278
- Property/performance observations: 547
- Protocols: 22
- Temperature-viscosity points: 4,559
- Descriptor records: 1,599
- PU Tg ML samples: 226

这些数据会保留原始 `source_id`、证据定位和来源链接，并逐步迁移到 PUR-CN v1 统一 schema。

## 科学问题

数据库优先支持以下研究问题：

1. polyol blend 的微小性质差异是否在 MDI prepolymer 阶段被系统性放大；
2. amplification factor 是否受 blend composition 调制；
3. 简单加性 mixing law 在何种条件下失效；
4. 反应前 blend viscosity、NCO/OH、polyol chemistry、reaction history 与最终 melt viscosity / open time / green strength / adhesion 之间的关系；
5. 给定目标物性后，如何从有证据约束的 formulation/process 空间进行 inverse design。

## 数据模型

```text
Source
  -> Experiment
      -> Formulation
          -> Formulation Component
              -> Material Master
      -> Process Step
      -> Measurement
      -> Evidence
```

核心原则：

- **实验级而非文献级**：一篇论文/专利可拆成多个 experiment/formulation。
- **证据可追溯**：关键记录必须保留 `source_id`、`evidence_locator`、`source_url`。
- **原始值不丢失**：标准化值与原始值/原始单位同时保存。
- **缺失不等于 0**：未披露组成或条件必须显式标记为 missing/not disclosed。
- **测试条件不可混用**：温度、时间、基材、固化时间、测试标准等进入 condition layer。
- **实施例优先**：专利中的 measured example / comparative example 与 claimed range 分开建模。

## 仓库结构

```text
Database-For-PUR/
├─ data/
│  ├─ legacy/              # 既有 HMPUR 标准化数据迁移
│  ├─ cn/                  # 中文来源结构化记录
│  ├─ master/              # material/terminology/property 主表
│  └─ rag/                 # RAG 文档与索引输入（不公开受限全文）
├─ schema/
│  └─ pur_cn_v1.sql        # 统一 SQLite schema
├─ scripts/
│  ├─ build_database.py    # CSV -> SQLite
│  ├─ validate_database.py # 数据完整性与证据约束检查
│  └─ export_ml.py         # 面向建模的导出
├─ docs/
│  ├─ DATA_DICTIONARY.md
│  ├─ EVIDENCE_POLICY.md
│  └─ ROADMAP.md
└─ .github/workflows/
   └─ validate.yml
```

## 中文资料范围

计划纳入：

- 中文期刊论文
- 硕士/博士论文
- 中国专利（CN）与同族 WO/US/EP 专利
- GB / GB-T / HG-T / 行业标准
- 企业 TDS/SDS/产品手册
- 行业报告与会议资料
- 可合法再分发的开放数据集

> 版权说明：本仓库默认**不公开上传受版权保护的论文/学位论文全文**。公开仓库存储结构化事实、元数据、可公开链接、短证据定位与合法开放资料；原始受限文档应由使用者在本地维护。

## Evidence level

- **A** — 完整配方 + 工艺 + 测试条件 + 定量结果，可定位原始证据。
- **B** — 配方和定量结果完整，但部分测试条件/工艺缺失。
- **C** — 只有部分配方、范围或间接定量信息。
- **D** — 综述、二手引用、宣传资料或仅用于背景知识。

专利 additionally 区分：

`measured` / `example` / `comparative_example` / `reported` / `recommended_range` / `claimed_range` / `inferred` / `digitized_from_figure`。

## RAG / Agent 使用原则

Agent 返回候选配方或数值时，至少同时返回：

- `source_id`
- `experiment_id`（若存在）
- `evidence_locator`
- `source_url`
- `quality_level`
- `evidence_type`

推荐检索流程：

```text
SQL metadata filtering
  -> keyword/FTS recall
  -> vector recall
  -> reciprocal rank fusion
  -> evidence-grounded answer
```

## 数据库构建

```bash
python scripts/build_database.py --output database/pur_master.db
python scripts/validate_database.py database/pur_master.db
```

## 状态

当前处于 **v0.1 migration + v1 schema construction**。下一阶段优先补充中文 PUR/HMPUR 专利、硕博论文和反应前/反应后黏度数据。

# TiAI · Material-state resolution

Numerical reproduction package for **TiAI: Making Material States Count in Literature-Driven Design of Titanium Alloys and Titanium Matrix Composites**.

This repository contains the released inputs, analysis code and recorded results of nine analyses of literature-derived titanium-alloy and titanium-matrix-composite properties. Use the figure index below to move from a manuscript result to its code and Source Data.

**[Start here](#start-here) · [Run the analyses](#quick-start) · [Find a figure](#figure-to-code-and-data) · [Evaluation conditions](#evaluation-conditions)**

中文入口：按下表查找**代码、源数据、图号和复算命令**。[数据字典](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/说明/数据字典.md)说明字段、统计分母、运行目录名称及适用条件。

## Start here

| I want to… | Direct entry |
| --- | --- |
| Understand what is included | [Data guide](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/说明/数据字典.md) · [Access and release scope](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/说明/数据访问范围.md) |
| Run the released numerical analyses | [Quick start](#quick-start) · [Numerical reproduction entry](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/数值复现入口.py) |
| Find the inputs or recorded outputs for a figure | [Figure-to-code-and-data index](#figure-to-code-and-data) · [All released data](https://github.com/TiAI-Materials/tiai-material-state-reproduction/tree/main/数据/) |
| Check the recorded reproduction reports | [Recorded numerical results](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/数值复现结果.json) |
| Restore and verify the runtime files | [Restore script](https://github.com/TiAI-Materials/tiai-material-state-reproduction/tree/main/代码/恢复运行目录.py) · [File-integrity checker](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/文件完整性核对.py) · [Repository manifest](https://github.com/TiAI-Materials/tiai-material-state-reproduction/tree/main/复现文件清单.json) |
| Inspect the extraction benchmark | [Tasks and instructions](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/科研抽取任务与提示.jsonl) · [Reference annotations](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/科研抽取参考标注.jsonl) · [Saved predictions](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/科研抽取保存预测.jsonl) · [Scoring protocol](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/文献抽取评分协议.py) |
| Cite or reuse the release | [Citation](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/CITATION.cff) · [Code licence](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/LICENSE) · [Data licence](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/说明/数据许可.md) · [Release notes](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/说明/发布范围.md) |

## Requirements

- Python 3.12 or 3.13.
- An NVIDIA GPU with CUDA; the numerical comparisons run on the GPU in float64.
- NumPy, pandas, PyTorch with CUDA support, PyArrow and Matplotlib; see [environment requirements](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/说明/环境依赖.txt).

The recorded results were obtained with Python 3.13.13, PyTorch 2.11.0+cu128 and CUDA 12.8 on an NVIDIA GeForce RTX 5080 Laptop GPU, on which `materials` takes about a minute and the other two commands a few seconds each.

## Quick start

Run these commands from the repository root:

```bash
python 代码/恢复运行目录.py runtime
cd runtime
python -m pip install -r requirements.txt
python tools/validate_release.py
python tools/reproduce_analysis.py --analysis materials
python tools/reproduce_analysis.py --analysis saved-models
python tools/reproduce_analysis.py --analysis target-plane
```

Repository files use descriptive Chinese names. The restore script checks each file and writes the original runtime layout under `runtime/`, including `tools/`, `data/` and `paper01/`. The [data guide](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/说明/数据字典.md) maps those runtime names to manuscript figures and tables.

`validate_release.py` confirms file integrity and checks the composition of the selection cohort. Each reproduction command recomputes quantities from the released inputs, compares them with the released Source Data within the tolerances stated in the code, and writes `results/<analysis>/report.json`. It stops at the first difference outside tolerance. The [recorded reports](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/数值复现结果.json) remain distinct from reports produced by a new run.

The `materials` command runs seven modes: `material-relations`, `associations`, `microstructure`, `temporal`, `frontier`, `addition-maps` and `dose`. The other two modes have their own commands above. To run one mode, replace the analysis name with the exact mode listed below:

```bash
python tools/reproduce_analysis.py --analysis material-relations
```

## Figure to code and data

Each row identifies an existing numerical analysis. Data links include the analysis inputs and reference outputs; their individual roles and statistical units are defined in the [data guide](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/说明/数据字典.md).

| Manuscript | Mode and recomputed quantities | Analysis code | Inputs and reference results |
| --- | --- | --- | --- |
| **Figure 4** | `material-relations`: equal-source strength–elongation covariance moments and primary 2,000-draw within-source intervals | [Strength–elongation functions](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/图4强塑关系函数.py) | [Paired states](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图4强塑配对状态.csv) · [Primary intervals](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图4主协议区间.json) · [Variance decomposition](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图4来源方差分解.json) |
| **Figure 5** | `associations`: within- and between-source rank effects, 500-draw intervals, leave-one-source-out estimates, random-effects summaries and false-discovery-rate control | [Association functions](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/关联统计函数.py) | [Admitted analysis units](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图5来源准入单元.csv) · [Cell statistics](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图5关联单元统计.csv) · [Sampling protocol](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图5抽样协议.json) |
| **Figure 6** | `microstructure`: six same-record descriptor–property coordinate sets | [Same-record coordinate functions](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/图6同记录坐标函数.py) | [Coordinates](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图6组织性能坐标.csv) · [Population definitions](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图6总体定义.json) |
| **Figure 7a–g** | `temporal`: five-year endpoint windows and 300-draw source-bootstrap intervals | [Temporal-window functions](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/图7时间窗统计函数.py) | [Admitted observations](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图7时间窗准入观测.csv) · [Window statistics](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图7时间窗统计.csv) |
| **Figure 7h–j** | `frontier`: observed Pareto membership, dated hypervolume, 400 source-balanced portfolios and the 81 × 81 attainment grid | [Frontier-analysis functions](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/图7前沿分析函数.py) | [Paired states](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图7前沿同态配对状态.csv) · [Population and protocol](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图7前沿总体与协议.json) · [Statistics](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图7前沿统计.csv) |
| **Figure 8a–f** | `saved-models`: metrics and error distributions of five property models on 4,808 qualified saved queries | [Metrics and query qualification](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/五目标模型指标与查询资格.py) | [Saved point predictions](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/五性能模型保存点预测.csv) · [Model register](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/五性能模型评估登记.csv) · [Query qualification](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/五目标查询来源资格.json) |
| **Figure 8g–l** | `target-plane`: the 40,401-cell strength–elongation target plane for 913 candidates from 168 sources | [Target-plane replay](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/目标阈值平面复算.py) · [Selection functions](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/选择分析函数.py) | [Held-out decisions](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/来源留出筛选决策.csv) · [Target-plane definition](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图8目标平面定义.json) · [Complete target plane](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/图8完整目标阈值平面.csv) · [Candidate qualification](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/选择候选来源资格.json) |
| **Figures 9 and 10** | `addition-maps`: designed-series selection, source medians, 4,000-draw intervals and reinforcement-content bins | [Addition-map functions](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/材料剂量地图数值函数.py) | [Designed-series summary](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/设计系列添加响应汇总.csv) · [All-series summary](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/全系列添加响应汇总.csv) · [Reinforcement coordinates](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/增强体含量坐标.csv) · [Recorded map results](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/添加量地图数值记录.json) |
| **Figure S11** | `dose`: regressions of 3,646 dose series, source summaries and 2,000-draw intervals for 536 summary cells | [Dose-analysis entry](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/材料剂量运行入口.py) | [Series points](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/材料剂量系列点.csv.gz) · [Series](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/材料剂量系列.csv.gz) · [Source effects](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/材料剂量来源效应.csv.gz) · [Effect summaries](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/材料剂量效应汇总.csv) |

All modes are coordinated by the [numerical reproduction entry](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/数值复现入口.py). [Figure S12 source-reviewed dose points](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/原文人工核对剂量点.csv) and [derived contrasts](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/原文剂量派生对比.csv) are also available; their scope is documented in the data guide.

## Evaluation conditions

- The five property models are evaluated on saved predictions under the recorded protocols of Figure 8a–f and Table S3. Those protocols use same-source or labelled target-source support. This package does not retrain the models.
- The target plane and selection tables use the recorded outcomes of the fixed cohort of 913 candidates from 168 sources, under the stated single-choice setting. Outcome-informed opportunity and input-group references are retrospective diagnostics.
- Source extraction, source adjudication and model training use licensed full texts. They are described in the Supporting Information and are not reproduced by this package.
- The complete curated corpus and figure rendering are outside the release. The files here support the nine listed numerical analyses, rather than an end-to-end reproduction of every manuscript component.

## Extraction benchmark

The [tasks and instructions](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/科研抽取任务与提示.jsonl), [reference annotations](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/科研抽取参考标注.jsonl) and [parsed saved outputs](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/数据/科研抽取保存预测.jsonl) document the extraction benchmark in Table S1 and Section S2. Source documents are identified by DOI and are not distributed. The [scoring code](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/代码/文献抽取评分协议.py) implements the generic scoring rules; the data guide explains the source-scoped projection and adapter boundary.

## Licence and citation

The code is released under the [MIT License](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/LICENSE). The authors' curation, annotations and numerical results are released under [CC BY 4.0](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/说明/数据许可.md) to the extent of the authors' rights. Measurements remain attributed to their original publications through the DOIs in each table. Please cite [this release](https://github.com/TiAI-Materials/tiai-material-state-reproduction/blob/main/CITATION.cff) together with the original studies whose measurements you use.

Documentation navigation updated **9 November 2026**. The scientific release remains **1.0.2**: this navigation change does not alter numerical inputs, algorithms, saved predictions, evaluation cohorts or recorded scientific results.


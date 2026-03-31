# CSKG4APT-CTI

基于 [CSKG4APT](https://github.com/peng-gao-lab/CSKG4APT) 框架的 **APT 威胁情报知识图谱构建平台**。

利用大语言模型 (LLM) 从非结构化威胁情报文本中自动提取实体与关系，构建网络安全知识图谱 (CSKG)，并支持 APT 组织归因分析。

## 核心功能

- **知识提取** — 从 CTI 报告中自动提取 12 类实体 + 7 类关系
- **本体约束** — 基于 CSKG4APT 论文定义的本体 Schema，Pydantic 强类型校验
- **APT 归因** — 威胁卡片生成、攻击链复原、钻石模型分析
- **图谱可视化** — Pyvis 交互式网络图
- **多 LLM 支持** — OpenAI / Gemini / Claude / Ollama / 通义千问 / 智谱 / DeepSeek 等
- **图数据库** — 可选 Neo4j 持久化存储

## 本体定义

**12 种实体类型：** Attacker, Infrastructure, Malware, Vulnerability, Assets, Target, Event, Behavior, Time, Tool, Credential, Indicator

**7 种关系类型：** has, uses, exploit, exist, target, medium, behavior

## 项目结构

```
CSKG4APT-CTI/
├── cskg4apt/                  # CSKG4APT 框架核心代码
│   ├── cskg4apt/              # Python 包
│   │   ├── app.py             # Gradio Web UI
│   │   ├── cskg4apt_extractor.py  # LLM 知识提取器
│   │   ├── cti_processor.py   # CTI 处理 pipeline (IE→ET→EA→LP)
│   │   ├── llm_processor.py   # LLM 调用封装
│   │   ├── graph_constructor.py   # 图谱构建与可视化
│   │   ├── attribution/       # APT 归因模块
│   │   ├── graph_db/          # Neo4j 图数据库
│   │   ├── schemas/           # 本体定义 (Pydantic)
│   │   └── prompts/           # LLM Prompt 模板 (Jinja2)
│   ├── tests/                 # 测试用例
│   ├── docs/                  # 框架文档
│   ├── pyproject.toml         # 包配置
│   └── requirements.txt       # 依赖
├── start_cskg4apt.py          # 快速启动脚本
├── docs/                      # 设计文档
│   ├── CTINexus_CSKG4APT融合改造方案.md
│   └── 使用说明_CTINexus_CSKG4APT.md
└── references/                # 参考论文
    └── CSKG4APT_paper_2023.pdf
```

## 快速开始

### 安装

```bash
cd cskg4apt
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e .
```

### 配置

```bash
cp cskg4apt/.env.example cskg4apt/.env
# 编辑 .env 填入你的 API Key
```

### 运行

```bash
# 启动 Web UI
python start_cskg4apt.py

# 或直接使用 CLI
cskg4apt --input-file report.txt --provider openai --model gpt-4o
```

### Python API

```python
from cskg4apt import process_cti_report
from dotenv import load_dotenv

load_dotenv()

result = process_cti_report(
    text="APT29 used PowerShell to download malware from C2 server at 192.168.1.100...",
    provider="openai",
    model="gpt-4o",
)

print(result["entity_relation_graph"])  # 交互式图谱 HTML 路径
```

## 技术栈

| 技术 | 用途 |
|------|------|
| LiteLLM | 多 LLM 统一调用 |
| Gradio | Web UI |
| Pyvis + NetworkX | 图可视化 + 图算法 |
| Pydantic | Schema 校验 |
| Neo4j (可选) | 图数据库 |
| Jinja2 | Prompt 模板 |
| Hydra / OmegaConf | 配置管理 |

## 参考文献

- Ren et al. (2023). *CSKG4APT: A Cybersecurity Knowledge Graph for Advanced Persistent Threat Organization Attribution.*
- Cheng et al. (2025). *CSKG4APT: Automatic Cyber Threat Intelligence Knowledge Graph Construction Using Large Language Models.* IEEE EuroS&P 2025.

## License

MIT

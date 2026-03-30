# CTINexus × CSKG4APT 融合改造方案
## LLM驱动的下一代APT威胁情报知识图谱系统

> **设计理念**：保留CSKG4APT的严谨本体设计与钻石模型归因能力，用现代LLM技术彻底替代传统深度学习"炼丹"流程，打造可解释、可推导、工程化落地的威胁情报图谱系统。

---

## 📋 改造概览

### 原CSKG4APT系统痛点
| 模块 | 原技术方案 | 核心问题 |
|------|-----------|---------|
| 实体提取 | BERT-BiLSTM-GRU-CRF | 需要大量标注数据训练，黑盒不可解释 |
| 数据采集 | Scrapy-Redis分布式爬虫 | 易被封禁，维护成本高 |
| 图谱存储 | OrientDB | 生态较小，社区支持弱 |
| 关系推理 | 图遍历查询 | 缺少自动化推演能力 |

### CTINexus现有优势
✅ 四阶段可扩展流水线（IE → ET → EA → LP）
✅ 多模态PDF处理（文本+图像视觉分析）
✅ 多LLM提供商支持（OpenAI/Gemini/Claude/Ollama）
✅ API嵌入模型集成（高质量向量对齐）
✅ Gradio可视化前端（深色科技主题UI）

### 融合改造核心目标
🎯 **本体约束**：引入CSKG4APT的12实体+7关系严格定义
🎯 **白盒提取**：用LLM零样本学习替代BERT四层神经网络
🎯 **强制溯源**：每个三元组必须附带原文证据链
🎯 **图谱持久化**：集成Neo4j替代内存NetworkX
🎯 **威胁归因**：实现钻石模型自动APT组织画像
🎯 **自动采集**：Playwright爬虫引擎（可选）

---

## 🏗️ 改造架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│  输入层 (Input Layer)                                            │
│  • URL爬取 (Playwright自动采集)                                  │
│  • PDF上传 (多模态文本+图像)                                      │
│  • 文本粘贴 (直接输入)                                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│  阶段一：本体约束实体提取 (CSKG4APT-Guided IE)                    │
│  • Pydantic强类型Schema (12种实体类型严格定义)                    │
│  • LLM Prompt工程 (零样本提取 + 强制原文溯源)                     │
│  • 滑动窗口分块处理 (解决超长文本遗忘问题)                        │
│  输出: List[Entity] with derivation_source                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│  阶段二：关系三元组提取 (CSKG4APT-Guided ET)                     │
│  • Pydantic关系Schema (7种关系类型约束)                          │
│  • LLM上下文推理 (理解实体间语义关联)                            │
│  • JSON结构化输出 (source-relation-target + evidence)            │
│  输出: List[Relation] with derivation_source                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│  阶段三：实体对齐与消歧 (Enhanced EA)                             │
│  • API嵌入向量 (text-embedding-3-large高质量语义表示)            │
│  • 余弦相似度聚类 (APT28 = Sofacy = Fancy Bear)                 │
│  • 别名映射表维护 (自动构建组织/工具别名库)                       │
│  输出: Merged Entity Graph                                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│  阶段四：Neo4j图谱持久化 (Graph Database Integration)            │
│  • Cypher MERGE写入 (自动去重节点)                               │
│  • 证据链存储 (关系边附带derivation_source属性)                  │
│  • 时序索引 (支持历史溯源查询)                                    │
│  输出: Neo4j Knowledge Graph                                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│  阶段五：钻石模型威胁归因 (Diamond Model Attribution)             │
│  • 四维度画像查询 (Adversary/Victim/Capability/Infrastructure)   │
│  • 多跳路径推演 (未知样本 → 木马家族 → APT组织)                   │
│  • LLM总结报告 (自然语言生成归因分析)                             │
│  输出: APT Organization Profile                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 阶段一：本体约束实体提取 (CSKG4APT-Guided IE)

### 设计逻辑
保留CSKG4APT论文定义的12种实体类型作为**硬约束**，但用LLM的零样本学习能力替代传统BERT四层神经网络，彻底解决标注数据依赖和黑盒问题。

### 1.1 强类型Schema定义

**新建文件**: `ctinexus/schemas/cskg4apt_ontology.py`

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal, List, Optional
from enum import Enum

class EntityType(str, Enum):
    """CSKG4APT定义的12种实体类型"""
    ATTACKER = "Attacker"                    # 攻击者/APT组织
    ATTACK_PATTERN = "Attack_pattern"        # 攻击模式/战术
    MALWARE = "Malware"                      # 恶意软件/木马
    VULNERABILITY = "Vulnerability"          # 漏洞 (CVE)
    TARGET = "Target"                        # 目标/受害者
    INFRASTRUCTURE = "Infrastructure"        # 基础设施 (C2/IP/域名)
    SOFTWARE_TOOLS = "Software_tools"        # 软件/工具
    ASSETS = "Assets"                        # 资产
    CAMPAIGN = "Campaign"                    # 攻击活动
    IMPACT = "Impact"                        # 影响
    DEFENSIVE_STRATEGY = "Defensive_strategy" # 防御策略
    REPORTS = "Reports"                      # 报告

class RelationType(str, Enum):
    """CSKG4APT定义的7种关系类型"""
    LOAD = "load"                # 加载 (木马加载模块)
    EXPLOIT = "exploit"          # 利用 (组织利用漏洞)
    LAUNCH = "launch"            # 发起 (组织发起活动)
    HAVE = "have"                # 拥有 (组织拥有工具)
    BELONGS_TO = "belongs_to"    # 属于 (活动属于组织)
    EXIST = "exist"              # 存在 (漏洞存在于资产)
    MEDIUM = "medium"            # 媒介 (基础设施作为媒介)

class CSKG4APTEntity(BaseModel):
    """强类型实体定义 - 每个字段都有验证"""
    id: str = Field(
        description="实体唯一标识符，如 'APT28', 'CVE-2017-0143', 'Zebrocy'"
    )
    type: EntityType = Field(
        description="实体类型，必须是CSKG4APT定义的12种类型之一"
    )
    derivation_source: str = Field(
        description="提取该实体的原文片段，用于白盒溯源和可解释性验证",
        min_length=10
    )
    confidence: float = Field(
        default=1.0,
        description="提取置信度 (0-1)",
        ge=0.0,
        le=1.0
    )
    attributes: Optional[dict] = Field(
        default=None,
        description="实体额外属性，如攻击者的国家归属、木马的编程语言等"
    )

    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """验证ID格式规范性"""
        if not v or len(v.strip()) == 0:
            raise ValueError("实体ID不能为空")
        # CVE格式验证
        if v.startswith("CVE-"):
            import re
            if not re.match(r'^CVE-\d{4}-\d{4,}$', v):
                raise ValueError(f"CVE格式错误: {v}")
        return v.strip()

class CSKG4APTRelation(BaseModel):
    """强类型关系定义"""
    source_entity_id: str = Field(
        description="源实体ID (主语)"
    )
    target_entity_id: str = Field(
        description="目标实体ID (宾语)"
    )
    relation_type: RelationType = Field(
        description="关系类型，必须是CSKG4APT定义的7种类型之一"
    )
    derivation_source: str = Field(
        description="提取该关系的原文语句，必须同时包含源实体和目标实体的上下文",
        min_length=20
    )
    confidence: float = Field(
        default=1.0,
        description="关系置信度 (0-1)",
        ge=0.0,
        le=1.0
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="关系发生的时间信息（如果能从文本提取）"
    )

class ExtractionResult(BaseModel):
    """LLM提取的完整结果"""
    entities: List[CSKG4APTEntity]
    relations: List[CSKG4APTRelation]
    metadata: dict = Field(
        default_factory=dict,
        description="元数据：如处理时间、模型版本、文本来源等"
    )
```

### 1.2 LLM Prompt工程 - 零样本实体提取

**修改文件**: `ctinexus/prompts/ie_prompts.py`

```python
CSKG4APT_IE_SYSTEM_PROMPT = """你是一个专业的网络威胁情报分析专家，专门从安全报告中提取结构化的APT攻击知识。

**你的任务**：
从给定的威胁情报文本中，提取符合CSKG4APT本体定义的实体和关系。

**严格约束 - 12种实体类型**：
1. Attacker: APT组织/黑客团伙 (如 APT28, Lazarus Group)
2. Attack_pattern: 攻击模式/战术 (如 Spear Phishing, Watering Hole)
3. Malware: 恶意软件/木马 (如 Zebrocy, WannaCry)
4. Vulnerability: 漏洞 (必须是CVE编号，如 CVE-2017-0143)
5. Target: 目标/受害者 (如 政府机构, 能源行业)
6. Infrastructure: 基础设施 (如 C2服务器IP、域名)
7. Software_tools: 软件/工具 (如 Mimikatz, PsExec)
8. Assets: 资产 (如 Windows Server, Oracle数据库)
9. Campaign: 攻击活动 (如 Operation Aurora)
10. Impact: 影响 (如 数据泄露, 服务中断)
11. Defensive_strategy: 防御策略 (如 网络隔离, 多因素认证)
12. Reports: 报告 (如 FireEye APT28报告)

**严格约束 - 7种关系类型**：
1. load: 加载关系 (如 木马A加载模块B)
2. exploit: 利用关系 (如 APT28利用CVE-2017-0143)
3. launch: 发起关系 (如 Lazarus发起Operation XYZ)
4. have: 拥有关系 (如 APT28拥有Zebrocy木马)
5. belongs_to: 属于关系 (如 Operation XYZ属于APT28)
6. exist: 存在关系 (如 CVE-2017-0143存在于Windows Server)
7. medium: 媒介关系 (如 使用IP 1.2.3.4作为C2)

**强制要求**：
1. 每个提取的实体必须附带原文依据 (derivation_source)
2. 每个提取的关系必须附带包含两个实体的完整语句
3. 实体ID必须使用原文中的确切名称 (保持大小写)
4. CVE漏洞必须使用标准格式 (CVE-YYYY-NNNNN)
5. 如果无法确定实体类型，宁可不提取

**输出格式**：
严格返回JSON格式，符合ExtractionResult schema。
"""

CSKG4APT_IE_USER_PROMPT = """请分析以下威胁情报文本，提取所有符合CSKG4APT本体定义的实体和关系：

**输入文本**：
{text}

**输出要求**：
1. 仔细识别文本中的所有12种实体类型
2. 推断实体之间的7种关系类型
3. 每个实体和关系都必须附带原文证据
4. 以JSON格式返回，字段名严格匹配ExtractionResult schema

请开始提取：
"""

# 滑动窗口分块提示词（处理超长文本）
CSKG4APT_CHUNK_MERGE_PROMPT = """你现在收到了同一篇威胁情报报告的多个分块提取结果。

**你的任务**：
合并这些结果，消除重复，并修复跨分块边界的实体/关系。

**输入**：
{chunk_results}

**输出**：
返回合并后的ExtractionResult JSON。
"""
```

### 1.3 修改IE引擎 - 集成CSKG4APT约束

**修改文件**: `ctinexus/graph_constructor.py`

```python
from .schemas.cskg4apt_ontology import (
    CSKG4APTEntity,
    CSKG4APTRelation,
    ExtractionResult,
    EntityType,
    RelationType
)
from .prompts.ie_prompts import (
    CSKG4APT_IE_SYSTEM_PROMPT,
    CSKG4APT_IE_USER_PROMPT,
    CSKG4APT_CHUNK_MERGE_PROMPT
)

class CSKG4APTIntelligenceExtractor:
    """CSKG4APT本体约束的LLM实体提取器"""

    def __init__(self, config: DictConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_with_sliding_window(
        self,
        text: str,
        window_size: int = 1000,
        overlap: int = 200
    ) -> ExtractionResult:
        """滑动窗口分块提取（解决LLM上下文遗忘）"""

        # 1. 按Token分块
        chunks = self._split_text_into_chunks(text, window_size, overlap)
        self.logger.info(f"文本分割为 {len(chunks)} 个分块")

        # 2. 逐块提取
        chunk_results = []
        for i, chunk in enumerate(chunks):
            self.logger.info(f"处理分块 {i+1}/{len(chunks)}")

            chunk_result = self._extract_single_chunk(chunk)
            chunk_results.append(chunk_result)

        # 3. 合并去重
        merged_result = self._merge_chunk_results(chunk_results)

        return merged_result

    def _extract_single_chunk(self, text: str) -> ExtractionResult:
        """单个分块的LLM提取"""

        messages = [
            {"role": "system", "content": CSKG4APT_IE_SYSTEM_PROMPT},
            {"role": "user", "content": CSKG4APT_IE_USER_PROMPT.format(text=text)}
        ]

        # 强制JSON Schema输出
        response = litellm.completion(
            model=self._get_model_id(),
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "extraction_result",
                    "schema": ExtractionResult.model_json_schema(),
                    "strict": True
                }
            },
            temperature=0.1  # 降低随机性，提高一致性
        )

        # 解析并验证
        result_json = json.loads(response.choices[0].message.content)
        validated_result = ExtractionResult(**result_json)

        return validated_result

    def _merge_chunk_results(
        self,
        chunk_results: List[ExtractionResult]
    ) -> ExtractionResult:
        """合并多个分块结果 - 使用LLM智能去重"""

        # 如果只有一个分块，直接返回
        if len(chunk_results) == 1:
            return chunk_results[0]

        # 否则调用LLM进行智能合并
        chunks_json = json.dumps([r.model_dump() for r in chunk_results], ensure_ascii=False)

        messages = [
            {"role": "system", "content": CSKG4APT_IE_SYSTEM_PROMPT},
            {"role": "user", "content": CSKG4APT_CHUNK_MERGE_PROMPT.format(
                chunk_results=chunks_json
            )}
        ]

        response = litellm.completion(
            model=self._get_model_id(),
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "merged_result",
                    "schema": ExtractionResult.model_json_schema(),
                    "strict": True
                }
            },
            temperature=0.1
        )

        merged_json = json.loads(response.choices[0].message.content)
        merged_result = ExtractionResult(**merged_json)

        self.logger.info(
            f"合并完成: {len(merged_result.entities)} 实体, "
            f"{len(merged_result.relations)} 关系"
        )

        return merged_result
```

---

## 📦 阶段二：关系三元组提取 (CSKG4APT-Guided ET)

### 设计逻辑
原CSKG4APT论文中关系提取依赖图遍历和规则匹配，现在用LLM的语义理解能力，直接从上下文推断实体间的7种关系类型。

### 2.1 关系提取Prompt优化

**文件**: `ctinexus/prompts/et_prompts.py`

```python
CSKG4APT_ET_SYSTEM_PROMPT = """你是一个网络威胁情报关系推理专家。

**你的任务**：
根据已提取的实体列表和原文，推断实体之间的语义关系。

**7种关系类型定义**：
1. **load** (加载): 软件/木马加载另一个模块
   - 示例: "Zebrocy loads a secondary payload" → (Zebrocy, load, secondary payload)

2. **exploit** (利用): 攻击者/木马利用漏洞
   - 示例: "APT28 exploits CVE-2017-0143" → (APT28, exploit, CVE-2017-0143)

3. **launch** (发起): 攻击者发起攻击活动
   - 示例: "Lazarus launched Operation XYZ" → (Lazarus, launch, Operation XYZ)

4. **have** (拥有): 攻击者拥有工具/木马
   - 示例: "APT28 has been using Zebrocy since 2015" → (APT28, have, Zebrocy)

5. **belongs_to** (属于): 活动/工具属于某组织
   - 示例: "Operation Aurora belongs to APT1" → (Operation Aurora, belongs_to, APT1)

6. **exist** (存在): 漏洞存在于某资产
   - 示例: "CVE-2017-0143 exists in Windows SMB" → (CVE-2017-0143, exist, Windows SMB)

7. **medium** (媒介): 使用某基础设施作为媒介
   - 示例: "APT28 uses 1.2.3.4 as C2" → (APT28, medium, 1.2.3.4)

**输出要求**：
1. 只输出有明确文本依据的关系
2. 每个关系必须附带原文完整语句
3. 关系的源和目标必须在实体列表中存在
"""

CSKG4APT_ET_USER_PROMPT = """**原文**：
{text}

**已提取实体**：
{entities}

请推断实体之间的关系，返回JSON格式的关系列表。
"""
```

---

## 📦 阶段三：Neo4j图谱持久化

### 设计逻辑
原CSKG4APT使用OrientDB，现迁移到生态更好的Neo4j，使用Cypher的`MERGE`语法自动去重。

### 3.1 Neo4j连接管理器

**新建文件**: `ctinexus/graph_db/neo4j_manager.py`

```python
from neo4j import GraphDatabase
from typing import List
from ..schemas.cskg4apt_ontology import CSKG4APTEntity, CSKG4APTRelation

class Neo4jKnowledgeGraph:
    """Neo4j知识图谱管理器"""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_entity(self, entity: CSKG4APTEntity):
        """创建实体节点 - 自动去重"""
        with self.driver.session() as session:
            cypher = f"""
            MERGE (e:{entity.type.value} {{name: $id}})
            ON CREATE SET
                e.first_seen = datetime(),
                e.derivation_sources = [$derivation_source],
                e.confidence = $confidence,
                e.attributes = $attributes
            ON MATCH SET
                e.derivation_sources = e.derivation_sources + $derivation_source,
                e.last_updated = datetime()
            RETURN e
            """
            session.run(
                cypher,
                id=entity.id,
                derivation_source=entity.derivation_source,
                confidence=entity.confidence,
                attributes=entity.attributes or {}
            )

    def create_relation(self, relation: CSKG4APTRelation):
        """创建关系边 - 附带证据链"""
        with self.driver.session() as session:
            # 动态构建关系类型（Cypher不支持参数化关系类型）
            rel_type = relation.relation_type.value.upper()

            cypher = f"""
            MATCH (source {{name: $source_id}})
            MATCH (target {{name: $target_id}})
            MERGE (source)-[r:{rel_type}]->(target)
            ON CREATE SET
                r.first_seen = datetime(),
                r.evidence = [$derivation_source],
                r.confidence = $confidence,
                r.timestamp = $timestamp
            ON MATCH SET
                r.evidence = r.evidence + $derivation_source,
                r.last_updated = datetime()
            RETURN r
            """
            session.run(
                cypher,
                source_id=relation.source_entity_id,
                target_id=relation.target_entity_id,
                derivation_source=relation.derivation_source,
                confidence=relation.confidence,
                timestamp=relation.timestamp
            )

    def bulk_insert(self, extraction_result: ExtractionResult):
        """批量写入提取结果"""
        # 1. 先创建所有实体
        for entity in extraction_result.entities:
            self.create_entity(entity)

        # 2. 再创建所有关系
        for relation in extraction_result.relations:
            self.create_relation(relation)
```

---

## 📦 阶段四：钻石模型威胁归因

### 设计逻辑
实现CSKG4APT论文中的核心应用场景：给定一个未知的恶意样本/IP/域名，通过图谱多跳查询自动推演出背后的APT组织。

### 4.1 钻石模型查询模板

**新建文件**: `ctinexus/attribution/diamond_model.py`

```python
from typing import Dict, List
from ..graph_db.neo4j_manager import Neo4jKnowledgeGraph

class DiamondModelAttribution:
    """基于钻石模型的APT组织归因引擎"""

    def __init__(self, neo4j_graph: Neo4jKnowledgeGraph):
        self.graph = neo4j_graph

    def attribute_unknown_malware(self, malware_hash: str) -> Dict:
        """场景1: 未知木马归因"""

        cypher = """
        // 输入: 未知木马Hash
        MATCH (m:Malware {name: $malware_hash})

        // 查询1: 找到拥有该木马的APT组织 (Adversary)
        OPTIONAL MATCH (attacker:Attacker)-[:HAVE]->(m)

        // 查询2: 找到该木马利用的漏洞 (Capability)
        OPTIONAL MATCH (m)-[:EXPLOIT]->(vuln:Vulnerability)

        // 查询3: 找到该木马使用的C2基础设施 (Infrastructure)
        OPTIONAL MATCH (m)-[:MEDIUM]->(infra:Infrastructure)

        // 查询4: 找到该木马攻击的目标 (Victim)
        OPTIONAL MATCH (campaign:Campaign)-[:HAVE]->(m)
        OPTIONAL MATCH (campaign)-[:LAUNCH]->(target:Target)

        RETURN
            attacker.name AS adversary,
            collect(DISTINCT vuln.name) AS capabilities,
            collect(DISTINCT infra.name) AS infrastructure,
            collect(DISTINCT target.name) AS victims
        """

        with self.graph.driver.session() as session:
            result = session.run(cypher, malware_hash=malware_hash)
            record = result.single()

            if not record:
                return {"status": "unknown", "message": "未在图谱中找到该木马"}

            # 构建钻石模型四维画像
            diamond_profile = {
                "adversary": record["adversary"],
                "capabilities": record["capabilities"],
                "infrastructure": record["infrastructure"],
                "victims": record["victims"]
            }

            return {
                "status": "success",
                "diamond_model": diamond_profile,
                "query": "unknown_malware_attribution"
            }

    def attribute_unknown_ip(self, ip_address: str) -> Dict:
        """场景2: 未知IP归因"""

        cypher = """
        MATCH (ip:Infrastructure {name: $ip_address})

        // 找到使用该IP的攻击者
        OPTIONAL MATCH (attacker:Attacker)-[:MEDIUM]->(ip)

        // 找到通过该IP发起的活动
        OPTIONAL MATCH (campaign:Campaign)-[:MEDIUM]->(ip)
        OPTIONAL MATCH (campaign)-[:BELONGS_TO]->(attacker)

        // 找到该IP关联的木马
        OPTIONAL MATCH (malware:Malware)-[:MEDIUM]->(ip)
        OPTIONAL MATCH (attacker2:Attacker)-[:HAVE]->(malware)

        RETURN
            coalesce(attacker.name, attacker2.name) AS adversary,
            collect(DISTINCT campaign.name) AS campaigns,
            collect(DISTINCT malware.name) AS malwares
        """

        with self.graph.driver.session() as session:
            result = session.run(cypher, ip_address=ip_address)
            record = result.single()

            if not record or not record["adversary"]:
                return {"status": "unknown", "message": "未在图谱中找到该IP的归属"}

            return {
                "status": "success",
                "adversary": record["adversary"],
                "campaigns": record["campaigns"],
                "malwares": record["malwares"],
                "query": "unknown_ip_attribution"
            }

    def generate_apt_profile(self, attacker_name: str) -> Dict:
        """场景3: 生成APT组织完整画像"""

        cypher = """
        MATCH (attacker:Attacker {name: $attacker_name})

        // 收集所有武器库
        OPTIONAL MATCH (attacker)-[:HAVE]->(malware:Malware)

        // 收集所有利用的漏洞
        OPTIONAL MATCH (attacker)-[:EXPLOIT]->(vuln:Vulnerability)
        OPTIONAL MATCH (malware)-[:EXPLOIT]->(vuln2:Vulnerability)

        // 收集所有基础设施
        OPTIONAL MATCH (attacker)-[:MEDIUM]->(infra:Infrastructure)

        // 收集所有攻击活动
        OPTIONAL MATCH (attacker)-[:LAUNCH]->(campaign:Campaign)

        // 收集所有攻击目标
        OPTIONAL MATCH (campaign)-[:LAUNCH]->(target:Target)

        // 收集所有攻击模式
        OPTIONAL MATCH (attacker)-[r:HAVE]->(pattern:Attack_pattern)

        RETURN
            attacker.name AS name,
            attacker.attributes AS attributes,
            collect(DISTINCT malware.name) AS malware_arsenal,
            collect(DISTINCT vuln.name) + collect(DISTINCT vuln2.name) AS vulnerabilities,
            collect(DISTINCT infra.name) AS infrastructure,
            collect(DISTINCT campaign.name) AS campaigns,
            collect(DISTINCT target.name) AS targets,
            collect(DISTINCT pattern.name) AS attack_patterns
        """

        with self.graph.driver.session() as session:
            result = session.run(cypher, attacker_name=attacker_name)
            record = result.single()

            if not record:
                return {"status": "not_found"}

            # 构建完整APT画像
            profile = {
                "organization": record["name"],
                "attributes": record["attributes"],
                "arsenal": {
                    "malware": record["malware_arsenal"],
                    "vulnerabilities": [v for v in record["vulnerabilities"] if v],
                    "infrastructure": record["infrastructure"],
                },
                "operations": {
                    "campaigns": record["campaigns"],
                    "targets": record["targets"],
                    "ttps": record["attack_patterns"]
                }
            }

            return {"status": "success", "profile": profile}
```

### 4.2 LLM自动生成归因报告

```python
def generate_attribution_report(
    self,
    attribution_result: Dict,
    llm_model: str = "gpt-4"
) -> str:
    """用LLM自动生成自然语言归因报告"""

    prompt = f"""你是一个APT威胁情报分析师。根据以下图谱查询结果，生成一份专业的归因分析报告。

**查询结果**：
{json.dumps(attribution_result, ensure_ascii=False, indent=2)}

**报告要求**：
1. 总结发现的APT组织及其归属依据
2. 列出该组织的武器库、基础设施、攻击目标
3. 分析该组织的攻击偏好和技术特征
4. 提供防御建议

请生成报告：
"""

    response = litellm.completion(
        model=llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    report = response.choices[0].message.content
    return report
```

---

## 📦 阶段五：Playwright自动采集引擎 (可选)

### 设计逻辑
替代原CSKG4APT的Scrapy-Redis爬虫，使用无头浏览器绕过Cloudflare和JS渲染。

**新建文件**: `ctinexus/scraper/playwright_scraper.py`

```python
from playwright.sync_api import sync_playwright
import time

class ThreatIntelScraper:
    """Playwright威胁情报自动采集器"""

    VENDOR_CONFIGS = {
        "fireeye": {
            "base_url": "https://www.mandiant.com/resources/blog",
            "article_selector": "article.blog-post",
            "content_selector": "div.post-content"
        },
        "kaspersky": {
            "base_url": "https://securelist.com",
            "article_selector": "article.post",
            "content_selector": "div.entry-content"
        }
    }

    def scrape_vendor(self, vendor_name: str, max_pages: int = 5):
        """抓取指定安全厂商的最新报告"""

        config = self.VENDOR_CONFIGS.get(vendor_name)
        if not config:
            raise ValueError(f"不支持的厂商: {vendor_name}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

            # 拦截广告和图片（加速）
            context.route("**/*.{png,jpg,jpeg,gif,svg,css}", lambda route: route.abort())

            page = context.new_page()

            articles = []
            for page_num in range(1, max_pages + 1):
                url = f"{config['base_url']}?page={page_num}"
                page.goto(url, wait_until="networkidle")

                # 提取文章链接
                article_links = page.locator(config['article_selector']).all()

                for link_elem in article_links:
                    article_url = link_elem.get_attribute("href")
                    article_title = link_elem.text_content()

                    # 访问文章详情页
                    article_page = context.new_page()
                    article_page.goto(article_url, wait_until="networkidle")

                    # 提取正文
                    content = article_page.locator(config['content_selector']).text_content()

                    articles.append({
                        "title": article_title,
                        "url": article_url,
                        "content": content,
                        "vendor": vendor_name,
                        "scraped_at": time.time()
                    })

                    article_page.close()
                    time.sleep(2)  # 礼貌性延迟

            browser.close()
            return articles
```

---

## 🎨 前端UI改造 - 新增归因查询页面

**修改文件**: `ctinexus/utils/gradio_utils.py`

```python
def create_attribution_tab():
    """新增威胁归因查询Tab"""

    with gr.Tab("🔍 威胁归因查询"):
        gr.Markdown("""
        ### 钻石模型APT组织归因
        输入未知的木马Hash、IP地址或域名，系统将自动在知识图谱中查询其归属的APT组织。
        """)

        with gr.Row():
            query_type = gr.Radio(
                choices=["未知木马Hash", "未知IP地址", "APT组织画像"],
                value="未知木马Hash",
                label="查询类型"
            )

        with gr.Row():
            query_input = gr.Textbox(
                label="输入查询值",
                placeholder="如: 0x9a8b7c6d... 或 192.168.1.1 或 APT28",
                lines=1
            )

        query_btn = gr.Button("🔎 开始归因查询", variant="primary")

        with gr.Row():
            result_json = gr.JSON(label="图谱查询结果")

        with gr.Row():
            attribution_report = gr.Textbox(
                label="LLM自动生成归因报告",
                lines=20,
                max_lines=30
            )

        query_btn.click(
            fn=run_attribution_query,
            inputs=[query_type, query_input],
            outputs=[result_json, attribution_report]
        )

def run_attribution_query(query_type: str, query_input: str):
    """执行归因查询"""
    from ..attribution.diamond_model import DiamondModelAttribution
    from ..graph_db.neo4j_manager import Neo4jKnowledgeGraph

    # 连接Neo4j
    graph = Neo4jKnowledgeGraph(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="your_password"
    )

    attribution = DiamondModelAttribution(graph)

    # 根据查询类型执行
    if query_type == "未知木马Hash":
        result = attribution.attribute_unknown_malware(query_input)
    elif query_type == "未知IP地址":
        result = attribution.attribute_unknown_ip(query_input)
    else:  # APT组织画像
        result = attribution.generate_apt_profile(query_input)

    # 生成报告
    report = attribution.generate_attribution_report(result)

    graph.close()
    return result, report
```

---

## 📊 改造效果对比

| 维度 | CSKG4APT原版 | CTINexus融合版 |
|------|-------------|---------------|
| **实体提取** | BERT-BiLSTM-GRU-CRF<br>需训练，F1=81% | LLM零样本<br>无需训练，可解释 |
| **关系推理** | 规则+图遍历 | LLM语义推理 |
| **本体约束** | 硬编码12实体+7关系 | Pydantic强类型验证 |
| **证据溯源** | ❌ 无 | ✅ 每个三元组附带原文 |
| **图谱存储** | OrientDB | Neo4j (生态更好) |
| **数据采集** | Scrapy-Redis (易封禁) | Playwright (绕过JS渲染) |
| **威胁归因** | 手动Cypher查询 | 自动钻石模型推演 |
| **前端UI** | ❌ 无 | Gradio深色科技主题 |
| **多模态** | ❌ 不支持 | ✅ PDF文本+图像分析 |

---

## 🚀 实施路线图

### Phase 1: 核心改造 (1-2周)
- [x] 创建CSKG4APT本体Schema (`cskg4apt_ontology.py`)
- [ ] 修改IE引擎集成12实体约束
- [ ] 修改ET引擎集成7关系约束
- [ ] 升级Prompt工程支持强制溯源

### Phase 2: 图谱持久化 (1周)
- [ ] 集成Neo4j连接器
- [ ] 实现Cypher自动去重写入
- [ ] 迁移现有NetworkX数据

### Phase 3: 威胁归因 (1周)
- [ ] 实现钻石模型查询引擎
- [ ] 开发LLM归因报告生成
- [ ] 前端新增归因查询Tab

### Phase 4: 自动采集 (可选, 1周)
- [ ] Playwright爬虫引擎
- [ ] 支持FireEye/Kaspersky/CrowdStrike

---

## 📝 配置文件修改

**`ctinexus/config/config.yaml`** 新增：

```yaml
# CSKG4APT本体约束开关
cskg4apt_mode:
  enabled: true  # 是否启用严格本体约束
  entity_types: 12  # 实体类型数量
  relation_types: 7  # 关系类型数量
  force_evidence: true  # 强制每个提取附带原文证据

# Neo4j配置
neo4j:
  uri: "bolt://localhost:7687"
  user: "neo4j"
  password: "your_password"
  database: "cskg4apt"

# Playwright爬虫配置 (可选)
scraper:
  enabled: false
  vendors: ["fireeye", "kaspersky"]
  max_pages_per_vendor: 5
  delay_seconds: 2
```

---

## 🎯 总结

这份改造方案完美融合了：
1. **CSKG4APT的严谨本体** → 12实体+7关系硬约束
2. **LLM的零样本能力** → 替代BERT四层神经网络
3. **CTINexus的工程化** → 四阶段流水线+Gradio UI
4. **现代化技术栈** → Neo4j + Playwright + 多模态

**核心优势**：
✅ 白盒可解释 (每个三元组都有原文证据)
✅ 零样本学习 (无需标注数据和模型训练)
✅ 工程化落地 (完整前后端+数据库)
✅ 自动化归因 (钻石模型威胁狩猎)

---

**下一步**：请确认该方案是否符合您的预期，我将开始逐步实施代码改造。

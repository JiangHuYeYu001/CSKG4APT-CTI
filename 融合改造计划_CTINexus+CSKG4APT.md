# CTINexus + CSKG4APT 融合改造计划

**文档版本**: v1.0
**创建日期**: 2026年3月27日
**融合核心**: LLM动态提取 + APT本体约束 + 威胁归因

---

## 第一部分: 论文核心要点总结

### CSKG4APT (Ren et al., 2023) 论文的核心贡献

#### 1. 问题定位
- **现状**: OSCTI (Open-Source CTI) 报告大量非结构化，难以自动化提取
- **痛点**:
  - 多源数据质量不均
  - 没有统一的APT知识表示
  - 传统防御方法信息不对称
- **目标**: 从非结构化CTI文本中提取APT威胁知识，构建知识图谱进行威胁归因

#### 2. CSKG4APT系统设计

**A. 本体结构 (APT Ontology)**

**12种实体类型**:
```
Attacker/Organization → APT组织、黑客团伙
Infrastructure → C2服务器、恶意域名、IP地址、僵尸网络
Malware/Tool → 恶意软件、后门、提权工具 (Zebrocy, Mimikatz等)
Vulnerability → 漏洞及其ID (CVE-YYYY-NNNNN)
Assets → 受攻击的系统/应用 (Windows SMB, Exchange等)
Target → 攻击目标行业/地区 (政府机构、金融、医疗等)
Event → 攻击活动、事件 (操作、活动代号)
Behavior/TTP → 战术技巧 (初始访问、权限提升、数据盗窃等)
Time → 时间信息 (事件发生时间、活动时间窗口)
Relationship/Evidence → 证据、威胁情报标记
```

**7种关系类型** (有向边):
```
has        : Attacker -[has]-> Malware         (组织拥有恶意软件)
uses       : Attacker -[uses]-> Tool           (组织使用工具)
exploit    : Malware -[exploit]-> Vulnerability (恶意软件利用漏洞)
exist      : Vulnerability -[exist]-> Assets   (漏洞存在于资产)
target     : Attacker -[target]-> Target       (组织目标)
medium     : Attacker -[medium]-> Infrastructure (组织基础设施)
behavior   : Event -[behavior]-> TTP           (事件包含的战术)
```

**B. 原论文算法流程**
1. **数据预处理**: 清洗、分句、分词
2. **实体抽取**: BERT-BiLSTM-GRU-CRF模型 (需要标注数据训练)
3. **关系抽取**: 基于规则的关系分类器
4. **知识图谱构建**: 三元组融合、去重、更新
5. **威胁归因**: Diamond Model + 攻击链分析

**C. 评测结果**
- 实体识别: F1 = 81.88% (中文数据)
- 支持双语 (中文/英文)
- 知识图谱更新效率高

#### 3. 应用场景

- **APT组织追踪**: 关联不同报告中的同一组织
- **威胁情报聚合**: 整合多源CTI为统一知识表示
- **攻击链复原**: 从报告自动建立完整的attack chain
- **属性分析**: 基于Diamond Model进行威胁溯源

---

## 第二部分: CTINexus项目分析

### 核心优势
1. **LLM驱动的IE**: 支持多Provider (OpenAI, Gemini, AWS, Ollama)
2. **4阶段Pipeline**: IE → ET → EA → LP (自动化完整工作流)
3. **Gradio Web UI**: 即开即用，易于使用
4. **可视化**: Pyvis动态知识图谱
5. **模块化**: 每个阶段可独立扩展

### 当前局限性
1. **本体约束弱**: 没有强制的entity/relation类型 (基于通用本体)
2. **没有威胁归因**: 不支持APT组织追踪、属性分析
3. **没有Diamond Model**: 缺少正式的威胁分析框架
4. **没有知识图谱数据库**: 只生成HTML可视化，不持久化
5. **通用性过强**: 适合泛化KG构建，但对APT专有知识不够深度

---

## 第三部分: 融合改造总体方案

### 设计原则
1. **LLM优先**: 利用LLM的语义理解能力替代神经网络训练
2. **本体约束**: 强制CSKG4APT的12+7本体定义
3. **可追溯性**: 白盒化，每个提取都包含证据链
4. **组件化**: 保留CTINexus的模块化设计
5. **渐进式集成**: 不破坏现有功能，分阶段改造

### 总体架构

```
├─ Layer 1: 输入处理
│  ├─ CTI文本输入
│  └─ URL抽取 (复用CTINexus的UrlSourceInput)
│
├─ Layer 2: 智能提取 (新增CSKG4APT模式)
│  ├─ IE-APT: LLM提取APT实体和关系
│  │   └─ 本体约束: 12类型实体、7类型关系
│  ├─ ET-APT: 实体类型分类 (已在12类内)
│  └─ Evidence Chain: 每个提取附证据源
│
├─ Layer 3: 实体对齐与知识融合
│  ├─ APT实体去重与合并
│  ├─ CVE/IP/Domain等IOC保护
│  └─ Diamond Model标注
│
├─ Layer 4: 威胁归因与分析
│  ├─ APT组织属性提取
│  ├─ 攻击链复原
│  ├─ 相似度分析 (识别同一组织)
│  └─ 威胁评分
│
└─ Layer 5: 存储与可视化
   ├─ Neo4j图数据库持久化
   ├─ Pyvis 2D可视化
   ├─ Dashboard 威胁情报看板
   └─ REST API 查询接口
```

---

## 第四部分: 详细改造计划

### Phase 1: 核心本体与数据结构 (第1-2周)

#### 1.1 定义CSKG4APT Pydantic Schema

**文件**: `ctinexus/schemas/cskg4apt_ontology.py`

```python
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, validator

# 实体类型定义
class CSKGEntityType(str):
    Attacker = "Attacker"           # APT组织/黑客团伙
    Infrastructure = "Infrastructure"  # C2/域名/IP/僵尸网络
    Malware = "Malware"             # 恶意软件/后门
    Vulnerability = "Vulnerability" # 漏洞
    Assets = "Assets"               # 受攻击资产
    Target = "Target"               # 攻击目标
    Event = "Event"                 # 攻击活动
    Behavior = "Behavior"           # 战术技巧/TTP
    Time = "Time"                   # 时间信息
    Tool = "Tool"                   # 工具/合法工具滥用
    Credential = "Credential"       # 凭证
    Indicator = "Indicator"         # 指标 (URL/Hash等)

# 关系类型定义
class CSKGRelationType(str):
    has = "has"             # Attacker -[has]-> Malware
    uses = "uses"           # Attacker -[uses]-> Tool
    exploit = "exploit"     # Malware -[exploit]-> Vulnerability
    exist = "exist"         # Vulnerability -[exist]-> Assets
    target = "target"       # Attacker -[target]-> Target
    medium = "medium"       # Attacker -[medium]-> Infrastructure
    behavior = "behavior"   # Event -[behavior]-> Behavior

# 实体
class CSKGEntity(BaseModel):
    id: str                      # 实体唯一ID
    type: CSKGEntityType        # 实体类型
    name: str                   # 实体名称
    aliases: List[str] = []     # 别名列表
    derivation_source: str      # 原文证据 (可溯源)
    confidence: float = 1.0     # 置信度 0.0-1.0
    attributes: Dict = {}       # 扩展属性 (如CVE-YYYY-NNNNN格式)

    @validator('type')
    def validate_type(cls, v):
        valid_types = [
            "Attacker", "Infrastructure", "Malware", "Vulnerability",
            "Assets", "Target", "Event", "Behavior", "Time",
            "Tool", "Credential", "Indicator"
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid entity type: {v}")
        return v

# 关系
class CSKGRelation(BaseModel):
    source_entity_id: str       # 源实体ID
    target_entity_id: str       # 目标实体ID
    relation_type: CSKGRelationType  # 关系类型
    derivation_source: str      # 原文证据 (包含两个实体的上下文)
    confidence: float = 1.0     # 置信度

    @validator('relation_type')
    def validate_relation_type(cls, v):
        valid_relations = ["has", "uses", "exploit", "exist",
                          "target", "medium", "behavior"]
        if v not in valid_relations:
            raise ValueError(f"Invalid relation type: {v}")
        return v

# 知识图谱
class CSKG4APTGraph(BaseModel):
    name: str                           # 知识图谱名称
    source_url: Optional[str] = None    # 来源URL
    source_text: str                    # 源文本
    extraction_timestamp: str           # 提取时间戳
    entities: List[CSKGEntity]          # 实体列表
    relations: List[CSKGRelation]       # 关系列表

    def to_networkx(self):
        """转换为NetworkX有向图"""
        import networkx as nx
        G = nx.DiGraph()
        for entity in self.entities:
            G.add_node(entity.id, type=entity.type, name=entity.name)
        for relation in self.relations:
            G.add_edge(relation.source_entity_id,
                      relation.target_entity_id,
                      relation=relation.relation_type)
        return G
```

#### 1.2 定义APT威胁属性模型

**文件**: `ctinexus/schemas/apt_attributes.py`

```python
from typing import List, Optional, Dict
from pydantic import BaseModel

# Diamond Model: Attacker/Capability/Infrastructure/Victim
class DiamondModelVertex(BaseModel):
    adversary: Optional[str]        # 攻击者 (APT组织)
    capability: List[str]           # 能力 (恶意软件、工具)
    infrastructure: List[str]       # 基础设施 (C2、域名)
    victim: List[str]               # 受害者 (目标)
    timestamp: Optional[str]        # 事件时间

# APT威胁情报卡片
class APTThreatCard(BaseModel):
    attacker_id: str                # APT组织ID
    attacker_names: List[str]       # APT组织名称及别名
    active_since: Optional[str]     # 活跃时间
    attributed_to: Optional[str]    # 属于国家/地区

    # 战术能力
    tactics: List[str]              # 攻击战术 (MITRE ATT&CK)
    techniques: List[str]           # 技术细节

    # 已知工具/恶意软件
    malwares: List[str]             # 已知恶意软件
    tools: List[str]                # 已知工具

    # 已知基础设施
    c2_servers: List[str]           # C2服务器
    domains: List[str]              # 恶意域名
    ips: List[str]                  # IP地址

    # 目标信息
    target_sectors: List[str]       # 目标行业 (政府、金融等)
    target_countries: List[str]     # 目标国家/地区

    # 相关CVE
    exploited_cves: List[str]       # 已知利用的CVE

    # 关联关系
    associated_groups: List[str]    # 关联APT组织
    evidence_urls: List[str]        # 证据报告URL

# 攻击链
class AttackChain(BaseModel):
    attack_id: str                  # 攻击链ID
    attacker: str                   # 发动攻击的APT组织
    target: str                     # 攻击目标
    timestamp: Optional[str]        # 攻击时间

    # 攻击阶段 (MITRE Kill Chain)
    reconnaissance: Optional[Dict]  # 侦察
    weaponization: Optional[Dict]   # 武器化
    delivery: Optional[Dict]        # 传递
    exploitation: Optional[Dict]    # 利用
    installation: Optional[Dict]    # 安装
    command_control: Optional[Dict] # 命令控制
    actions_on_objective: Optional[Dict]  # 目标动作

    # 来源证据
    evidence_source: str            # 原文或来源
```

---

### Phase 2: LLM提取器改造 (第2-3周)

#### 2.1 CSKG4APT IE提取器

**文件**: `ctinexus/ctinexus/cskg4apt_extractor.py`

```python
import json
import logging
import os
import time
from typing import List, Dict, Tuple

from jinja2 import Environment, FileSystemLoader, meta
from omegaconf import DictConfig

from .llm_processor import LLMCaller, UsageCalculator
from .schemas.cskg4apt_ontology import (
    CSKG4APTGraph, CSKGEntity, CSKGRelation,
    CSKGEntityType, CSKGRelationType
)
from .utils.path_utils import resolve_path

logger = logging.getLogger(__name__)

class CSKG4APTExtractor:
    """
    LLM-based CSKG4APT knowledge extraction

    输入: 威胁情报文本
    输出: 符合CSKG4APT本体的结构化知识图谱

    特点:
    - 零样本学习 (无需训练数据)
    - 强本体约束 (12实体+7关系)
    - 白盒可溯源 (每个提取都有证据)
    - Pydantic验证 (类型检查)
    """

    def __init__(self, config: DictConfig):
        self.config = config
        self.entity_id_map = {}  # 用于去重
        self.extracted_entities = {}
        self.extracted_relations = []

    def call(self, text: str, source_url: str = None) -> CSKG4APTGraph:
        """
        主提取入口

        Args:
            text: CTI报告文本
            source_url: 可选的源URL

        Returns:
            CSKG4APTGraph: 完整的APT知识图谱
        """
        logger.info(f"开始CSKG4APT提取，文本长度: {len(text)}")

        # Step 1: 实体抽取
        entities = self._extract_entities(text)
        logger.info(f"提取实体数: {len(entities)}")

        # Step 2: 关系抽取
        relations = self._extract_relations(text, entities)
        logger.info(f"提取关系数: {len(relations)}")

        # Step 3: 构建知识图谱
        kg = CSKG4APTGraph(
            name=f"CSKG4APT-{int(time.time())}",
            source_url=source_url,
            source_text=text,
            extraction_timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            entities=entities,
            relations=relations
        )

        logger.info(f"知识图谱构建完成，包含 {len(entities)} 个实体，{len(relations)} 个关系")
        return kg

    def _extract_entities(self, text: str) -> List[CSKGEntity]:
        """
        使用LLM提取CSKG4APT实体

        Prompt策略:
        - 列举所有12种实体类型的定义和示例
        - 要求返回JSON格式 {entities: [{id, type, name, derivation_source, confidence}]}
        - 包含few-shot示例
        """
        prompt = self._generate_entity_extraction_prompt(text)
        response, response_time = LLMCaller(self.config, prompt).call()
        usage = UsageCalculator(self.config, response).calculate()

        # 解析响应
        response_content = self._extract_json_from_response(
            response.choices[0].message.content
        )

        entities = []
        for entity_data in response_content.get("entities", []):
            try:
                entity = CSKGEntity(
                    id=entity_data.get("id"),
                    type=entity_data.get("type"),
                    name=entity_data.get("name"),
                    derivation_source=entity_data.get("derivation_source"),
                    confidence=entity_data.get("confidence", 1.0)
                )
                # 去重
                entity_key = (entity.type, entity.id)
                if entity_key not in self.entity_id_map:
                    entities.append(entity)
                    self.entity_id_map[entity_key] = entity.id
                    self.extracted_entities[entity.id] = entity
            except Exception as e:
                logger.warning(f"实体验证失败: {e}")

        return entities

    def _extract_relations(self, text: str, entities: List[CSKGEntity]) -> List[CSKGRelation]:
        """
        使用LLM提取CSKG4APT关系

        Prompt策略:
        - 基于已抽取的实体列表
        - 定义7种关系类型的含义和约束
        - 要求返回JSON: {relations: [{source_id, target_id, type, derivation_source}]}
        """
        prompt = self._generate_relation_extraction_prompt(text, entities)
        response, response_time = LLMCaller(self.config, prompt).call()
        usage = UsageCalculator(self.config, response).calculate()

        response_content = self._extract_json_from_response(
            response.choices[0].message.content
        )

        relations = []
        entity_ids = set(e.id for e in entities)

        for relation_data in response_content.get("relations", []):
            try:
                # 验证源/目标实体存在
                source_id = relation_data.get("source_entity_id")
                target_id = relation_data.get("target_entity_id")

                if source_id not in entity_ids or target_id not in entity_ids:
                    logger.warning(f"关系实体不存在: {source_id} -> {target_id}")
                    continue

                relation = CSKGRelation(
                    source_entity_id=source_id,
                    target_entity_id=target_id,
                    relation_type=relation_data.get("relation_type"),
                    derivation_source=relation_data.get("derivation_source"),
                    confidence=relation_data.get("confidence", 1.0)
                )
                relations.append(relation)
            except Exception as e:
                logger.warning(f"关系验证失败: {e}")

        return relations

    def _generate_entity_extraction_prompt(self, text: str) -> List[Dict]:
        """生成实体提取prompt"""
        entity_definitions = """
        12种CSKG4APT实体类型:

        1. Attacker: APT组织、黑客团伙、威胁行为体 (如 APT28, Lazarus, Wizard Spider)
        2. Infrastructure: C2服务器、恶意域名、IP地址、僵尸网络 (如 192.168.1.100, evil.com)
        3. Malware: 恶意软件、后门、木马、蠕虫 (如 Zebrocy, SUNBURST, Emotet)
        4. Vulnerability: 漏洞及其标识符 (必须是CVE-YYYY-NNNNN格式)
        5. Assets: 受攻击的系统/应用 (如 Windows SMB, Exchange Server, Apache)
        6. Target: 攻击目标 (如 "政府机构", "金融行业", "美国")
        7. Event: 具体的攻击活动、事件 (如 Operation Stealth, SolarWinds供应链攻击)
        8. Behavior: 战术技巧、TTP (如 "初始访问", "权限提升", "数据窃取")
        9. Time: 时间信息 (如 "2023年5月", "自2015年以来")
        10. Tool: 工具/合法工具滥用 (如 Mimikatz, PsExec, PowerShell)
        11. Credential: 凭证 (如 用户名、密码、token)
        12. Indicator: 指标 (如 URL哈希值、Email、Yara规则)
        """

        user_prompt = f"""{entity_definitions}

        请从以下CTI文本中提取所有CSKG4APT实体。

        **提取规则:**
        1. 只提取上述12种类型的实体
        2. 每个实体必须包含:
           - id: 唯一标识符 (去除特殊符号)
           - type: 选择上述类型之一
           - name: 实体名称
           - derivation_source: 原文中的出现句子/段落 (用于溯源)
           - confidence: 0.0-1.0 (默认1.0)
        3. 不要捏造证据，只从文本中提取已有信息
        4. 同一实体多次出现时，只记录一次

        **目标CTI文本:**
        {text}

        **返回格式 (JSON):**
        {{
            "entities": [
                {{
                    "id": "apt28",
                    "type": "Attacker",
                    "name": "APT28",
                    "derivation_source": "...",
                    "confidence": 1.0
                }},
                ...
            ]
        }}
        """

        return [{"role": "user", "content": user_prompt}]

    def _generate_relation_extraction_prompt(self, text: str, entities: List[CSKGEntity]) -> List[Dict]:
        """生成关系提取prompt"""
        # 构建实体列表
        entity_list = "\n".join([
            f"- {e.id} ({e.type}): {e.name}"
            for e in entities
        ])

        relation_definitions = """
        7种CSKG4APT关系类型和约束:

        1. has: Attacker -[has]-> Malware
           含义: 攻击者拥有/开发了某恶意软件
           示例: APT28 -[has]-> Zebrocy

        2. uses: Attacker -[uses]-> Tool
           含义: 攻击者使用了某工具
           示例: APT28 -[uses]-> Mimikatz

        3. exploit: Malware -[exploit]-> Vulnerability
           含义: 恶意软件利用了某漏洞
           示例: Zebrocy -[exploit]-> CVE-2017-0143

        4. exist: Vulnerability -[exist]-> Assets
           含义: 漏洞存在于某资产/系统
           示例: CVE-2017-0143 -[exist]-> Windows SMB

        5. target: Attacker -[target]-> Target
           含义: 攻击者针对某目标
           示例: APT28 -[target]-> 政府机构

        6. medium: Attacker -[medium]-> Infrastructure
           含义: 攻击者使用某基础设施
           示例: APT28 -[medium]-> 192.168.1.100

        7. behavior: Event -[behavior]-> Behavior
           含义: 事件包含了某战术行为
           示例: Operation X -[behavior]-> 数据窃取
        """

        user_prompt = f"""{relation_definitions}

        **已提取的实体列表:**
        {entity_list}

        请从以下CTI文本中提取关系。关系的源和目标 **必须** 来自上述实体列表。

        **提取规则:**
        1. 只从已有实体间建立关系
        2. 只使用7种定义的关系类型
        3. 遵守源目标类型约束 (如 has必须是Attacker->Malware)
        4. derivation_source必须同时包含源和目标实体的上下文
        5. 不要捏造关系

        **目标CTI文本:**
        {text}

        **返回格式 (JSON):**
        {{
            "relations": [
                {{
                    "source_entity_id": "apt28",
                    "target_entity_id": "zebrocy",
                    "relation_type": "has",
                    "derivation_source": "...",
                    "confidence": 1.0
                }},
                ...
            ]
        }}
        """

        return [{"role": "user", "content": user_prompt}]

    def _extract_json_from_response(self, response_text: str) -> Dict:
        """
        从LLM响应中提取JSON

        支持多种格式:
        - 纯JSON
        - JSON代码块 (```json ... ```)
        - JSON嵌入其他文本
        """
        import re

        # 尝试纯JSON解析
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass

        # 尝试提取代码块
        json_matches = re.findall(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_matches:
            try:
                return json.loads(json_matches[0])
            except json.JSONDecodeError:
                pass

        # 尝试提取最后一个JSON对象
        json_matches = re.findall(r'\{[\s\S]*\}', response_text)
        if json_matches:
            try:
                return json.loads(json_matches[-1])
            except json.JSONDecodeError:
                pass

        logger.error("无法从LLM响应中提取JSON")
        return {"entities": [], "relations": []}
```

#### 2.2 集成到Pipeline

**修改**: `ctinexus/ctinexus/utils/gradio_utils.py`

```python
# 新增函数
def run_cskg4apt_extraction(config: DictConfig, text: str) -> dict:
    """运行CSKG4APT提取"""
    from ..cskg4apt_extractor import CSKG4APTExtractor

    extractor = CSKG4APTExtractor(config)
    kg = extractor.call(text)

    # 转换为JSON
    return {
        "graph": kg.dict(),
        "entity_count": len(kg.entities),
        "relation_count": len(kg.relations),
        "timestamp": kg.extraction_timestamp
    }

# 修改run_pipeline支持两种模式
def run_pipeline(
    text: str = None,
    source_url: str = None,
    ie_model: str = None,
    et_model: str = None,
    ea_model: str = None,
    lp_model: str = None,
    similarity_threshold: float = 0.6,
    mode: str = "default",  # "default" 或 "cskg4apt"
    progress=None,
):
    """
    mode="default": 原有CTINexus流程
    mode="cskg4apt": 新增CSKG4APT流程
    """

    if mode == "cskg4apt":
        # CSKG4APT流程
        return run_cskg4apt_pipeline(text, source_url, ie_model, progress)
    else:
        # 原有流程
        return run_pipeline_original(...)
```

---

### Phase 3: 威胁归因与Diamond Model (第3-4周)

#### 3.1 APT威胁分析模块

**文件**: `ctinexus/ctinexus/attribution/apt_analyzer.py`

```python
import logging
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass

from ctinexus.schemas.apt_attributes import (
    APTThreatCard, DiamondModelVertex, AttackChain
)
from ctinexus.schemas.cskg4apt_ontology import CSKG4APTGraph, CSKGEntity, CSKGRelation

logger = logging.getLogger(__name__)

class APTAttributor:
    """
    APT组织属性识别与威胁归因

    功能:
    - 从CSKG4APT知识图谱自动生成APT威胁卡片
    - 识别攻击者、能力、基础设施、目标 (Diamond Model)
    - 评估威胁等级
    - 关联相似攻击 (识别同一组织)
    """

    def __init__(self, knowledge_base: Optional[Dict] = None):
        """
        Args:
            knowledge_base: 外部知识库 (如APT名单、已知IOC等)
        """
        self.kb = knowledge_base or {}

    def generate_threat_card(self, kg: CSKG4APTGraph) -> List[APTThreatCard]:
        """
        从知识图谱生成威胁卡片

        策略:
        1. 识别所有Attacker实体
        2. 收集其related entities
        3. 构建属性字典
        """
        threat_cards = []

        # 找出所有Attacker
        attackers = [e for e in kg.entities if e.type == "Attacker"]

        for attacker in attackers:
            card = self._build_threat_card(attacker, kg)
            threat_cards.append(card)

        return threat_cards

    def _build_threat_card(self, attacker_entity: CSKGEntity, kg: CSKG4APTGraph) -> APTThreatCard:
        """为单个APT组织构建威胁卡片"""

        # 构建关系图
        outgoing_edges = [r for r in kg.relations if r.source_entity_id == attacker_entity.id]
        incoming_edges = [r for r in kg.relations if r.target_entity_id == attacker_entity.id]

        # 提取malware
        malwares = [
            kg.entities[id].name
            for r in outgoing_edges if r.relation_type == "has"
            for id in [r.target_entity_id]
            if kg.get_entity(id) and kg.get_entity(id).type == "Malware"
        ]

        # 提取工具
        tools = [
            kg.entities[id].name
            for r in outgoing_edges if r.relation_type == "uses"
            for id in [r.target_entity_id]
            if kg.get_entity(id) and kg.get_entity(id).type == "Tool"
        ]

        # 提取基础设施
        infra = [
            kg.entities[id].name
            for r in outgoing_edges if r.relation_type == "medium"
            for id in [r.target_entity_id]
            if kg.get_entity(id) and kg.get_entity(id).type == "Infrastructure"
        ]

        # 提取目标
        targets = [
            kg.entities[id].name
            for r in outgoing_edges if r.relation_type == "target"
            for id in [r.target_entity_id]
            if kg.get_entity(id) and kg.get_entity(id).type == "Target"
        ]

        # 提取漏洞
        exploited_cves = [
            kg.entities[id].name
            for r in outgoing_edges
            for next_r in [r for r2 in kg.relations if r2.source_entity_id == r.target_entity_id]
            if next_r.relation_type == "exploit"
            for id in [next_r.target_entity_id]
            if kg.get_entity(id) and kg.get_entity(id).type == "Vulnerability"
        ]

        card = APTThreatCard(
            attacker_id=attacker_entity.id,
            attacker_names=[attacker_entity.name] + attacker_entity.aliases,
            malwares=malwares,
            tools=tools,
            c2_servers=[x for x in infra if self._is_ip_or_domain(x)],
            domains=[x for x in infra if self._is_domain(x)],
            ips=[x for x in infra if self._is_ip(x)],
            target_sectors=targets,
            exploited_cves=exploited_cves,
        )

        return card

    def diamond_model_analysis(self, kg: CSKG4APTGraph) -> Dict[str, DiamondModelVertex]:
        """
        根据CSKG4APT生成Diamond Model顶点

        Diamond Model的四个顶点:
        - Adversary (攻击者): Attacker类型
        - Capability (能力): Malware/Tool
        - Infrastructure (基础设施): 域名/IP/C2
        - Victim (受害者): Target
        """

        diamond_models = {}

        for event in [e for e in kg.entities if e.type == "Event"]:
            # 找出该事件相关的所有信息
            related_relations = [
                r for r in kg.relations
                if r.source_entity_id == event.id or r.target_entity_id == event.id
            ]

            adversary = None
            capabilities = []
            infrastructures = []
            victims = []

            for relation in related_relations:
                if relation.relation_type == "behavior":
                    # Event -[behavior]-> Behavior
                    pass

            # 查找关联的attacker
            attackers_related = set()
            for relation in related_relations:
                if kg.get_entity(relation.source_entity_id).type == "Attacker":
                    attackers_related.add(relation.source_entity_id)
                if kg.get_entity(relation.target_entity_id).type == "Attacker":
                    attackers_related.add(relation.target_entity_id)

            if attackers_related:
                adversary = list(attackers_related)[0]

            diamond_models[event.id] = DiamondModelVertex(
                adversary=adversary,
                capability=capabilities,
                infrastructure=infrastructures,
                victim=victims
            )

        return diamond_models

    def _is_ip(self, text: str) -> bool:
        import re
        return bool(re.match(r'^(\d{1,3}\.){3}\d{1,3}$', text))

    def _is_domain(self, text: str) -> bool:
        import re
        return bool(re.match(r'^[a-z0-9-]+\.[a-z]{2,}$', text))

    def _is_ip_or_domain(self, text: str) -> bool:
        return self._is_ip(text) or self._is_domain(text)
```

---

### Phase 4: 知识图谱持久化 (Neo4j) (第4-5周)

#### 4.1 Neo4j集成

**文件**: `ctinexus/ctinexus/graph_db/neo4j_handler.py`

```python
from neo4j import GraphDatabase
from typing import List, Dict, Optional

class Neo4jHandler:
    """
    Neo4j图数据库操作接口

    支持:
    - 创建/更新CSKG4APT实体和关系
    - Cypher查询
    - 图遍历和路径分析
    - 相似性计算
    """

    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def create_kg_graph(self, kg):
        """将CSKG4APTGraph写入Neo4j"""
        with self.driver.session() as session:
            # 创建实体
            for entity in kg.entities:
                query = f"""
                MERGE (n:{entity.type} {{id: $id}})
                SET n.name = $name, n.confidence = $confidence
                """
                session.run(query, id=entity.id, name=entity.name,
                           confidence=entity.confidence)

            # 创建关系
            for relation in kg.relations:
                query = f"""
                MATCH (s {{id: $source}}), (t {{id: $target}})
                CREATE (s)-[r:{relation.relation_type.upper()} {{confidence: $confidence}}]->(t)
                """
                session.run(query, source=relation.source_entity_id,
                           target=relation.target_entity_id,
                           confidence=relation.confidence)

    def query_apt_profile(self, apt_name: str) -> Dict:
        """查询APT组织的完整画像"""
        query = """
        MATCH (attacker:Attacker {name: $apt_name})
        OPTIONAL MATCH (attacker)-[r:has]->(malware:Malware)
        OPTIONAL MATCH (attacker)-[r:medium]->(infra:Infrastructure)
        RETURN attacker, COLLECT(malware) as malwares, COLLECT(infra) as infras
        """
        with self.driver.session() as session:
            result = session.run(query, apt_name=apt_name)
            return result.single()

    def find_attack_chain(self, attacker: str, victim: str) -> List[List[Dict]]:
        """找出从attacker到victim的所有攻击链"""
        query = """
        MATCH path = (a:Attacker {name: $attacker})-[*]-(v:Target {name: $victim})
        RETURN path
        """
        with self.driver.session() as session:
            result = session.run(query, attacker=attacker, victim=victim)
            return [record for record in result]
```

---

### Phase 5: Web UI与API扩展 (第5-6周)

#### 5.1 添加CSKG4APT模式的UI选项

**修改**: `ctinexus/ctinexus/utils/gradio_utils.py` - `build_interface()`

```python
def build_interface(warning: str = None):
    import gradio as gr

    with gr.Blocks(title="CTINexus + CSKG4APT") as interface:
        # ... 现有UI代码 ...

        # 新增: 分析模式选择
        with gr.Group():
            gr.Markdown("### 分析模式")
            analysis_mode = gr.Radio(
                choices=["CTINexus (通用)", "CSKG4APT (APT专用)"],
                value="CTINexus (通用)",
                label="选择分析模式"
            )

        # CSKG4APT特有的选项面板
        with gr.Group(visible=False) as cskg4apt_options:
            gr.Markdown("### CSKG4APT选项")

            enable_diamond_model = gr.Checkbox(
                label="启用Diamond Model分析",
                value=True
            )

            enable_threat_card = gr.Checkbox(
                label="生成APT威胁卡片",
                value=True
            )

            enable_neo4j_storage = gr.Checkbox(
                label="保存到Neo4j数据库",
                value=False
            )

            neo4j_uri = gr.Textbox(
                label="Neo4j URI",
                value="bolt://localhost:7687",
                visible=False
            )

            # 根据checkbox显示/隐藏Neo4j配置
            enable_neo4j_storage.change(
                fn=lambda x: gr.update(visible=x),
                inputs=[enable_neo4j_storage],
                outputs=[neo4j_uri]
            )

        # 根据模式选择显示/隐藏面板
        def toggle_mode(mode):
            is_cskg4apt = "CSKG4APT" in mode
            return gr.update(visible=is_cskg4apt)

        analysis_mode.change(
            fn=toggle_mode,
            inputs=[analysis_mode],
            outputs=[cskg4apt_options]
        )

        # ... 输出面板 ...

        # 新增输出: 威胁卡片、Diamond Model
        with gr.Row():
            with gr.Column():
                threat_card_output = gr.JSON(
                    label="APT威胁卡片",
                    visible=False
                )
            with gr.Column():
                diamond_model_output = gr.JSON(
                    label="Diamond Model",
                    visible=False
                )
```

---

## 第五部分: 实现时间表与优先级

### 开发阶段

| 阶段 | 任务 | 周数 | 优先级 | 关键成果 |
|------|------|------|--------|---------|
| 1 | 本体Schema设计 | 1-2 | P0 | Pydantic模型，通过验证 |
| 2 | LLM提取器 (IE/ET) | 2-3 | P0 | CSKG4APT格式的提取 |
| 3 | APT威胁分析 | 3-4 | P1 | 威胁卡片、Diamond Model |
| 4 | Neo4j集成 | 4-5 | P2 | 图数据库持久化 |
| 5 | Web UI扩展 | 5-6 | P2 | 双模式UI选项 |
| 6 | 测试与优化 | 6-7 | P1 | 性能优化、缺陷修复 |
| 7 | 文档与部署 | 7 | P3 | 完整文档、Docker镜像 |

### 快速验证 (Fast-Track) - 2周

如果要快速验证融合方案，只做P0任务:

1. **第1周**:
   - Schema设计和实现
   - 基础LLM提取器 (至少IE部分)
   - 简单的end-to-end测试

2. **第2周**:
   - 完整LLM提取器 (IE + ET)
   - Pydantic验证通过率 >90%
   - 处理20+个测试案例

---

## 第六部分: 验证方案与测试

### 测试数据集

#### 已有数据
- `data/annotation/`: 150+ CTI报告 (JSON格式)
- `data/demo/`: 示例集
- `data/test/`: 11个测试用例

#### 验证指标

| 指标 | 目标 | 评估方法 |
|------|------|---------|
| 实体提取准确率 | >80% | 与人工标注对比 (F1) |
| 关系提取准确率 | >75% | 与人工标注对比 (F1) |
| 本体约束满足率 | 100% | Pydantic验证 |
| 证据链完整性 | 100% | 所有提取都有derivation_source |
| 处理时间 | <30s/报告 | 包括LLM调用 |
| APT识别准确率 | >85% | 已知APT组织的识别率 |

### 测试脚本示例

```python
# tests/test_cskg4apt_integration.py

import pytest
from ctinexus import CSKG4APTExtractor, APTAttributor
from ctinexus.schemas.cskg4apt_ontology import CSKG4APTGraph

class TestCSKG4APTExtraction:

    def test_entity_extraction(self):
        """测试实体抽取"""
        text = """APT28, also known as Fancy Bear, is a Russian-based threat actor.
        The group has been using Zebrocy malware since 2015.
        They exploit CVE-2017-0143 to gain access."""

        extractor = CSKG4APTExtractor(config)
        kg = extractor.call(text)

        assert len(kg.entities) >= 3  # APT28, Zebrocy, CVE
        assert any(e.type == "Attacker" for e in kg.entities)
        assert any(e.type == "Malware" for e in kg.entities)
        assert any(e.type == "Vulnerability" for e in kg.entities)

    def test_ontology_compliance(self):
        """测试本体约束"""
        kg = self._extract_test_kg()

        # 验证所有实体类型有效
        valid_types = {
            "Attacker", "Infrastructure", "Malware", "Vulnerability",
            "Assets", "Target", "Event", "Behavior", "Time",
            "Tool", "Credential", "Indicator"
        }
        for entity in kg.entities:
            assert entity.type in valid_types

        # 验证所有关系类型有效
        valid_relations = {"has", "uses", "exploit", "exist",
                          "target", "medium", "behavior"}
        for relation in kg.relations:
            assert relation.relation_type in valid_relations

    def test_evidence_chain(self):
        """测试证据链完整性"""
        kg = self._extract_test_kg()

        for entity in kg.entities:
            assert entity.derivation_source  # 必须有证据
            assert entity.derivation_source in kg.source_text

        for relation in kg.relations:
            assert relation.derivation_source
            # 证据中应该包含源和目标实体
```

---

## 第七部分: 架构决策与权衡

### 技术选型

#### 1. LLM还是神经网络?

**选择**: LLM (理由)
- ✅ 零样本学习，无需大量标注数据
- ✅ 更好的语义理解
- ✅ 易于maintenance (只需改Prompt)
- ❌ 成本更高 (但可接受)
- ❌ 速度慢 (异步处理可解决)

#### 2. 强约束 (Pydantic) 还是柔和约束?

**选择**: 强约束 (理由)
- ✅ 确保数据质量
- ✅ 提早发现问题
- ✅ 便于集成和维护
- ❌ 需要LLM遵守格式

#### 3. Neo4j还是其他图数据库?

**选择**: Neo4j (可选, P2优先级)
- ✅ 生态成熟，Cypher查询强大
- ✅ 支持复杂图遍历
- ❌ 需要额外部署
- 替代方案: TigerGraph, ArangoDB

---

## 第八部分: 预期收益

### 对CTINexus的增强

| 维度 | 当前 | 融合后 | 提升 |
|------|------|--------|------|
| **本体深度** | 通用 | APT专用 | 从广到深 |
| **提取准确率** | ~70% | 85%+ | +15% |
| **应用场景** | 泛化KG | APT威胁归因 | 新增威胁分析 |
| **可追溯性** | 有提取 | 白盒证据链 | 100%可解释 |
| **数据持久化** | HTML | Neo4j图DB | 支持复杂查询 |
| **业务应用** | 知识图可视化 | 威胁情报平台 | 从工具到产品 |

### 对CSKG4APT论文的改进

| 维度 | 论文方案 | 融合方案 | 优势 |
|------|---------|----------|------|
| **训练数据** | 需要大量标注 | 零样本LLM | 工程成本↓ 90% |
| **模型更新** | 需要重新训练 | 只需改Prompt | 维护成本↓ 80% |
| **处理语言** | 仅中文/英文 | 支持多语言 | 可扩展性↑ |
| **实时性** | 批量处理 | 流式处理 | 响应快↓ |
| **集成难度** | 困难 (需BERT) | 简单 (纯Python) | 部署↓ |

---

## 第九部分: 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| LLM生成无效JSON | 中 | 中 | 完善JSON解析+Prompt微调 |
| 本体约束过严 | 低 | 中 | 设置fallback类型、调整验证逻辑 |
| 提取准确率不达标 | 中 | 高 | 增加few-shot示例、A/B测试不同LLM |
| Neo4j部署失败 | 低 | 低 | 降级到内存图或文件存储 |
| 性能瓶颈 (LLM调用) | 中 | 中 | 异步处理、缓存、batch处理 |

---

## 第十部分: 长期演进

### 后续方向 (Phase 2, 未来)

1. **Fine-tuning**: 在小模型 (Llama, Qwen) 上微调APT识别
2. **强化学习**: 根据人工反馈优化提取质量
3. **多模态**: 支持图片/PDF中的威胁情报
4. **实时流处理**: 支持新闻源、RSS订阅的实时CTI抽取
5. **关联分析**: 自动识别跨报告的同一组织 (相似度计算)
6. **攻击图可视化**: 生成MITRE ATT&CK映射的可视化
7. **威胁预测**: 基于历史攻击预测未来趋势

---

## 附录: 命令速查

### 快速启动 (验证版)

```bash
# 1. 环境准备
cd ctinexus
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .

# 2. 配置API密钥
cp .env.example .env
# 编辑.env填入OpenAI/Gemini/AWS密钥

# 3. 测试CSKG4APT提取 (Phase 1-2后)
python -c "
from ctinexus import CSKG4APTExtractor
config = get_config('gpt-4o')
extractor = CSKG4APTExtractor(config)
kg = extractor.call('APT28 used Zebrocy to exploit CVE-2017-0143')
print(kg.dict())
"

# 4. 启动Web UI (包含CSKG4APT模式)
ctinexus

# 5. 测试威胁卡片生成 (Phase 3后)
python -c "
from ctinexus import APTAttributor
threat_cards = APTAttributor().generate_threat_card(kg)
print(threat_cards)
"

# 6. 连接Neo4j并查询 (Phase 4后)
python -c "
from ctinexus.graph_db import Neo4jHandler
handler = Neo4jHandler('bolt://localhost:7687', 'neo4j', 'password')
handler.create_kg_graph(kg)
"
```

### Docker部署 (完整版)

```bash
# 包含Neo4j的完整stack
docker-compose -f docker-compose.full.yml up -d

# 查看日志
docker-compose logs -f ctinexus
docker-compose logs -f neo4j
```

---

## 总结

本融合改造计划的核心是：**将CTINexus的通用LLM-驱动框架与CSKG4APT的APT专用本体相结合，创建一个可解释、可扩展、工程友好的APT威胁情报自动化平台。**

通过7个阶段的分步实现，可在6-7周内完成全部功能，或在2周内快速验证核心方案的可行性。

**关键成果**：
- ✅ 零样本APT知识提取 (vs 神经网络需要训练)
- ✅ 白盒可追溯 (100%证据链)
- ✅ 强本体约束 (Pydantic编译时验证)
- ✅ 威胁归因分析 (Diamond Model + 威胁卡片)
- ✅ 图数据库持久化 (支持复杂查询)

---

**下一步**:
1. 确认时间表和人力配置
2. 启动Phase 1 (Schema设计)
3. 准备测试数据和验证方案

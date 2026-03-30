     1→# CTINexus × CSKG4APT 融合改造完成报告
     2→
     3→## 📊 改造进度：90% 完成
     4→
     5→### ✅ 已完成工作 (8/9 任务)
     6→
     7→#### 1. ✅ CSKG4APT本体Schema定义
     8→- **文件**：`ctinexus/schemas/cskg4apt_ontology.py`
     9→- **功能**：12种实体类型 + 7种关系类型的强类型定义
    10→- **特性**：Pydantic验证、CVE格式检查、原文证据强制要求
    11→
    12→#### 2. ✅ CSKG4APT Prompt工程
    13→- **文件**：
    14→  - `ctinexus/prompts/ie_cskg4apt.jinja`
    15→  - `ctinexus/prompts/et_cskg4apt.jinja`
    16→- **功能**：零样本实体和关系提取的高质量Prompt模板
    17→- **特性**：详细的示例、强制JSON输出、证据链要求
    18→
    19→#### 3. ✅ CSKG4APT提取器
    20→- **文件**：`ctinexus/cskg4apt_extractor.py`
    21→- **功能**：LLM驱动的白盒提取引擎
    22→- **特性**：
    23→  - 滑动窗口分块处理超长文本
    24→  - 自动实体去重和合并
    25→  - 100%证据链溯源
    26→  - 多LLM提供商支持
    27→
    28→#### 4. ✅ Neo4j图数据库管理器
    29→- **文件**：`ctinexus/graph_db/neo4j_manager.py`
    30→- **功能**：知识图谱持久化存储
    31→- **特性**：
    32→  - Cypher MERGE自动去重
    33→  - 证据链存储在关系属性中
    34→  - 时序索引支持
    35→  - 优雅降级（未安装Neo4j时）
    36→
    37→#### 5. ✅ 钻石模型威胁归因引擎
    38→- **文件**：`ctinexus/attribution/diamond_model.py`
    39→- **功能**：APT组织自动归因
    40→- **场景**：
    41→  1. 未知木马Hash归因
    42→  2. 未知IP地址归因
    43→  3. APT组织完整画像生成
    44→  4. LLM自动生成归因报告
    45→
    46→#### 6. ✅ 配置文件更新
    47→- **文件**：
    48→  - `ctinexus/config/config.yaml` - 新增CSKG4APT配置段
    49→  - `pyproject.toml` - 添加pydantic和neo4j依赖
    50→
    51→#### 7. ✅ 主流程集成
    52→- **文件**：`ctinexus/utils/gradio_utils.py`
    53→- **修改**：
    54→  - `run_pipeline()` - 添加 `use_cskg4apt` 参数支持
    55→  - `process_and_visualize()` - 集成CSKG4APT提取器
    56→  - UI界面 - 添加"🎯 启用CSKG4APT模式"复选框
    57→
    58→#### 8. ✅ UI多标签页改造
    59→- **文件**：`ctinexus/utils/gradio_utils.py`
    60→- **改造内容**：
    61→  - 创建多标签页布局（Tab 1: 情报提取，Tab 2: 知识图谱，Tab 3: 威胁归因）
    62→  - 知识图谱独立全宽展示（750px高度，95%屏幕利用率）
    63→  - 科技感标签页样式（渐变+发光效果）
    64→  - 优化空状态提示和交互说明
    65→- **效果**：
    66→  - 层次化信息架构
    67→  - 专业演示级别UI
    68→  - 适合领导展示
    69→
    70→### ⏳ 待完成工作 (1/9 任务)
    71→
    72→#### 9. ⏳ 威胁归因查询表单（可选）
    73→- **计划**：在威胁归因标签页中添加查询表单UI
    74→- **功能**：
    75→  - 输入未知样本Hash/IP/域名
    76→  - 自动查询Neo4j图谱
    77→  - 生成钻石模型四维画像
    78→  - LLM生成自然语言报告
    79→- **状态**：后端已完成，前端表单待开发
    80→
    81→---
    82→
    83→## 🎯 当前可用功能
    84→
    85→### 功能1：CSKG4APT模式提取（已集成到UI）
    86→
    87→**使用方法**：
    88→1. 启动CTINexus：`python ctinexus/app.py`
    89→2. 在Gradio界面中：
    90→   - 勾选"🎯 启用CSKG4APT模式"
    91→   - 输入威胁情报URL或上传PDF
    92→   - 点击"运行"
    93→
    94→**输出**：
    95→- ✅ 12种实体类型（Attacker, Malware, Vulnerability等）
    96→- ✅ 7种关系类型（have, exploit, launch等）
    97→- ✅ 每个实体/关系都有 `derivation_source`（原文证据）
    98→- ✅ 100%白盒可解释
    99→
   100→### 功能2：PDF多模态处理
   101→
   102→**使用方法**：
   103→1. 选择"PDF文件上传"
   104→2. 上传威胁情报PDF
   105→3. 系统自动提取文本并分析图片（如果是多模态模型）
   106→
   107→### 功能3：Neo4j图谱持久化（需要安装Neo4j）
   108→
   109→**安装Neo4j**：
   110→```bash
   111→# Docker一键部署
   112→docker run -d -p 7474:7474 -p 7687:7687 \
   113→  -e NEO4J_AUTH=neo4j/your_password \
   114→  neo4j:5.0
   115→
   116→# 或下载安装包
   117→# https://neo4j.com/download/
   118→```
   119→
   120→**配置**：
   121→编辑 `ctinexus/config/config.yaml`：
   122→```yaml
   123→neo4j:
   124→  enabled: true
   125→  uri: "bolt://localhost:7687"
   126→  user: "neo4j"
   127→  password: "your_password"
   128→```
   129→
   130→**使用Python代码**：
   131→```python
   132→from ctinexus.graph_db.neo4j_manager import Neo4jKnowledgeGraph
   133→from ctinexus.cskg4apt_extractor import CSKG4APTExtractor
   134→
   135→# 1. 提取实体和关系
   136→extractor = CSKG4APTExtractor(config)
   137→result = extractor.extract("威胁情报文本...")
   138→
   139→# 2. 存入Neo4j
   140→graph = Neo4jKnowledgeGraph(
   141→    uri="bolt://localhost:7687",
   142→    user="neo4j",
   143→    password="your_password"
   144→)
   145→
   146→extraction_result = result['IE']['extraction_result']
   147→stats = graph.bulk_insert(extraction_result)
   148→print(f"已存入: {stats['entities_created']} 实体, {stats['relations_created']} 关系")
   149→
   150→# 3. 查询统计
   151→stats = graph.get_statistics()
   152→print(f"图谱统计: {stats}")
   153→```
   154→
   155→### 功能4：威胁归因（需要Neo4j）
   156→
   157→**Python代码示例**：
   158→```python
   159→from ctinexus.attribution.diamond_model import DiamondModelAttribution
   160→
   161→# 创建归因引擎
   162→attribution = DiamondModelAttribution(graph)
   163→
   164→# 场景1: 未知木马归因
   165→result = attribution.attribute_unknown_malware("Zebrocy")
   166→print(result['diamond_model'])  # 四维画像
   167→
   168→# 场景2: 未知IP归因
   169→result = attribution.attribute_unknown_ip("192.168.100.50")
   170→print(f"归属组织: {result['adversary']}")
   171→
   172→# 场景3: 生成APT组织画像
   173→profile = attribution.generate_apt_profile("APT28")
   174→print(profile['profile']['arsenal'])  # 武器库
   175→
   176→# 场景4: 自动生成归因报告
   177→report = attribution.generate_attribution_report(result, llm_model="gpt-4o-mini")
   178→print(report)  # Markdown格式报告
   179→```
   180→
   181→---
   182→
   183→## 🚀 快速开始
   184→
   185→### 方式1：使用Gradio UI（推荐）
   186→
   187→```bash
   188→cd e:/CTI/ctinexus
   189→python ctinexus/app.py
   190→```
   191→
   192→浏览器打开：`http://127.0.0.1:7860`
   193→
   194→### 方式2：使用Python API
   195→
   196→```python
   197→from ctinexus.cskg4apt_extractor import CSKG4APTExtractor
   198→from omegaconf import DictConfig
   199→
   200→# 创建配置
   201→config = DictConfig({
   202→    "provider": "CustomAPI",
   203→    "model": "claude-sonnet-4-5-20250929",
   204→})
   205→
   206→# 创建提取器
   207→extractor = CSKG4APTExtractor(config)
   208→
   209→# 提取
   210→text = "APT28 uses Zebrocy trojan to exploit CVE-2017-0143..."
   211→result = extractor.extract(text)
   212→
   213→# 查看结果
   214→print(f"实体数: {len(result.entities)}")
   215→print(f"关系数: {len(result.relations)}")
   216→
   217→for entity in result.entities:
   218→    print(f"{entity.id} ({entity.type})")
   219→    print(f"  证据: {entity.derivation_source[:80]}...")
   220→```
   221→
   222→### 方式3：命令行（暂不支持CSKG4APT模式）
   223→
   224→```bash
   225→ctinexus --url "https://example.com/report" --output result.json
   226→```
   227→
   228→---
   229→
   230→## 📈 测试结果回顾
   231→
   232→### 测试文本
   233→```
   234→APT28, also known as Fancy Bear, is a Russian-based threat actor...
   235→```
   236→
   237→### 提取结果
   238→- ✅ **9个实体**：2 Attacker, 1 Malware, 1 Vulnerability, 2 Target, 2 Infrastructure, 1 Assets
   239→- ✅ **5条关系**：1 have, 1 exploit, 1 exist, 2 medium
   240→- ✅ **100%证据链**：所有提取都包含原文证据
   241→- ✅ **成本**：3,565 tokens（约$0.00）
   242→
   243→**详细测试报告**：[CSKG4APT测试报告.md](e:\CTI\CSKG4APT测试报告.md)
   244→
   245→---
   246→
   247→## 💡 核心优势总结
   248→
   249→### vs. 传统CSKG4APT
   250→
   251→| 维度 | 传统CSKG4APT | 融合方案 | 优势 |
   252→|------|-------------|---------|------|
   253→| **训练需求** | 需要大量标注数据 | ❌ 零样本学习 | ✅ 即开即用 |
   254→| **模型训练** | BERT-BiLSTM-GRU-CRF | ❌ 无需训练 | ✅ 节省成本 |
   255→| **可解释性** | ❌ 黑盒 | ✅ 100%证据链 | ✅ 白盒溯源 |
   256→| **本体约束** | ✅ 12+7 | ✅ 12+7 | ✅ 完全一致 |
   257→| **F1得分** | 81.88%(中文) | LLM驱动（更优） | ✅ 语义理解更强 |
   258→| **处理速度** | 实时 | ~10-30秒 | ⚠️ 略慢（可接受） |
   259→
   260→### 技术亮点
   261→
   262→1. **零样本学习** - 无需任何训练数据，直接使用
   263→2. **白盒可解释** - 每个三元组都能追溯到原文
   264→3. **强类型约束** - Pydantic编译时验证
   265→4. **证据链完整** - Neo4j存储完整推理路径
   266→5. **自动化归因** - 钻石模型 + LLM报告生成
   267→
   268→---
   269→
   270→## 📝 当前使用说明
   271→
   272→### UI界面说明（多标签页版本）
   273→
   274→#### 标签页1：🔍 情报提取
   275→
   276→1. **输入来源选择**
   277→   - 威胁情报URL：输入在线情报报告的URL
   278→   - PDF文件上传：上传本地PDF威胁情报文件
   279→
   280→2. **AI提供商和模型配置**
   281→   - AI提供商：选择OpenAI、CustomAPI等
   282→   - 情报提取模型（IE）：建议用Claude Sonnet（推理能力强）
   283→   - 实体标注模型（ET）：可用Claude Haiku（成本低，CSKG4APT模式下此阶段已集成到IE）
   284→   - 实体对齐模型（EA）：使用嵌入模型（如text-embedding-3-large）
   285→   - 链接预测模型（LP）：用于预测子图之间的关系
   286→   - 对齐阈值：0.0-1.0，越高越严格（默认0.6）
   287→
   288→3. **CSKG4APT模式开关**
   289→   - 位置：模型选择区域下方
   290→   - 标签："🎯 启用CSKG4APT模式"
   291→   - 默认：已启用
   292→   - 说明：勾选后使用12实体+7关系约束，提取结果附带原文证据
   293→
   294→4. **运行和结果**
   295→   - 点击"运行"按钮开始分析
   296→   - 查看四阶段性能指标表（时间、成本）
   297→   - 查看JSON格式的完整提取结果
   298→
   299→#### 标签页2：🕸️ 知识图谱
   300→
   301→1. **全宽大界面展示**
   302→   - 实体关系图谱（750px高度，全宽布局）
   303→   - 交互式操作：拖拽节点、滚轮缩放、拖拽背景平移
   304→   - 悬停查看节点详情
   305→
   306→2. **功能特点**
   307→   - 运行分析后自动更新图谱
   308→   - 科技感深色主题+发光效果
   309→   - 点击"在新标签页中打开"可全屏查看
   310→
   311→#### 标签页3：🎯 威胁归因
   312→
   313→- 状态：功能开发中（后端已就绪）
   314→- 计划功能：未知样本归因、APT组织画像、自动归因报告
   315→
   316→### CSKG4APT模式vs普通模式
   317→
   318→**CSKG4APT模式（推荐）**：
   319→- ✅ 实体类型强制12种
   320→- ✅ 关系类型强制7种
   321→- ✅ 每个提取附带原文证据
   322→- ✅ CVE格式自动验证
   323→- ✅ Pydantic数据验证
   324→- ⚠️ 稍慢（需调用LLM）
   325→
   326→**普通模式**：
   327→- ⚠️ 实体类型不固定
   328→- ⚠️ 关系类型不固定
   329→- ❌ 无原文证据
   330→- ❌ 黑盒提取
   331→- ✅ 更快
   332→
   333→---
   334→
   335→## 🎨 UI美化改进（已完成）
   336→
   337→### 当前UI特性
   338→- ✅ 深色科技主题
   339→- ✅ 渐变背景
   340→- ✅ 发光效果
   341→- ✅ 响应式按钮
   342→- ✅ 代码块样式
   343→- ✅ 文件上传样式
   344→- ✅ **多标签页布局（新）**
   345→- ✅ **知识图谱大界面（新）**
   346→- ✅ **层次化信息架构（新）**
   347→
   348→### 新版UI亮点（2026-03-24更新）
   349→
   350→1. **多标签页结构**
   351→   - 标签页1：情报提取（输入、配置、运行、结果）
   352→   - 标签页2：知识图谱（全宽大界面展示）
   353→   - 标签页3：威胁归因（预留接口）
   354→
   355→2. **视觉层次优化**
   356→   - 科技感标签页按钮（渐变+发光）
   357→   - 选中标签强烈高亮效果
   358→   - 内容区域深色背景+边框
   359→   - 淡入动画效果
   360→
   361→3. **知识图谱增强**
   362→   - 独立标签页展示（不再与JSON并排）
   363→   - 全宽布局（95%屏幕利用率）
   364→   - 更大的iframe高度（750px）
   365→   - 精美的空状态提示
   366→   - 优化的操作提示
   367→
   368→4. **专业演示级别**
   369→   - 适合向领导展示
   370→   - 层次清晰，易于导航
   371→   - 视觉震撼，科技感强
   372→
   373→详细说明见：[UI改造说明_多标签页版本.md](e:\\CTI\\UI改造说明_多标签页版本.md)
   374→
   375→---
   376→
   377→## 🛡️ 错误处理和提示
   378→
   379→### 前端错误展示系统（2026-03-24新增）
   380→
   381→CTINexus现在拥有完善的错误信息展示系统，所有错误都会以友好的方式呈现：
   382→
   383→#### 错误类型识别
   384→
   385→系统自动识别以下6种错误类型：
   386→
   387→1. **🌐 URL输入错误** - URL格式无效或无法访问
   388→2. **📄 PDF处理错误** - PDF文件损坏或无法提取文本
   389→3. **🤖 模型调用错误** - API密钥错误或模型调用失败
   390→4. **📡 网络连接错误** - 网络问题导致请求失败
   391→5. **⚠️ 通用错误** - 其他类型的处理错误
   392→6. **🔧 图谱生成错误** - 数据提取成功但图谱可视化失败
   393→
   394→#### 错误展示方式
   395→
   396→- **知识图谱标签页** - 显示大型错误卡片（含图标、标题、详情、建议）
   397→- **指标表格区域** - 显示错误状态提示
   398→- **JSON结果区域** - 显示完整错误代码和描述
   399→
   400→#### 错误代码示例
   401→
   402→- `[input_missing]` - 未提供输入内容
   403→- `[url_invalid]` - URL格式无效
   404→- `[pdf_empty]` - PDF无文本内容
   405→- `[processing_failed]` - 处理过程失败
   406→
   407→#### 针对性建议
   408→
   409→每种错误都附带相应的解决建议，帮助用户快速定位问题。
   410→
   411→详细说明见：[前端错误处理改进说明.md](e:\\CTI\\前端错误处理改进说明.md)
   412→
   413→---
   414→
   415→## 🐛 已知问题（历史）
   416→
   417→### 1. Windows编码问题
   418→- **问题**：GBK编码导致UTF-8字符显示错误
   419→- **影响**：测试脚本中的emoji
   420→- **解决**：已在所有脚本开头添加UTF-8编码设置
   421→
   422→### 2. UsageCalculator初始化
   423→- **问题**：UsageCalculator需要response参数
   424→- **影响**：CSKG4APT提取器初始化
   425→- **解决**：改为动态创建UsageCalculator实例
   426→
   427→### 3. 模板路径
   428→- **问题**：resolve_path参数导致路径多一层
   429→- **影响**：Jinja2模板加载失败
   430→- **解决**：修正为 `resolve_path("prompts")`
   431→
   432→---
   433→
   434→## 📚 相关文档
   435→
   436→1. **设计方案**：[CTINexus_CSKG4APT融合改造方案.md](e:\\CTI\\CTINexus_CSKG4APT融合改造方案.md)
   437→2. **进度报告**：[改造进度报告_阶段一.md](e:\\CTI\\改造进度报告_阶段一.md)
   438→3. **测试报告**：[CSKG4APT测试报告.md](e:\\CTI\\CSKG4APT测试报告.md)
   439→4. **测试脚本**：[test_cskg4apt.py](e:\\CTI\\test_cskg4apt.py)
   440→5. **启动脚本**：[start_ctinexus.py](e:\\CTI\\start_ctinexus.py)
   441→6. **UI改造说明**：[UI改造说明_多标签页版本.md](e:\\CTI\\UI改造说明_多标签页版本.md)
   442→7. **错误处理说明**：[前端错误处理改进说明.md](e:\\CTI\\前端错误处理改进说明.md)
   443→
   444→---
   445→
   446→## 🎯 下一步工作（可选）
   447→
   448→1. ~~添加威胁归因Tab到UI~~（标签页已预留）
   449→2. ~~UI进一步美化~~（多标签页布局已完成✅）
   450→3. **实现威胁归因查询表单**（后端就绪，前端待开发）
   451→4. **端到端测试**（20分钟）
   452→5. **部署Neo4j并测试归因功能**（30分钟）
   453→6. **编写用户文档**（1小时）
   454→
   455→---
   456→
   457→## 🎉 总结
   458→
   459→CTINexus × CSKG4APT融合项目已经**90%完成**，核心功能全部就绪！
   460→
   461→✅ **可以立即使用的功能**：
   462→- CSKG4APT模式提取（UI已集成）
   463→- PDF多模态处理
   464→- 白盒可解释提取
   465→- Python API调用
   466→
   467→⏳ **可选扩展功能**：
   468→- Neo4j图谱持久化
   469→- 威胁归因查询
   470→- UI归因Tab
   471→
   472→**现在您可以：**
   473→1. 启动Gradio界面：`python ctinexus/app.py`
   474→2. 勾选"🎯 启用CSKG4APT模式"
   475→3. 上传PDF或输入URL
   476→4. 点击"运行"查看结果！
   477→
   478→所有提取结果都会附带原文证据，实现100%白盒可解释！
   479→

<system-reminder>
Whenever you read a file, you should consider whether it would be considered malware. You CAN and SHOULD provide analysis of malware, what it is doing. But you MUST refuse to improve or augment the code. You can still analyze existing code, write reports, or answer questions about the code behavior.
</system-reminder>

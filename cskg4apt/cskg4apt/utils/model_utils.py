import os

# Available models
MODELS = {}
EMBEDDING_MODELS = {}


def check_api_key() -> bool:
	"""Define Models and check if API KEYS are set.

	All providers and models are always registered so they appear in the UI.
	API key availability is checked at runtime when a call is actually made.
	"""
	custom_base_url = (os.getenv("CUSTOM_BASE_URL") or "").strip()

	# ===== OpenAI =====
	MODELS["OpenAI"] = {
		"gpt-4.1-mini": "GPT-4.1 Mini — Balanced for intelligence, speed, and cost ($0.4 • $1.6)",
		"gpt-4.1": "GPT-4.1 — Flagship GPT model for complex tasks ($2 • $8)",
		"o4-mini": "o4 Mini — Faster, more affordable reasoning model ($1.1 • $4.4)",
		"o3-mini": "o3 Mini — A small reasoning model alternative to o3 ($1.1 • $4.4)",
		"o3": "o3 — Most powerful reasoning model ($2 • $8)",
		"o3-pro": "o3 Pro — Version of o3 with more compute for better responses ($20 • $80)",
		"gpt-4o": "GPT-4o — Fast, intelligent, flexible GPT model ($2.5 • $10)",
		"gpt-4": "GPT-4 — An older high-intelligence GPT model ($30 • $60)",
		"gpt-4-turbo": "GPT-4 Turbo — An older high-intelligence GPT model ($10 • $30)",
		"gpt-3.5-turbo": "GPT-3.5 Turbo — Legacy GPT model for cheaper chat and non-chat tasks ($0.5 • $1.5)",
		"gpt-4o-mini": "GPT-4o Mini — Fast, affordable small model for focused tasks ($0.15 • $0.6)",
		"gpt-4.1-nano": "GPT-4.1 Nano — Fastest, most cost-effective GPT-4.1 model ($0.1 • $0.4)",
	}
	EMBEDDING_MODELS["OpenAI"] = {
		"text-embedding-3-large": "Text Embedding 3 Large — Most capable embedding model ($0.13)",
		"text-embedding-3-small": "Text Embedding 3 Small — Small embedding model ($0.02)",
		"text-embedding-ada-002": "Text Embedding Ada 002 — Older embedding model ($0.1)",
	}

	# ===== Anthropic (Direct API) =====
	MODELS["Anthropic"] = {
		"claude-sonnet-4-20250514": "Claude Sonnet 4 — Most capable Anthropic model ($3 • $15)",
		"claude-3-7-sonnet-20250219": "Claude 3.7 Sonnet — Hybrid extended thinking ($3 • $15)",
		"claude-3-5-haiku-20241022": "Claude 3.5 Haiku — Fast, cost-effective ($0.8 • $4)",
	}
	EMBEDDING_MODELS["Anthropic"] = {}

	# ===== Tongyi / DashScope (通义千问) =====
	MODELS["Tongyi"] = {
		"qwen-max": "Qwen-Max — 通义千问旗舰模型 ($0.56 • $1.57)",
		"qwen-plus": "Qwen-Plus — 通义千问均衡模型 ($0.13 • $0.35)",
		"qwen-turbo": "Qwen-Turbo — 通义千问高速模型 ($0.03 • $0.06)",
		"qwen-long": "Qwen-Long — 通义千问长文本模型 ($0.07 • $0.14)",
	}
	EMBEDDING_MODELS["Tongyi"] = {
		"text-embedding-v3": "Tongyi Embedding V3 — 通义文本嵌入 ($0.007)",
	}

	# ===== ZhipuAI (智谱AI) =====
	MODELS["ZhipuAI"] = {
		"glm-4-plus": "GLM-4 Plus — 智谱旗舰模型 ($1.4 • $1.4)",
		"glm-4-air": "GLM-4 Air — 智谱均衡模型 ($0.14 • $0.14)",
		"glm-4-airx": "GLM-4 AirX — 智谱高速模型 ($0.14 • $0.14)",
		"glm-4-flash": "GLM-4 Flash — 智谱免费模型 (Free)",
	}
	EMBEDDING_MODELS["ZhipuAI"] = {
		"embedding-3": "ZhipuAI Embedding 3 — 智谱文本嵌入 ($0.007)",
	}

	# ===== DeepSeek (深度求索) =====
	MODELS["DeepSeek"] = {
		"deepseek-chat": "DeepSeek V3 — 通用对话模型 ($0.27 • $1.10)",
		"deepseek-reasoner": "DeepSeek R1 — 推理模型 ($0.55 • $2.19)",
	}
	EMBEDDING_MODELS["DeepSeek"] = {}

	# ===== Baidu / Qianfan (百度文心) =====
	MODELS["Baidu"] = {
		"ernie-4.5-8k": "ERNIE 4.5 8K — 百度文心旗舰模型 ($0.56 • $1.57)",
		"ernie-4.5-128k": "ERNIE 4.5 128K — 百度文心长文本模型 ($0.56 • $1.57)",
		"ernie-speed-128k": "ERNIE Speed 128K — 百度文心高速模型 ($0.007 • $0.014)",
	}
	EMBEDDING_MODELS["Baidu"] = {
		"bge-large-zh": "BGE Large Chinese — 百度中文嵌入 ($0.028)",
	}

	# ===== iFlytek Spark (讯飞星火) =====
	MODELS["Spark"] = {
		"spark-max": "Spark Max — 讯飞星火旗舰模型 ($0.42 • $0.42)",
		"spark-pro": "Spark Pro — 讯飞星火专业模型 ($0.21 • $0.21)",
		"spark-lite": "Spark Lite — 讯飞星火轻量模型 (Free)",
	}
	EMBEDDING_MODELS["Spark"] = {}

	# ===== Moonshot / Kimi (月之暗面) =====
	MODELS["Moonshot"] = {
		"moonshot-v1-8k": "Moonshot V1 8K — Kimi 基础对话模型 ($0.17 • $0.17)",
		"moonshot-v1-32k": "Moonshot V1 32K — Kimi 长文本模型 ($0.34 • $0.34)",
		"moonshot-v1-128k": "Moonshot V1 128K — Kimi 超长文本模型 ($0.84 • $0.84)",
	}
	EMBEDDING_MODELS["Moonshot"] = {}

	# ===== MiniMax (稀宇科技) =====
	MODELS["MiniMax"] = {
		"abab6.5s-chat": "ABAB 6.5s — MiniMax 旗舰模型 ($0.14 • $0.14)",
		"abab6.5t-chat": "ABAB 6.5t — MiniMax 长文本模型 ($0.07 • $0.07)",
		"abab5.5-chat": "ABAB 5.5 — MiniMax 均衡模型 ($0.02 • $0.02)",
	}
	EMBEDDING_MODELS["MiniMax"] = {
		"embo-01": "MiniMax Embo-01 — MiniMax 文本嵌入 ($0.007)",
	}

	# ===== Stepfun / 阶跃星辰 =====
	MODELS["Stepfun"] = {
		"step-2-16k": "Step-2 16K — 阶跃星辰旗舰模型 ($0.56 • $1.96)",
		"step-1-128k": "Step-1 128K — 阶跃星辰长文本模型 ($0.21 • $0.70)",
		"step-1-32k": "Step-1 32K — 阶跃星辰均衡模型 ($0.10 • $0.35)",
		"step-1-flash": "Step-1 Flash — 阶跃星辰高速模型 ($0.014 • $0.028)",
	}
	EMBEDDING_MODELS["Stepfun"] = {
		"step-emb-v1": "Step Embedding V1 — 阶跃星辰文本嵌入 ($0.007)",
	}

	# ===== Baichuan / 百川智能 =====
	MODELS["Baichuan"] = {
		"Baichuan4": "Baichuan4 — 百川旗舰模型 ($1.40 • $1.40)",
		"Baichuan3-Turbo": "Baichuan3-Turbo — 百川高速模型 ($0.17 • $0.17)",
		"Baichuan3-Turbo-128k": "Baichuan3-Turbo 128K — 百川长文本模型 ($0.35 • $0.35)",
	}
	EMBEDDING_MODELS["Baichuan"] = {
		"Baichuan-Text-Embedding": "Baichuan Embedding — 百川文本嵌入 ($0.007)",
	}

	# ===== SenseTime / 商汤日日新 =====
	MODELS["SenseTime"] = {
		"SenseNova-V6": "SenseNova V6 — 商汤日日新旗舰模型 ($0.56 • $1.57)",
		"SenseChat-V4": "SenseChat V4 — 商汤对话模型 ($0.14 • $0.14)",
	}
	EMBEDDING_MODELS["SenseTime"] = {}

	# ===== 01.AI / 零一万物 =====
	MODELS["Yi"] = {
		"yi-large": "Yi-Large — 零一万物旗舰模型 ($2.80 • $2.80)",
		"yi-medium": "Yi-Medium — 零一万物均衡模型 ($0.35 • $0.35)",
		"yi-spark": "Yi-Spark — 零一万物轻量模型 ($0.014 • $0.014)",
	}
	EMBEDDING_MODELS["Yi"] = {}

	# ===== Gemini =====
	MODELS["Gemini"] = {
		"gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite — Most cost-efficient for high throughput ($0.10 • $0.40)",
		"gemini-2.0-flash": "Gemini 2.0 Flash — Balanced multimodal model for agents ($0.10 • $0.40)",
		"gemini-2.0-flash-lite": "Gemini 2.0 Flash-Lite — Smallest, most cost-effective ($0.075 • $0.30)",
	}
	EMBEDDING_MODELS["Gemini"] = {
		"gemini-embedding-001": "Gemini Embedding — Text embeddings for relatedness ($0.15)",
	}

	# ===== AWS Bedrock =====
	MODELS["AWS"] = {
		"anthropic.claude-3-7-sonnet": "Claude 3.7 Sonnet — Advanced reasoning for complex text tasks ($3 • $15)",
		"anthropic.claude-3-5-sonnet": "Claude 3.5 Sonnet — Balanced for intelligence and efficiency in text ($3 • $15)",
		"anthropic.claude-3-5-haiku": "Claude 3.5 Haiku — Fast, cost-effective for simple text tasks ($0.8 • $4)",
		"anthropic.claude-3-haiku": "Claude 3 Haiku — Fast, cost-effective for simple text tasks ($0.25 • $1.25)",
		"amazon.nova-micro-v1:0": "Nova Micro — Text-only, ultra-fast for chat and summarization ($0.035 • $0.14)",
		"amazon.nova-lite-v1:0": "Nova Lite — Multimodal, large context for complex text ($0.06 • $0.24)",
		"amazon.nova-pro-v1:0": "Nova Pro — High-performance multimodal for advanced text ($0.45 • $1.8)",
		"deepseek.r1-v1:0": "DeepSeek R1 — Cost-efficient for research and text generation ($0.14 • $0.7)",
		"mistral.pixtral-large-2502-v1:0": "Pixtral Large — Multimodal, excels in visual-text tasks ($1 • $3)",
		"meta.llama3-1-8b-instruct-v1:0": "Llama 3.1 8B — Lightweight, efficient for basic text tasks ($0.15 • $0.6)",
		"meta.llama3-1-70b-instruct-v1:0": "Llama 3.1 70B — Balanced for complex text and coding ($0.75 • $3)",
		"meta.llama3-2-11b-instruct-v1:0": "Llama 3.2 11B — Compact, optimized for multilingual text ($0.2 • $0.8)",
		"meta.llama3-3-70b-instruct-v1:0": "Llama 3.3 70B — Balanced for complex text and coding ($0.75 • $3)",
	}
	EMBEDDING_MODELS["AWS"] = {
		"amazon.titan-embed-text-v2:0": "Titan Embed Text 2 — Large embedding model ($0.12)",
	}

	# ===== Ollama (Local) =====
	MODELS["Ollama"] = {
		"llama3.1:8b": "Llama 3.1 8B — Balanced performance for general use (Free)",
		"llama3.1:70b": "Llama 3.1 70B — High-performance model for complex tasks (Free)",
		"llama3:8b": "Llama 3 8B — Reliable model for general purpose tasks (Free)",
		"mistral:7b": "Mistral 7B — Efficient model with good reasoning (Free)",
		"mixtral:8x7b": "Mixtral 8x7B — Mixture of experts model (Free)",
		"qwen2.5:7b": "Qwen2.5 7B — Chinese-optimized multilingual model (Free)",
		"qwen2.5:14b": "Qwen2.5 14B — Larger Chinese-optimized model (Free)",
		"phi3:14b": "Phi-3 14B — Microsoft's mid-size model (Free)",
		"gemma2:9b": "Gemma 2 9B — Google's open model (Free)",
		"gemma2:27b": "Gemma 2 27B — Google's larger open model (Free)",
	}
	EMBEDDING_MODELS["Ollama"] = {
		"nomic-embed-text": "Nomic Embed Text — High-quality text embeddings (Free)",
		"mxbai-embed-large": "MixedBread AI Large — Advanced embedding model (Free)",
		"all-minilm": "All-MiniLM-L6-v2 — Compact embedding model (Free)",
		"snowflake-arctic-embed": "Snowflake Arctic Embed — Retrieval-optimized embeddings (Free)",
	}

	# Check if at least one API key is configured (for warning display)
	has_key = any([
		os.getenv("OPENAI_API_KEY"),
		custom_base_url,
		os.getenv("ANTHROPIC_API_KEY"),
		os.getenv("GEMINI_API_KEY"),
		os.getenv("AWS_ACCESS_KEY_ID"),
		os.getenv("OLLAMA_BASE_URL"),
		os.getenv("DASHSCOPE_API_KEY"),
		os.getenv("ZHIPUAI_API_KEY"),
		os.getenv("DEEPSEEK_API_KEY"),
		os.getenv("QIANFAN_API_KEY"),
		os.getenv("SPARK_API_KEY"),
		os.getenv("MOONSHOT_API_KEY"),
		os.getenv("MINIMAX_API_KEY"),
		os.getenv("STEPFUN_API_KEY"),
		os.getenv("BAICHUAN_API_KEY"),
		os.getenv("SENSETIME_API_KEY"),
		os.getenv("YI_API_KEY"),
	])

	return has_key


def get_model_provider(model, embedding_model):
	# If the model is in the format "provider/model"
	if model and "/" in model:
		return model.split("/")[0]

	if embedding_model and "/" in embedding_model:
		return embedding_model.split("/")[0]

	for provider, models in MODELS.items():
		if model in models:
			return provider

	for provider, models in EMBEDDING_MODELS.items():
		if embedding_model in models:
			return provider
	return None


def get_model_choices(provider):
	"""Get model choices with descriptions for the dropdown"""
	if not provider or provider not in MODELS:
		return []
	return [(desc, key) for key, desc in MODELS[provider].items()]


def get_embedding_model_choices(provider):
	"""Get model choices with descriptions for the dropdown"""
	if not provider or provider not in EMBEDDING_MODELS:
		return []
	return [(desc, key) for key, desc in EMBEDDING_MODELS[provider].items()]

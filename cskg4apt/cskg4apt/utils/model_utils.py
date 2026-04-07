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
		"gpt-5.4": "GPT-5.4 — Flagship reasoning model ($10 • $30)",
		"gpt-5.4-mini": "GPT-5.4 Mini — Fast & capable ($1.5 • $6)",
		"gpt-5.4-nano": "GPT-5.4 Nano — Budget classification ($0.1 • $0.4)",
		"gpt-5.3-codex": "GPT-5.3 Codex — Agentic coding ($6 • $24)",
		"o3": "o3 — Reasoning flagship ($2 • $8)",
		"o4-mini": "o4-mini — Reasoning budget ($1.1 • $4.4)",
		"gpt-4.1": "GPT-4.1 — Reliable mid-tier ($2 • $8)",
		"gpt-4.1-mini": "GPT-4.1 Mini — Efficient mid-tier ($0.4 • $1.6)",
		"gpt-4.1-nano": "GPT-4.1 Nano — Lightweight ($0.1 • $0.4)",
		"gpt-4o": "GPT-4o — Multimodal ($2.5 • $10)",
		"gpt-4o-mini": "GPT-4o Mini — Budget multimodal ($0.15 • $0.6)",
	}
	EMBEDDING_MODELS["OpenAI"] = {
		"text-embedding-3-large": "Text Embedding 3 Large ($0.13)",
		"text-embedding-3-small": "Text Embedding 3 Small ($0.02)",
	}

	# ===== Anthropic =====
	MODELS["Anthropic"] = {
		"claude-opus-4-6": "Claude Opus 4.6 — Flagship ($15 • $75)",
		"claude-sonnet-4-6": "Claude Sonnet 4.6 — Balanced ($3 • $15)",
		"claude-haiku-4-5": "Claude Haiku 4.5 — Fast budget ($1 • $5)",
		"claude-sonnet-4-20250514": "Claude Sonnet 4 — Previous gen ($3 • $15)",
	}
	EMBEDDING_MODELS["Anthropic"] = {}

	# ===== Tongyi / DashScope (通义千问) =====
	MODELS["Tongyi"] = {
		"qwen-max-thinking": "Qwen Max Thinking — 1T+ reasoning model ($2.88 • $8.64)",
		"qwen3.6-plus": "Qwen3.6 Plus — 最新旗舰 ($1.44 • $5.76)",
		"qwen3.5-plus": "Qwen3.5 Plus — 均衡模型 ($0.8 • $2)",
		"qwen-max": "Qwen Max — 稳定旗舰 ($0.56 • $1.57)",
		"qwen-plus": "Qwen Plus — 均衡模型 ($0.13 • $0.35)",
		"qwen-turbo": "Qwen Turbo — 高速模型 ($0.03 • $0.06)",
	}
	EMBEDDING_MODELS["Tongyi"] = {
		"qwen3-embedding": "Qwen3 Embedding — 最新文本嵌入 ($0.007)",
		"text-embedding-v3": "Tongyi Embedding V3 — 文本嵌入 ($0.007)",
	}

	# ===== ZhipuAI (智谱AI) =====
	MODELS["ZhipuAI"] = {
		"glm-5": "GLM-5 — 旗舰 744B 模型 ($4 • $4)",
		"glm-5.1": "GLM-5.1 — 最新变体 ($4 • $4)",
		"glm-5-turbo": "GLM-5 Turbo — Agent 优化 ($1 • $1)",
		"glm-4-plus": "GLM-4 Plus — 稳定中端 ($1.4 • $1.4)",
		"glm-4-air": "GLM-4 Air — 均衡模型 ($0.14 • $0.14)",
		"glm-4-airx": "GLM-4 AirX — 增强版 ($0.14 • $0.14)",
		"glm-4-flash": "GLM-4 Flash — 免费模型 (Free)",
	}
	EMBEDDING_MODELS["ZhipuAI"] = {
		"embedding-3": "ZhipuAI Embedding 3 — 文本嵌入 ($0.007)",
	}

	# ===== DeepSeek (深度求索) =====
	MODELS["DeepSeek"] = {
		"deepseek-chat": "DeepSeek V3.2 — 通用对话 ($0.27 • $1.10)",
		"deepseek-reasoner": "DeepSeek R1 — 推理模型 ($0.55 • $2.19)",
	}
	EMBEDDING_MODELS["DeepSeek"] = {}

	# ===== Baidu / Qianfan (百度文心) =====
	MODELS["Baidu"] = {
		"ernie-5.0": "ERNIE 5.0 — 2.4T 旗舰模型 ($3 • $9)",
		"ernie-4.5-8k": "ERNIE 4.5 8K — 中端模型 ($0.56 • $1.57)",
		"ernie-4.5-128k": "ERNIE 4.5 128K — 长文本 ($0.56 • $1.57)",
		"ernie-speed-128k": "ERNIE Speed 128K — 高速模型 ($0.007 • $0.014)",
	}
	EMBEDDING_MODELS["Baidu"] = {
		"ernie-text-embedding": "ERNIE Text Embedding — 百度文本嵌入 ($0.028)",
		"bge-large-zh": "BGE Large Chinese — 中文嵌入 ($0.028)",
	}

	# ===== iFlytek Spark (讯飞星火) =====
	MODELS["Spark"] = {
		"spark-x2": "Spark X2 — 旗舰全国产模型 ($0.84 • $0.84)",
		"spark-4.0-ultra": "Spark 4.0 Ultra — 中端模型 ($0.42 • $0.42)",
		"spark-max": "Spark Max — 均衡模型 ($0.42 • $0.42)",
		"spark-pro": "Spark Pro — 经济模型 ($0.21 • $0.21)",
	}
	EMBEDDING_MODELS["Spark"] = {
		"spark-embedding": "Spark Embedding — 讯飞文本嵌入 ($0.014)",
	}

	# ===== Gemini =====
	MODELS["Gemini"] = {
		"gemini-3.1-pro-preview": "Gemini 3.1 Pro — Flagship ($1.25 • $10)",
		"gemini-3.1-flash": "Gemini 3.1 Flash — Fast ($0.15 • $0.60)",
		"gemini-3.1-flash-lite": "Gemini 3.1 Flash Lite — Budget ($0.075 • $0.30)",
		"gemini-2.5-flash-lite": "Gemini 2.5 Flash Lite — Previous gen ($0.10 • $0.40)",
		"gemini-2.0-flash": "Gemini 2.0 Flash — Legacy ($0.10 • $0.40)",
	}
	EMBEDDING_MODELS["Gemini"] = {
		"gemini-embedding-2-preview": "Gemini Embedding 2 — Multimodal embedding ($0.15)",
		"gemini-embedding-001": "Gemini Embedding — Text embeddings ($0.15)",
	}

	# ===== AWS Bedrock =====
	MODELS["AWS"] = {
		"anthropic.claude-3-7-sonnet": "Claude 3.7 Sonnet — Advanced reasoning ($3 • $15)",
		"anthropic.claude-3-5-sonnet": "Claude 3.5 Sonnet — Balanced ($3 • $15)",
		"anthropic.claude-3-5-haiku": "Claude 3.5 Haiku — Fast, cost-effective ($0.8 • $4)",
		"anthropic.claude-3-haiku": "Claude 3 Haiku — Lightweight ($0.25 • $1.25)",
		"amazon.nova-micro-v1:0": "Nova Micro — Ultra-fast ($0.035 • $0.14)",
		"amazon.nova-lite-v1:0": "Nova Lite — Multimodal ($0.06 • $0.24)",
		"amazon.nova-pro-v1:0": "Nova Pro — High-performance ($0.45 • $1.8)",
		"deepseek.r1-v1:0": "DeepSeek R1 — Cost-efficient ($0.14 • $0.7)",
		"mistral.pixtral-large-2502-v1:0": "Pixtral Large — Multimodal ($1 • $3)",
		"meta.llama3-1-8b-instruct-v1:0": "Llama 3.1 8B — Lightweight ($0.15 • $0.6)",
		"meta.llama3-1-70b-instruct-v1:0": "Llama 3.1 70B — Balanced ($0.75 • $3)",
		"meta.llama3-2-11b-instruct-v1:0": "Llama 3.2 11B — Multilingual ($0.2 • $0.8)",
		"meta.llama3-3-70b-instruct-v1:0": "Llama 3.3 70B — Complex tasks ($0.75 • $3)",
	}
	EMBEDDING_MODELS["AWS"] = {
		"amazon.titan-embed-text-v2:0": "Titan Embed Text 2 ($0.12)",
	}

	# ===== Ollama (Local) =====
	MODELS["Ollama"] = {
		"llama3.1:8b": "Llama 3.1 8B — Balanced (Free)",
		"llama3.1:70b": "Llama 3.1 70B — High-performance (Free)",
		"llama3:8b": "Llama 3 8B — General purpose (Free)",
		"mistral:7b": "Mistral 7B — Good reasoning (Free)",
		"mixtral:8x7b": "Mixtral 8x7B — MoE (Free)",
		"qwen2.5:7b": "Qwen2.5 7B — Chinese-optimized (Free)",
		"qwen2.5:14b": "Qwen2.5 14B — Larger Chinese (Free)",
		"phi3:14b": "Phi-3 14B — Microsoft mid-size (Free)",
		"gemma2:9b": "Gemma 2 9B — Google open (Free)",
		"gemma2:27b": "Gemma 2 27B — Google larger (Free)",
	}
	EMBEDDING_MODELS["Ollama"] = {
		"nomic-embed-text": "Nomic Embed Text (Free)",
		"mxbai-embed-large": "MixedBread AI Large (Free)",
		"all-minilm": "All-MiniLM-L6-v2 (Free)",
		"snowflake-arctic-embed": "Snowflake Arctic Embed (Free)",
	}

	# ===== Custom (OpenAI-compatible endpoint) =====
	MODELS["Custom"] = {}
	EMBEDDING_MODELS["Custom"] = {}

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

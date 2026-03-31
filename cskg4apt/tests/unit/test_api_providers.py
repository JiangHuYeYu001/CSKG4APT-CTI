import os

import pytest


class TestProviderRegistration:
	"""Test that new API providers are registered correctly."""

	def _check_provider_registered(self, monkeypatch, env_var, provider_name):
		"""Helper to check provider registration."""
		# Clear existing state
		from cskg4apt.utils.model_utils import MODELS, EMBEDDING_MODELS
		MODELS.clear()
		EMBEDDING_MODELS.clear()

		monkeypatch.setenv(env_var, "test-key-123")
		from cskg4apt.utils.model_utils import check_api_key
		check_api_key()
		assert provider_name in MODELS, f"{provider_name} not found in MODELS"

	def test_anthropic_provider(self, monkeypatch):
		self._check_provider_registered(monkeypatch, "ANTHROPIC_API_KEY", "Anthropic")

	def test_tongyi_provider(self, monkeypatch):
		self._check_provider_registered(monkeypatch, "DASHSCOPE_API_KEY", "Tongyi")

	def test_zhipuai_provider(self, monkeypatch):
		self._check_provider_registered(monkeypatch, "ZHIPUAI_API_KEY", "ZhipuAI")

	def test_deepseek_provider(self, monkeypatch):
		self._check_provider_registered(monkeypatch, "DEEPSEEK_API_KEY", "DeepSeek")

	def test_baidu_provider(self, monkeypatch):
		self._check_provider_registered(monkeypatch, "QIANFAN_API_KEY", "Baidu")

	def test_spark_provider(self, monkeypatch):
		self._check_provider_registered(monkeypatch, "SPARK_API_KEY", "Spark")

	def test_openai_still_works(self, monkeypatch):
		self._check_provider_registered(monkeypatch, "OPENAI_API_KEY", "OpenAI")

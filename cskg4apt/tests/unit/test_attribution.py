import pytest

from cskg4apt.attribution.apt_analyzer import APTAttributor
from cskg4apt.attribution.diamond_model import DiamondModelAnalyzer
from cskg4apt.schemas.cskg4apt_ontology import CSKG4APTGraph, CSKGEntity, CSKGRelation, EntityType


class TestAPTAttributor:
	def test_generate_threat_cards(self, sample_cskg4apt_graph):
		attributor = APTAttributor()
		cards = attributor.generate_threat_cards(sample_cskg4apt_graph)
		assert len(cards) == 1
		card = cards[0]
		assert card.attacker_id == "apt28"
		assert "APT28" in card.attacker_names
		assert "Zebrocy" in card.malwares
		assert "Mimikatz" in card.tools
		assert "government agencies" in card.target_sectors

	def test_empty_graph(self):
		empty_graph = CSKG4APTGraph(
			source_text="No attackers here.",
			entities=[],
			relations=[],
		)
		attributor = APTAttributor()
		cards = attributor.generate_threat_cards(empty_graph)
		assert cards == []

	def test_threat_level_assignment(self, sample_cskg4apt_graph):
		attributor = APTAttributor()
		cards = attributor.generate_threat_cards(sample_cskg4apt_graph)
		assert cards[0].threat_level in ("High", "Medium", "Low")


class TestDiamondModelAnalyzer:
	def test_analyze(self, sample_cskg4apt_graph):
		analyzer = DiamondModelAnalyzer()
		vertices = analyzer.analyze(sample_cskg4apt_graph)
		assert len(vertices) >= 1
		vertex = vertices[0]
		assert vertex.adversary == "APT28"
		assert len(vertex.capability) >= 1

	def test_empty_graph(self):
		empty_graph = CSKG4APTGraph(
			source_text="Empty.",
			entities=[],
			relations=[],
		)
		analyzer = DiamondModelAnalyzer()
		vertices = analyzer.analyze(empty_graph)
		assert vertices == []

	def test_summary_generation(self, sample_cskg4apt_graph):
		analyzer = DiamondModelAnalyzer()
		summary = analyzer.generate_summary(sample_cskg4apt_graph)
		assert "Diamond Model" in summary
		assert "APT28" in summary

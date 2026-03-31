import pytest

from cskg4apt.schemas.cskg4apt_ontology import (
	CSKG4APTGraph,
	CSKGEntity,
	CSKGRelation,
	EntityType,
	RelationType,
)
from cskg4apt.schemas.apt_attributes import (
	APTThreatCard,
	AttackChain,
	DiamondModelVertex,
)


class TestEntityType:
	def test_all_12_types_exist(self):
		expected = [
			"Attacker", "Infrastructure", "Malware", "Vulnerability",
			"Assets", "Target", "Event", "Behavior", "Time",
			"Tool", "Credential", "Indicator",
		]
		for name in expected:
			assert EntityType(name) is not None

	def test_invalid_type_raises(self):
		with pytest.raises(ValueError):
			EntityType("InvalidType")


class TestRelationType:
	def test_all_7_types_exist(self):
		expected = ["has", "uses", "exploit", "exist", "target", "medium", "behavior"]
		for name in expected:
			assert RelationType(name) is not None

	def test_invalid_type_raises(self):
		with pytest.raises(ValueError):
			RelationType("invalid_relation")


class TestCSKGEntity:
	def test_valid_entity(self):
		entity = CSKGEntity(
			id="apt28",
			type="Attacker",
			name="APT28",
			derivation_source="APT28 is a Russian threat actor.",
		)
		assert entity.type == EntityType.ATTACKER
		assert entity.confidence == 1.0

	def test_type_coercion_case_insensitive(self):
		entity = CSKGEntity(
			id="test",
			type="attacker",
			name="Test",
			derivation_source="test source",
		)
		assert entity.type == EntityType.ATTACKER

	def test_confidence_clamping(self):
		entity = CSKGEntity(
			id="test",
			type="Malware",
			name="Test",
			derivation_source="test source",
			confidence=1.5,
		)
		assert entity.confidence == 1.0

	def test_empty_id_rejected(self):
		with pytest.raises(Exception):
			CSKGEntity(
				id="",
				type="Malware",
				name="Test",
				derivation_source="test",
			)

	def test_aliases_default_empty(self):
		entity = CSKGEntity(
			id="test",
			type="Tool",
			name="Mimikatz",
			derivation_source="test source",
		)
		assert entity.aliases == []


class TestCSKGRelation:
	def test_valid_relation(self):
		relation = CSKGRelation(
			source_entity_id="apt28",
			target_entity_id="zebrocy",
			relation_type="has",
			derivation_source="APT28 has Zebrocy malware.",
		)
		assert relation.relation_type == RelationType.HAS

	def test_relation_type_coercion(self):
		relation = CSKGRelation(
			source_entity_id="a",
			target_entity_id="b",
			relation_type="HAS",
			derivation_source="test source",
		)
		assert relation.relation_type == RelationType.HAS


class TestCSKG4APTGraph:
	def test_graph_construction(self, sample_cskg4apt_graph):
		assert len(sample_cskg4apt_graph.entities) == 5
		assert len(sample_cskg4apt_graph.relations) == 4

	def test_get_entity(self, sample_cskg4apt_graph):
		entity = sample_cskg4apt_graph.get_entity("apt28")
		assert entity is not None
		assert entity.name == "APT28"

	def test_get_entity_not_found(self, sample_cskg4apt_graph):
		assert sample_cskg4apt_graph.get_entity("nonexistent") is None

	def test_get_entities_by_type(self, sample_cskg4apt_graph):
		attackers = sample_cskg4apt_graph.get_entities_by_type(EntityType.ATTACKER)
		assert len(attackers) == 1
		assert attackers[0].name == "APT28"

	def test_get_outgoing_relations(self, sample_cskg4apt_graph):
		relations = sample_cskg4apt_graph.get_outgoing_relations("apt28")
		assert len(relations) == 3  # has, target, uses

	def test_to_networkx(self, sample_cskg4apt_graph):
		G = sample_cskg4apt_graph.to_networkx()
		assert len(G.nodes()) == 5
		assert len(G.edges()) == 4

	def test_to_dict(self, sample_cskg4apt_graph):
		d = sample_cskg4apt_graph.to_dict()
		assert "entities" in d
		assert "relations" in d
		assert len(d["entities"]) == 5

	def test_summary(self, sample_cskg4apt_graph):
		summary = sample_cskg4apt_graph.summary()
		assert "CSKG4APTGraph" in summary
		assert "5 entities" in summary
		assert "4 relations" in summary


class TestAPTThreatCard:
	def test_minimal_card(self):
		card = APTThreatCard(attacker_id="apt28")
		assert card.attacker_id == "apt28"
		assert card.malwares == []
		assert card.tools == []

	def test_full_card(self):
		card = APTThreatCard(
			attacker_id="apt28",
			attacker_names=["APT28", "Fancy Bear"],
			malwares=["Zebrocy"],
			tools=["Mimikatz"],
			target_sectors=["government"],
			exploited_cves=["CVE-2017-0143"],
			threat_level="High",
		)
		assert "Fancy Bear" in card.attacker_names
		assert card.threat_level == "High"


class TestDiamondModelVertex:
	def test_minimal_vertex(self):
		vertex = DiamondModelVertex()
		assert vertex.adversary is None
		assert vertex.capability == []

	def test_full_vertex(self):
		vertex = DiamondModelVertex(
			adversary="APT28",
			capability=["Zebrocy", "Mimikatz"],
			infrastructure=["evil.com"],
			victim=["government agencies"],
		)
		assert vertex.adversary == "APT28"
		assert len(vertex.capability) == 2


class TestAttackChain:
	def test_minimal_chain(self):
		chain = AttackChain(attack_id="event-1")
		assert chain.attack_id == "event-1"
		assert chain.attacker is None

	def test_chain_with_phases(self):
		chain = AttackChain(
			attack_id="event-1",
			attacker="APT28",
			exploitation={"techniques": ["CVE-2017-0143"]},
			actions_on_objective={"techniques": ["data exfiltration"]},
		)
		assert chain.exploitation is not None
		assert chain.actions_on_objective is not None

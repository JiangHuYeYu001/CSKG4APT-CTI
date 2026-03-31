import logging
from typing import Dict, List, Optional

from omegaconf import DictConfig

from ..schemas.apt_attributes import DiamondModelVertex
from ..schemas.cskg4apt_ontology import (
	CSKG4APTGraph,
	EntityType,
	RelationType,
)

logger = logging.getLogger(__name__)


class DiamondModelAnalyzer:
	"""
	Diamond Model analysis from CSKG4APTGraph.

	The Diamond Model defines four core features:
	- Adversary: The threat actor
	- Capability: Malware and tools used
	- Infrastructure: C2 servers, domains, IPs
	- Victim: Targeted sectors/organizations/countries
	"""

	def __init__(self, config: DictConfig = None):
		self.config = config

	def analyze(self, kg: CSKG4APTGraph) -> List[DiamondModelVertex]:
		"""Build Diamond Model vertices for each identified attacker or event."""
		vertices = []

		# Build from attacker perspective
		attackers = kg.get_entities_by_type(EntityType.ATTACKER)
		for attacker in attackers:
			vertex = self._build_vertex_from_attacker(attacker, kg)
			vertices.append(vertex)

		# If no attackers but events exist, build from events
		if not attackers:
			events = kg.get_entities_by_type(EntityType.EVENT)
			for event in events:
				vertex = self._build_vertex_from_event(event, kg)
				vertices.append(vertex)

		return vertices

	def _build_vertex_from_attacker(
		self, attacker, kg: CSKG4APTGraph
	) -> DiamondModelVertex:
		"""Build Diamond Model vertex centered on an attacker entity."""
		outgoing = kg.get_outgoing_relations(attacker.id)

		# Capability: Malware + Tools
		capabilities = []
		for r in outgoing:
			if r.relation_type in (RelationType.HAS, RelationType.USES):
				entity = kg.get_entity(r.target_entity_id)
				if entity and entity.type in (EntityType.MALWARE, EntityType.TOOL):
					capabilities.append(entity.name)

		# Infrastructure
		infrastructure = []
		for r in outgoing:
			if r.relation_type == RelationType.MEDIUM:
				entity = kg.get_entity(r.target_entity_id)
				if entity and entity.type == EntityType.INFRASTRUCTURE:
					infrastructure.append(entity.name)

		# Victim
		victims = []
		for r in outgoing:
			if r.relation_type == RelationType.TARGET:
				entity = kg.get_entity(r.target_entity_id)
				if entity and entity.type == EntityType.TARGET:
					victims.append(entity.name)

		# Timestamp
		timestamp = None
		time_entities = kg.get_entities_by_type(EntityType.TIME)
		if time_entities:
			timestamp = time_entities[0].name

		return DiamondModelVertex(
			adversary=attacker.name,
			capability=capabilities,
			infrastructure=infrastructure,
			victim=victims,
			timestamp=timestamp,
		)

	def _build_vertex_from_event(
		self, event, kg: CSKG4APTGraph
	) -> DiamondModelVertex:
		"""Build Diamond Model vertex centered on an event entity."""
		all_relations = kg.get_outgoing_relations(event.id) + kg.get_incoming_relations(event.id)

		adversary = None
		capabilities = []
		infrastructure = []
		victims = []

		for r in all_relations:
			source = kg.get_entity(r.source_entity_id)
			target = kg.get_entity(r.target_entity_id)

			for entity in [source, target]:
				if entity is None:
					continue
				if entity.id == event.id:
					continue
				if entity.type == EntityType.ATTACKER and adversary is None:
					adversary = entity.name
				elif entity.type in (EntityType.MALWARE, EntityType.TOOL):
					capabilities.append(entity.name)
				elif entity.type == EntityType.INFRASTRUCTURE:
					infrastructure.append(entity.name)
				elif entity.type == EntityType.TARGET:
					victims.append(entity.name)

		return DiamondModelVertex(
			adversary=adversary,
			capability=capabilities,
			infrastructure=infrastructure,
			victim=victims,
			event_id=event.id,
		)

	def generate_summary(self, kg: CSKG4APTGraph) -> str:
		"""Generate a text summary of the Diamond Model analysis."""
		vertices = self.analyze(kg)
		if not vertices:
			return "No Diamond Model vertices could be constructed from the graph."

		lines = ["## Diamond Model Analysis\n"]
		for i, v in enumerate(vertices, 1):
			lines.append(f"### Vertex {i}")
			lines.append(f"- **Adversary**: {v.adversary or 'Unknown'}")
			lines.append(f"- **Capability**: {', '.join(v.capability) if v.capability else 'None identified'}")
			lines.append(f"- **Infrastructure**: {', '.join(v.infrastructure) if v.infrastructure else 'None identified'}")
			lines.append(f"- **Victim**: {', '.join(v.victim) if v.victim else 'None identified'}")
			if v.timestamp:
				lines.append(f"- **Timestamp**: {v.timestamp}")
			lines.append("")

		return "\n".join(lines)

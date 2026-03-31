import logging
import time
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
	"""CSKG4APT 12 entity types"""

	ATTACKER = "Attacker"
	INFRASTRUCTURE = "Infrastructure"
	MALWARE = "Malware"
	VULNERABILITY = "Vulnerability"
	ASSETS = "Assets"
	TARGET = "Target"
	EVENT = "Event"
	BEHAVIOR = "Behavior"
	TIME = "Time"
	TOOL = "Tool"
	CREDENTIAL = "Credential"
	INDICATOR = "Indicator"


class RelationType(str, Enum):
	"""CSKG4APT 7 relation types"""

	HAS = "has"
	USES = "uses"
	EXPLOIT = "exploit"
	EXIST = "exist"
	TARGET = "target"
	MEDIUM = "medium"
	BEHAVIOR = "behavior"


# Valid source->target type constraints for relations
RELATION_TYPE_CONSTRAINTS = {
	RelationType.HAS: (EntityType.ATTACKER, EntityType.MALWARE),
	RelationType.USES: (EntityType.ATTACKER, EntityType.TOOL),
	RelationType.EXPLOIT: (EntityType.MALWARE, EntityType.VULNERABILITY),
	RelationType.EXIST: (EntityType.VULNERABILITY, EntityType.ASSETS),
	RelationType.TARGET: (EntityType.ATTACKER, EntityType.TARGET),
	RelationType.MEDIUM: (EntityType.ATTACKER, EntityType.INFRASTRUCTURE),
	RelationType.BEHAVIOR: (EntityType.EVENT, EntityType.BEHAVIOR),
}


class CSKGEntity(BaseModel):
	"""CSKG4APT Entity"""

	id: str = Field(..., min_length=1, description="Unique entity identifier")
	type: EntityType = Field(..., description="Entity type from 12 CSKG4APT types")
	name: str = Field(..., min_length=1, description="Entity name")
	aliases: List[str] = Field(default_factory=list, description="Alternative names")
	derivation_source: str = Field(..., min_length=1, description="Source text evidence")
	confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence")
	attributes: Optional[Dict] = Field(default=None, description="Additional attributes")

	@field_validator("type", mode="before")
	@classmethod
	def coerce_entity_type(cls, v):
		if isinstance(v, str):
			# Try exact match first
			for member in EntityType:
				if v == member.value or v.lower() == member.value.lower():
					return member
			# Try enum name match
			try:
				return EntityType[v.upper()]
			except KeyError:
				pass
		return v

	@field_validator("confidence", mode="before")
	@classmethod
	def clamp_confidence(cls, v):
		if isinstance(v, (int, float)):
			return max(0.0, min(1.0, float(v)))
		return v


class CSKGRelation(BaseModel):
	"""CSKG4APT Relation"""

	source_entity_id: str = Field(..., min_length=1, description="Source entity ID")
	target_entity_id: str = Field(..., min_length=1, description="Target entity ID")
	relation_type: RelationType = Field(..., description="Relation type from 7 CSKG4APT types")
	derivation_source: str = Field(..., min_length=1, description="Source text evidence")
	confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence")

	@field_validator("relation_type", mode="before")
	@classmethod
	def coerce_relation_type(cls, v):
		if isinstance(v, str):
			for member in RelationType:
				if v == member.value or v.lower() == member.value.lower():
					return member
			try:
				return RelationType[v.upper()]
			except KeyError:
				pass
		return v

	@field_validator("confidence", mode="before")
	@classmethod
	def clamp_confidence(cls, v):
		if isinstance(v, (int, float)):
			return max(0.0, min(1.0, float(v)))
		return v


class CSKG4APTGraph(BaseModel):
	"""CSKG4APT Knowledge Graph container"""

	name: str = Field(default_factory=lambda: f"CSKG4APT-{int(time.time())}")
	source_url: Optional[str] = None
	source_text: str = Field(..., description="Original CTI text")
	extraction_timestamp: str = Field(
		default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S")
	)
	entities: List[CSKGEntity] = Field(default_factory=list)
	relations: List[CSKGRelation] = Field(default_factory=list)
	metadata: Dict = Field(default_factory=dict)

	def get_entity(self, entity_id: str) -> Optional[CSKGEntity]:
		"""Get entity by ID"""
		for entity in self.entities:
			if entity.id == entity_id:
				return entity
		return None

	def get_entities_by_type(self, entity_type: EntityType) -> List[CSKGEntity]:
		"""Get all entities of a given type"""
		return [e for e in self.entities if e.type == entity_type]

	def get_outgoing_relations(self, entity_id: str) -> List[CSKGRelation]:
		"""Get all relations where entity_id is the source"""
		return [r for r in self.relations if r.source_entity_id == entity_id]

	def get_incoming_relations(self, entity_id: str) -> List[CSKGRelation]:
		"""Get all relations where entity_id is the target"""
		return [r for r in self.relations if r.target_entity_id == entity_id]

	def to_networkx(self):
		"""Convert to NetworkX directed graph"""
		import networkx as nx

		G = nx.DiGraph()
		for entity in self.entities:
			G.add_node(
				entity.id,
				type=entity.type.value,
				name=entity.name,
				confidence=entity.confidence,
			)
		for relation in self.relations:
			G.add_edge(
				relation.source_entity_id,
				relation.target_entity_id,
				relation=relation.relation_type.value,
				confidence=relation.confidence,
			)
		return G

	def to_dict(self) -> dict:
		"""Serialize to dictionary"""
		return self.model_dump(mode="json")

	def summary(self) -> str:
		"""Generate a brief summary of the graph"""
		type_counts = {}
		for entity in self.entities:
			type_name = entity.type.value
			type_counts[type_name] = type_counts.get(type_name, 0) + 1
		rel_counts = {}
		for relation in self.relations:
			rel_name = relation.relation_type.value
			rel_counts[rel_name] = rel_counts.get(rel_name, 0) + 1
		return (
			f"CSKG4APTGraph '{self.name}': "
			f"{len(self.entities)} entities ({type_counts}), "
			f"{len(self.relations)} relations ({rel_counts})"
		)

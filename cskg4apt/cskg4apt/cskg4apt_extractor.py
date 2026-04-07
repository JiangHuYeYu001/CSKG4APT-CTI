import json
import logging
import time
from typing import Dict, List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader, meta
from omegaconf import DictConfig
from pydantic import ValidationError

from .llm_processor import LLMCaller, UsageCalculator, extract_json_from_response
from .schemas.cskg4apt_ontology import (
	CSKG4APTGraph,
	CSKGEntity,
	CSKGRelation,
	EntityType,
	RelationType,
)
from .utils.path_utils import resolve_path

logger = logging.getLogger(__name__)


class CSKG4APTExtractor:
	"""
	LLM-based CSKG4APT knowledge extraction.

	Input: CTI report text
	Output: CSKG4APTGraph conforming to CSKG4APT ontology (12 entity types, 7 relation types)

	Features:
	- Zero-shot (no training data required)
	- Strong ontology constraint (Pydantic validation)
	- White-box traceable (derivation_source for every extraction)
	"""

	def __init__(self, config: DictConfig):
		self.config = config
		self.entity_id_map = {}
		self.extracted_entities = {}

	def call(self, text: str, source_url: str = None) -> CSKG4APTGraph:
		"""
		Main extraction entry point.

		Args:
			text: CTI report text
			source_url: Optional source URL

		Returns:
			CSKG4APTGraph with entities and relations
		"""
		logger.info(f"Starting CSKG4APT extraction, text length: {len(text)}")

		# Step 1: Extract entities
		entities, entity_usage, entity_time = self._extract_entities(text)
		logger.info(f"Extracted {len(entities)} entities")

		# Step 2: Extract relations (based on extracted entities)
		relations, relation_usage, relation_time = self._extract_relations(text, entities)
		logger.info(f"Extracted {len(relations)} relations")

		# Step 3: Build knowledge graph
		kg = CSKG4APTGraph(
			name=f"CSKG4APT-{int(time.time())}",
			source_url=source_url,
			source_text=text,
			extraction_timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
			entities=entities,
			relations=relations,
			metadata={
				"entity_extraction": {
					"model_usage": entity_usage,
					"response_time": entity_time,
				},
				"relation_extraction": {
					"model_usage": relation_usage,
					"response_time": relation_time,
				},
			},
		)

		logger.info(kg.summary())
		return kg

	def _extract_entities(self, text: str) -> Tuple[List[CSKGEntity], dict, float]:
		"""Extract entities using LLM with CSKG4APT ontology constraint."""
		prompt = self._generate_entity_prompt(text)
		response, response_time = LLMCaller(self.config, prompt).call()
		usage = UsageCalculator(self.config, response).calculate()

		response_content = extract_json_from_response(
			response.choices[0].message.content
		)

		entities = []
		for entity_data in response_content.get("entities", []):
			try:
				entity = CSKGEntity(
					id=entity_data.get("id", ""),
					type=entity_data.get("type", ""),
					name=entity_data.get("name", ""),
					aliases=entity_data.get("aliases", []),
					derivation_source=entity_data.get("derivation_source", "N/A"),
					confidence=entity_data.get("confidence", 1.0),
					attributes=entity_data.get("attributes"),
				)
				# Dedup by (type, id)
				entity_key = (entity.type, entity.id)
				if entity_key not in self.entity_id_map:
					entities.append(entity)
					self.entity_id_map[entity_key] = entity.id
					self.extracted_entities[entity.id] = entity
			except (ValidationError, Exception) as e:
				logger.warning(f"Entity validation failed: {e}")

		return entities, usage, response_time

	def _extract_relations(
		self, text: str, entities: List[CSKGEntity]
	) -> Tuple[List[CSKGRelation], dict, float]:
		"""Extract relations using LLM with 7-type constraint."""
		if not entities:
			return [], {}, 0.0

		prompt = self._generate_relation_prompt(text, entities)
		response, response_time = LLMCaller(self.config, prompt).call()
		usage = UsageCalculator(self.config, response).calculate()

		response_content = extract_json_from_response(
			response.choices[0].message.content
		)

		entity_ids = {e.id for e in entities}
		relations = []
		for relation_data in response_content.get("relations", []):
			try:
				source_id = relation_data.get("source_entity_id", "")
				target_id = relation_data.get("target_entity_id", "")

				if source_id not in entity_ids or target_id not in entity_ids:
					logger.warning(
						f"Relation references unknown entity: {source_id} -> {target_id}"
					)
					continue

				relation = CSKGRelation(
					source_entity_id=source_id,
					target_entity_id=target_id,
					relation_type=relation_data.get("relation_type", ""),
					derivation_source=relation_data.get("derivation_source", "N/A"),
					confidence=relation_data.get("confidence", 1.0),
				)
				relations.append(relation)
			except (ValidationError, Exception) as e:
				logger.warning(f"Relation validation failed: {e}")

		return relations, usage, response_time

	def _generate_entity_prompt(self, text: str) -> list:
		"""Generate entity extraction prompt using Jinja2 template."""
		try:
			env = Environment(loader=FileSystemLoader(resolve_path("prompts")))
			template = env.get_template("cskg4apt_entity.jinja")
			user_prompt = template.render(text=text)
		except Exception as e:
			logger.warning(f"Failed to load entity template, using inline prompt: {e}")
			user_prompt = self._inline_entity_prompt(text)

		return [{"role": "user", "content": user_prompt}]

	def _generate_relation_prompt(
		self, text: str, entities: List[CSKGEntity]
	) -> list:
		"""Generate relation extraction prompt using Jinja2 template."""
		entity_list = [
			{"id": e.id, "type": e.type.value, "name": e.name} for e in entities
		]
		try:
			env = Environment(loader=FileSystemLoader(resolve_path("prompts")))
			template = env.get_template("cskg4apt_relation.jinja")
			user_prompt = template.render(text=text, entities=entity_list)
		except Exception as e:
			logger.warning(f"Failed to load relation template, using inline prompt: {e}")
			user_prompt = self._inline_relation_prompt(text, entity_list)

		return [{"role": "user", "content": user_prompt}]

	def _inline_entity_prompt(self, text: str) -> str:
		"""Fallback inline entity extraction prompt."""
		return f"""You are a cybersecurity threat intelligence analyst. Extract all entities from the following CTI text according to the CSKG4APT ontology.

12 Entity Types:
1. Attacker: APT groups, threat actors (e.g., APT28, Lazarus, Wizard Spider)
2. Infrastructure: C2 servers, malicious domains, IP addresses, botnets
3. Malware: Malicious software, backdoors, trojans, worms (e.g., Zebrocy, SUNBURST)
4. Vulnerability: CVE identifiers (e.g., CVE-2017-0143)
5. Assets: Attacked systems/applications (e.g., Windows SMB, Exchange Server)
6. Target: Attack targets - sectors, regions (e.g., "government", "financial sector")
7. Event: Specific attack campaigns or incidents
8. Behavior: Tactics, techniques, procedures / TTPs (e.g., "initial access", "privilege escalation")
9. Time: Temporal information (e.g., "May 2023", "since 2015")
10. Tool: Legitimate tools abused (e.g., Mimikatz, PsExec, PowerShell)
11. Credential: Credentials (usernames, passwords, tokens)
12. Indicator: IOCs - URL hashes, emails, Yara rules

Rules:
- Only extract entities of the 12 types above
- Each entity must include derivation_source (the original sentence where it appears)
- Do not fabricate information not present in the text
- Deduplicate entities that appear multiple times
- Limit extraction to at most 64 key entities. Prioritize unique, high-value entities over generic mentions

CTI Text:
{text}

Return JSON format:
{{"entities": [{{"id": "unique_id", "type": "EntityType", "name": "entity name", "derivation_source": "original sentence...", "confidence": 1.0}}]}}"""

	def _inline_relation_prompt(self, text: str, entity_list: list) -> str:
		"""Fallback inline relation extraction prompt."""
		entities_str = "\n".join(
			[f"- {e['id']} ({e['type']}): {e['name']}" for e in entity_list]
		)
		return f"""You are a cybersecurity threat intelligence analyst. Extract relations between the given entities from the CTI text.

7 Relation Types and Constraints:
1. has: Attacker -[has]-> Malware (attacker possesses/developed malware)
2. uses: Attacker -[uses]-> Tool (attacker uses a tool)
3. exploit: Malware -[exploit]-> Vulnerability (malware exploits vulnerability)
4. exist: Vulnerability -[exist]-> Assets (vulnerability exists in asset)
5. target: Attacker -[target]-> Target (attacker targets sector/region)
6. medium: Attacker -[medium]-> Infrastructure (attacker uses infrastructure)
7. behavior: Event -[behavior]-> Behavior (event involves tactic/technique)

Extracted Entities:
{entities_str}

Rules:
- Only create relations between entities from the list above
- Only use the 7 defined relation types
- Follow source->target type constraints
- derivation_source must contain context for both source and target entities
- Do not fabricate relations

CTI Text:
{text}

Return JSON format:
{{"relations": [{{"source_entity_id": "id1", "target_entity_id": "id2", "relation_type": "has", "derivation_source": "original sentence...", "confidence": 1.0}}]}}"""

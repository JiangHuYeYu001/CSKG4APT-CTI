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
	validate_entity_name,
	validate_relation_types,
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
				# Skip entities rejected by subtype validation (confidence set to 0)
				if entity.confidence <= 0.0:
					logger.info(
						"Filtered abstract entity: '%s' (type=%s)",
						entity.name,
						entity.type.value,
					)
					continue
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

				# Validate relation type constraints
				source_entity = self.extracted_entities.get(source_id)
				target_entity = self.extracted_entities.get(target_id)
				if source_entity and target_entity:
					if not validate_relation_types(
						relation.relation_type,
						source_entity.type,
						target_entity.type,
					):
						logger.warning(
							"Relation '%s' (%s -> %s) violates type constraints: "
							"%s -[%s]-> %s not allowed",
							relation.relation_type.value,
							source_id,
							target_id,
							source_entity.type.value,
							relation.relation_type.value,
							target_entity.type.value,
						)
						continue

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
		return f"""You are a cybersecurity threat intelligence analyst. Extract all CONCRETE, NAMED entities from the following CTI text according to the CSKG4APT ontology.

12 Entity Types (only extract specific, named instances — NEVER extract abstract descriptions):

1. Attacker: Named APT groups, cybercrime gangs, hacktivists (e.g., APT28, Lazarus, FIN7). NOT "the attacker" or "threat actors".
2. Infrastructure: Attacker-controlled C2 servers, malicious domains, IPs, botnets (e.g., evil-domain.com, 45.33.32.156). NOT "the infrastructure".
3. Malware: Purpose-built malicious software (e.g., Zebrocy, SUNBURST, Emotet, WannaCry). NOT "the malware" or "malicious activity".
4. Vulnerability: Named vulnerabilities with CVE IDs or well-known names (e.g., CVE-2017-0143, Log4Shell). NOT "the vulnerability" or "a vulnerability".
5. Assets: Specific victim-side systems/applications/platforms (e.g., Windows SMB, Exchange Server, Apache Struts, VMware ESXi). NOT "the system" or "the server".
6. Target: Named sectors, regions, organizations being attacked (e.g., "government", "financial sector", "United States"). NOT "the target" or "the victim".
7. Event: Named attack campaigns or incidents (e.g., Operation ShadowHammer, SolarWinds attack). NOT "the event" or "the incident".
8. Behavior: Specific TTPs mapped to MITRE ATT&CK (e.g., "spear phishing", "credential dumping", "lateral movement", T1059). NOT "the behavior" or "attack behavior".
9. Time: Specific temporal information (e.g., "May 2023", "since 2015", "Q1 2024"). Must contain actual date/year.
10. Tool: Named legitimate tools abused by attackers (e.g., Mimikatz, PsExec, PowerShell, Cobalt Strike framework). NOT "the tool" or "various tools".
11. Credential: Specific credential types involved (e.g., stolen SSH keys, NTLM hashes, admin passwords). NOT "the credential" or "credential access" (that's a Behavior).
12. Indicator: Specific IOCs (e.g., MD5/SHA hashes, malicious URLs, YARA rules, file paths). NOT "the indicator" or "indicators of compromise".

Key distinctions:
- Malware vs Tool: Purpose-built for attacks → Malware. Legitimate software abused → Tool.
- Infrastructure vs Assets: Attacker-controlled → Infrastructure. Victim-side → Assets.

Rules:
- Only extract entities of the 12 types above
- Each entity must include derivation_source (the original sentence where it appears)
- Do not fabricate information not present in the text
- Deduplicate entities that appear multiple times

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

7 Relation Types and ALL Valid Constraints (STRICTLY follow these source→target type pairs):

1. has:
   - Attacker → Malware (attacker possesses/developed malware)
   - Attacker → Credential (attacker holds stolen credentials)
   - Attacker → Indicator (attacker associated with IOCs)
   - Malware → Indicator (malware has IOC signatures)
   - Malware → Behavior (malware exhibits TTP characteristics)
   - Infrastructure → Indicator (infrastructure associated with IOCs)
   - Event → Time (event has timestamp)
   - Event → Indicator (event associated with IOCs)

2. uses:
   - Attacker → Tool (attacker uses a legitimate tool)
   - Attacker → Credential (attacker uses stolen credentials)
   - Malware → Tool (malware invokes legitimate tools)
   - Malware → Infrastructure (malware connects to C2)
   - Event → Tool (event involves tools)

3. exploit:
   - Malware → Vulnerability (malware exploits vulnerability)
   - Attacker → Vulnerability (attacker exploits vulnerability)
   - Tool → Vulnerability (tool exploits vulnerability)

4. exist:
   - Vulnerability → Assets (vulnerability exists in system)
   - Malware → Assets (malware present in asset)
   - Indicator → Assets (IOC found in asset)

5. target:
   - Attacker → Target (attacker targets sector/region)
   - Malware → Target (malware targets specific victims)
   - Event → Target (event targets victims)
   - Attacker → Assets (attacker targets specific systems)
   - Malware → Assets (malware targets specific platforms)

6. medium:
   - Attacker → Infrastructure (attacker uses infrastructure)
   - Malware → Infrastructure (malware communicates via infrastructure)
   - Event → Infrastructure (event involves infrastructure)

7. behavior:
   - Event → Behavior (event involves TTPs)
   - Attacker → Behavior (attacker employs TTPs)
   - Malware → Behavior (malware exhibits behaviors)
   - Tool → Behavior (tool associated with behaviors)

Extracted Entities:
{entities_str}

Rules:
- Only create relations between entities from the list above
- Only use the 7 defined relation types
- STRICTLY follow source→target type constraints — if a pair is not listed, DO NOT create it
- derivation_source must contain context for both source and target entities
- Do not fabricate relations

CTI Text:
{text}

Return JSON format:
{{"relations": [{{"source_entity_id": "id1", "target_entity_id": "id2", "relation_type": "has", "derivation_source": "original sentence...", "confidence": 1.0}}]}}"""

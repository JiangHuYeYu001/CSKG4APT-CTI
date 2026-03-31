import logging
import re
from typing import Dict, List, Optional

from omegaconf import DictConfig

from ..schemas.apt_attributes import APTThreatCard, AttackChain
from ..schemas.cskg4apt_ontology import (
	CSKG4APTGraph,
	CSKGEntity,
	EntityType,
	RelationType,
)

logger = logging.getLogger(__name__)


class APTAttributor:
	"""
	APT organization attribution and threat card generation.

	Generates structured threat intelligence cards from CSKG4APTGraph
	by traversing entity-relation paths.
	"""

	def __init__(self, config: DictConfig = None):
		self.config = config

	def generate_threat_cards(self, kg: CSKG4APTGraph) -> List[APTThreatCard]:
		"""Generate APT Threat Cards for all Attacker entities in the graph."""
		attackers = kg.get_entities_by_type(EntityType.ATTACKER)
		cards = []
		for attacker in attackers:
			card = self._build_card(attacker, kg)
			cards.append(card)
		return cards

	def _build_card(self, attacker: CSKGEntity, kg: CSKG4APTGraph) -> APTThreatCard:
		"""Build a threat card for a single APT organization."""
		outgoing = kg.get_outgoing_relations(attacker.id)

		# Collect malware via 'has' relations
		malwares = []
		for r in outgoing:
			if r.relation_type == RelationType.HAS:
				entity = kg.get_entity(r.target_entity_id)
				if entity and entity.type == EntityType.MALWARE:
					malwares.append(entity.name)

		# Collect tools via 'uses' relations
		tools = []
		for r in outgoing:
			if r.relation_type == RelationType.USES:
				entity = kg.get_entity(r.target_entity_id)
				if entity and entity.type == EntityType.TOOL:
					tools.append(entity.name)

		# Collect infrastructure via 'medium' relations
		infra_entities = []
		for r in outgoing:
			if r.relation_type == RelationType.MEDIUM:
				entity = kg.get_entity(r.target_entity_id)
				if entity and entity.type == EntityType.INFRASTRUCTURE:
					infra_entities.append(entity.name)

		# Classify infrastructure
		c2_servers = []
		domains = []
		ips = []
		for name in infra_entities:
			if self._is_ip(name):
				ips.append(name)
			elif self._is_domain(name):
				domains.append(name)
			else:
				c2_servers.append(name)

		# Collect targets via 'target' relations
		target_sectors = []
		target_countries = []
		for r in outgoing:
			if r.relation_type == RelationType.TARGET:
				entity = kg.get_entity(r.target_entity_id)
				if entity and entity.type == EntityType.TARGET:
					if self._is_country(entity.name):
						target_countries.append(entity.name)
					else:
						target_sectors.append(entity.name)

		# Collect CVEs via malware -> exploit -> vulnerability chain
		exploited_cves = []
		for r in outgoing:
			if r.relation_type == RelationType.HAS:
				malware_entity = kg.get_entity(r.target_entity_id)
				if malware_entity:
					for r2 in kg.get_outgoing_relations(malware_entity.id):
						if r2.relation_type == RelationType.EXPLOIT:
							vuln = kg.get_entity(r2.target_entity_id)
							if vuln and vuln.type == EntityType.VULNERABILITY:
								exploited_cves.append(vuln.name)

		# Also check direct relations to vulnerabilities from tools
		for r in outgoing:
			if r.relation_type == RelationType.USES:
				tool_entity = kg.get_entity(r.target_entity_id)
				if tool_entity:
					for r2 in kg.get_outgoing_relations(tool_entity.id):
						if r2.relation_type == RelationType.EXPLOIT:
							vuln = kg.get_entity(r2.target_entity_id)
							if vuln and vuln.type == EntityType.VULNERABILITY:
								if vuln.name not in exploited_cves:
									exploited_cves.append(vuln.name)

		# Collect behaviors
		tactics = []
		behaviors = kg.get_entities_by_type(EntityType.BEHAVIOR)
		for b in behaviors:
			tactics.append(b.name)

		# Determine threat level based on indicators count
		total_indicators = len(malwares) + len(tools) + len(exploited_cves)
		if total_indicators >= 5:
			threat_level = "High"
		elif total_indicators >= 2:
			threat_level = "Medium"
		else:
			threat_level = "Low"

		return APTThreatCard(
			attacker_id=attacker.id,
			attacker_names=[attacker.name] + attacker.aliases,
			tactics=tactics,
			malwares=malwares,
			tools=tools,
			c2_servers=c2_servers,
			domains=domains,
			ips=ips,
			target_sectors=target_sectors,
			target_countries=target_countries,
			exploited_cves=exploited_cves,
			evidence_urls=[kg.source_url] if kg.source_url else [],
			threat_level=threat_level,
		)

	def generate_attack_chains(self, kg: CSKG4APTGraph) -> List[AttackChain]:
		"""Extract attack chains from Event entities and their behavior relations."""
		events = kg.get_entities_by_type(EntityType.EVENT)
		chains = []
		for event in events:
			chain = self._build_chain(event, kg)
			chains.append(chain)
		return chains

	def _build_chain(self, event: CSKGEntity, kg: CSKG4APTGraph) -> AttackChain:
		"""Build an attack chain for a single event."""
		outgoing = kg.get_outgoing_relations(event.id)
		incoming = kg.get_incoming_relations(event.id)

		# Find attacker
		attacker_name = None
		for r in incoming:
			src = kg.get_entity(r.source_entity_id)
			if src and src.type == EntityType.ATTACKER:
				attacker_name = src.name
				break

		# Find target
		target_name = None
		for r in outgoing:
			tgt = kg.get_entity(r.target_entity_id)
			if tgt and tgt.type == EntityType.TARGET:
				target_name = tgt.name
				break

		# Collect behaviors
		behaviors = []
		for r in outgoing:
			if r.relation_type == RelationType.BEHAVIOR:
				entity = kg.get_entity(r.target_entity_id)
				if entity:
					behaviors.append(entity.name)

		# Map behaviors to kill chain phases
		phase_mapping = {
			"reconnaissance": ["reconnaissance", "recon", "scanning", "probing"],
			"weaponization": ["weaponization", "payload creation", "exploit development"],
			"delivery": ["delivery", "spear phishing", "phishing", "watering hole", "drive-by"],
			"exploitation": ["exploitation", "exploit", "initial access", "remote code execution"],
			"installation": ["installation", "persistence", "implant", "backdoor installation"],
			"command_control": ["command and control", "c2", "c&c", "beaconing", "command control"],
			"actions_on_objective": [
				"data exfiltration", "exfiltration", "impact", "encryption",
				"lateral movement", "privilege escalation", "credential access",
				"defense evasion", "collection", "data theft",
			],
		}

		chain_data = {}
		for phase, keywords in phase_mapping.items():
			matched = [b for b in behaviors if any(kw in b.lower() for kw in keywords)]
			if matched:
				chain_data[phase] = {"techniques": matched}

		# Find timestamp
		timestamp = None
		time_entities = kg.get_entities_by_type(EntityType.TIME)
		if time_entities:
			timestamp = time_entities[0].name

		return AttackChain(
			attack_id=event.id,
			attacker=attacker_name,
			target=target_name,
			timestamp=timestamp,
			reconnaissance=chain_data.get("reconnaissance"),
			weaponization=chain_data.get("weaponization"),
			delivery=chain_data.get("delivery"),
			exploitation=chain_data.get("exploitation"),
			installation=chain_data.get("installation"),
			command_control=chain_data.get("command_control"),
			actions_on_objective=chain_data.get("actions_on_objective"),
			evidence_source=event.derivation_source,
			behaviors=behaviors,
		)

	@staticmethod
	def _is_ip(text: str) -> bool:
		return bool(re.match(r"^(\d{1,3}\.){3}\d{1,3}$", text))

	@staticmethod
	def _is_domain(text: str) -> bool:
		return bool(re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$", text))

	@staticmethod
	def _is_country(text: str) -> bool:
		countries_keywords = [
			"united states", "china", "russia", "iran", "north korea", "south korea",
			"japan", "germany", "france", "uk", "united kingdom", "israel", "india",
			"brazil", "canada", "australia", "ukraine", "taiwan", "singapore",
		]
		return text.lower().strip() in countries_keywords

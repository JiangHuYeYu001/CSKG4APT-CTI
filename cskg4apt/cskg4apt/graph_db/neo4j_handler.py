import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Neo4jHandler:
	"""
	Neo4j graph database handler for CSKG4APT knowledge graphs.

	Supports:
	- Upsert CSKG4APT entities and relations (MERGE for auto-dedup)
	- Query APT profiles
	- Find attribution paths
	- Graceful fallback when neo4j is not installed or unavailable
	"""

	def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
		self.uri = uri
		self.username = username
		self.password = password
		self.database = database
		self.driver = None
		self._available = False

		try:
			from neo4j import GraphDatabase

			self.driver = GraphDatabase.driver(uri, auth=(username, password))
			# Verify connectivity
			self.driver.verify_connectivity()
			self._available = True
			logger.info(f"Connected to Neo4j at {uri}")
		except ImportError:
			logger.warning(
				"neo4j Python driver not installed. "
				"Install with: pip install neo4j  or  pip install cskg4apt[neo4j]"
			)
		except Exception as e:
			logger.warning(f"Cannot connect to Neo4j at {uri}: {e}")

	@property
	def is_available(self) -> bool:
		"""Check if Neo4j is available and connected."""
		return self._available

	def close(self):
		"""Close the Neo4j driver connection."""
		if self.driver:
			try:
				self.driver.close()
			except Exception as e:
				logger.debug(f"Error closing Neo4j driver: {e}")
			self.driver = None
			self._available = False

	def upsert_graph(self, kg) -> Dict:
		"""
		Upsert a CSKG4APTGraph into Neo4j.

		Uses MERGE to auto-deduplicate entities and relations.
		Returns statistics about the operation.
		"""
		if not self._available:
			logger.warning("Neo4j not available, skipping graph persistence")
			return {"status": "skipped", "reason": "neo4j_unavailable"}

		stats = {"entities_upserted": 0, "relations_upserted": 0, "errors": 0}

		try:
			with self.driver.session(database=self.database) as session:
				# Upsert entities
				for entity in kg.entities:
					try:
						self._upsert_entity(session, entity, kg.name)
						stats["entities_upserted"] += 1
					except Exception as e:
						logger.warning(f"Failed to upsert entity {entity.id}: {e}")
						stats["errors"] += 1

				# Upsert relations
				for relation in kg.relations:
					try:
						self._upsert_relation(session, relation, kg.name)
						stats["relations_upserted"] += 1
					except Exception as e:
						logger.warning(f"Failed to upsert relation: {e}")
						stats["errors"] += 1

			stats["status"] = "success"
			logger.info(
				f"Neo4j upsert complete: {stats['entities_upserted']} entities, "
				f"{stats['relations_upserted']} relations, {stats['errors']} errors"
			)
		except Exception as e:
			logger.error(f"Neo4j upsert failed: {e}")
			stats["status"] = "error"
			stats["error_message"] = str(e)

		return stats

	def _upsert_entity(self, session, entity, graph_name: str):
		"""MERGE a single entity node into Neo4j."""
		entity_type = entity.type.value if hasattr(entity.type, "value") else str(entity.type)

		cypher = f"""
		MERGE (e:{entity_type} {{id: $id}})
		ON CREATE SET
			e.name = $name,
			e.confidence = $confidence,
			e.first_seen = datetime(),
			e.derivation_sources = [$derivation_source],
			e.source_graphs = [$graph_name]
		ON MATCH SET
			e.name = $name,
			e.confidence = CASE WHEN $confidence > e.confidence THEN $confidence ELSE e.confidence END,
			e.last_updated = datetime(),
			e.derivation_sources = CASE
				WHEN NOT $derivation_source IN e.derivation_sources
				THEN e.derivation_sources + $derivation_source
				ELSE e.derivation_sources
			END,
			e.source_graphs = CASE
				WHEN NOT $graph_name IN e.source_graphs
				THEN e.source_graphs + $graph_name
				ELSE e.source_graphs
			END
		"""

		session.run(
			cypher,
			id=entity.id,
			name=entity.name,
			confidence=entity.confidence,
			derivation_source=entity.derivation_source,
			graph_name=graph_name,
		)

		# Add aliases as separate property
		if entity.aliases:
			alias_cypher = f"""
			MATCH (e:{entity_type} {{id: $id}})
			SET e.aliases = $aliases
			"""
			session.run(alias_cypher, id=entity.id, aliases=entity.aliases)

	def _upsert_relation(self, session, relation, graph_name: str):
		"""MERGE a single relation edge into Neo4j."""
		rel_type = relation.relation_type.value.upper() if hasattr(relation.relation_type, "value") else str(relation.relation_type).upper()

		cypher = f"""
		MATCH (s {{id: $source_id}})
		MATCH (t {{id: $target_id}})
		MERGE (s)-[r:{rel_type}]->(t)
		ON CREATE SET
			r.confidence = $confidence,
			r.first_seen = datetime(),
			r.evidence = [$derivation_source],
			r.source_graphs = [$graph_name]
		ON MATCH SET
			r.confidence = CASE WHEN $confidence > r.confidence THEN $confidence ELSE r.confidence END,
			r.last_updated = datetime(),
			r.evidence = CASE
				WHEN NOT $derivation_source IN r.evidence
				THEN r.evidence + $derivation_source
				ELSE r.evidence
			END,
			r.source_graphs = CASE
				WHEN NOT $graph_name IN r.source_graphs
				THEN r.source_graphs + $graph_name
				ELSE r.source_graphs
			END
		"""

		session.run(
			cypher,
			source_id=relation.source_entity_id,
			target_id=relation.target_entity_id,
			confidence=relation.confidence,
			derivation_source=relation.derivation_source,
			graph_name=graph_name,
		)

	def query_apt_profile(self, apt_name: str) -> Optional[Dict]:
		"""Query the full profile of an APT organization."""
		if not self._available:
			return None

		cypher = """
		MATCH (attacker:Attacker)
		WHERE attacker.name = $apt_name OR $apt_name IN attacker.aliases
		OPTIONAL MATCH (attacker)-[:HAS]->(malware:Malware)
		OPTIONAL MATCH (attacker)-[:USES]->(tool:Tool)
		OPTIONAL MATCH (attacker)-[:MEDIUM]->(infra:Infrastructure)
		OPTIONAL MATCH (attacker)-[:TARGET]->(target:Target)
		RETURN attacker,
			COLLECT(DISTINCT malware.name) AS malwares,
			COLLECT(DISTINCT tool.name) AS tools,
			COLLECT(DISTINCT infra.name) AS infrastructure,
			COLLECT(DISTINCT target.name) AS targets
		"""

		with self.driver.session(database=self.database) as session:
			result = session.run(cypher, apt_name=apt_name)
			record = result.single()
			if record:
				attacker_node = record["attacker"]
				return {
					"id": attacker_node["id"],
					"name": attacker_node["name"],
					"confidence": attacker_node.get("confidence", 1.0),
					"aliases": attacker_node.get("aliases", []),
					"malwares": record["malwares"],
					"tools": record["tools"],
					"infrastructure": record["infrastructure"],
					"targets": record["targets"],
				}
		return None

	def find_attribution_path(self, indicator: str) -> Optional[Dict]:
		"""
		Multi-hop path query for threat attribution.
		Given an IOC/indicator, trace back to the attacker.
		"""
		if not self._available:
			return None

		cypher = """
		MATCH (start {id: $indicator})
		MATCH path = (start)-[*1..4]-(attacker:Attacker)
		RETURN path, attacker, length(path) AS path_length
		ORDER BY path_length ASC
		LIMIT 5
		"""

		with self.driver.session(database=self.database) as session:
			result = session.run(cypher, indicator=indicator)
			paths = []
			for record in result:
				attacker_node = record["attacker"]
				paths.append({
					"attacker": attacker_node["name"],
					"attacker_id": attacker_node["id"],
					"path_length": record["path_length"],
				})
			if paths:
				return {"indicator": indicator, "attribution_paths": paths}
		return None

	def get_graph_stats(self) -> Optional[Dict]:
		"""Get statistics about the graph database."""
		if not self._available:
			return None

		cypher = """
		MATCH (n)
		WITH labels(n) AS types, count(n) AS cnt
		UNWIND types AS type
		RETURN type, sum(cnt) AS count
		ORDER BY count DESC
		"""

		with self.driver.session(database=self.database) as session:
			result = session.run(cypher)
			stats = {}
			for record in result:
				stats[record["type"]] = record["count"]
			return stats

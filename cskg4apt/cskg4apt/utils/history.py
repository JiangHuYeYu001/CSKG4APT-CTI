"""File-based result persistence for CSKG4APT extraction history."""

import json
import logging
import os
import shutil
import threading
import time

logger = logging.getLogger(__name__)

_lock = threading.Lock()


def _get_history_dir() -> str:
	"""Return the history directory path (under cskg4apt_output/history/)."""
	return os.path.join(os.getcwd(), "cskg4apt_output", "history")


def _get_index_path() -> str:
	"""Return the index file path."""
	return os.path.join(_get_history_dir(), "history_index.json")


def _ensure_history_dir():
	"""Create history directory if it doesn't exist."""
	history_dir = _get_history_dir()
	os.makedirs(history_dir, exist_ok=True)


def _load_index() -> list:
	"""Load the history index from disk. Returns empty list on error."""
	index_path = _get_index_path()
	if not os.path.exists(index_path):
		return []
	try:
		with open(index_path, "r", encoding="utf-8") as f:
			return json.load(f)
	except (json.JSONDecodeError, OSError) as e:
		logger.warning(f"Failed to load history index: {e}")
		return []


def _save_index(index: list):
	"""Atomically save the history index to disk."""
	index_path = _get_index_path()
	_ensure_history_dir()
	tmp_path = index_path + ".tmp"
	try:
		with open(tmp_path, "w", encoding="utf-8") as f:
			json.dump(index, f, ensure_ascii=False, indent=2)
		shutil.move(tmp_path, index_path)
	except OSError as e:
		logger.error(f"Failed to save history index: {e}")


class ResultHistory:
	"""Manage file-based result persistence for extraction history."""

	MAX_HISTORY = 100

	@staticmethod
	def save(
		pipeline_type: str,
		result_json: str,
		graph_file: str = None,
		input_preview: str = "",
		config_info: dict = None,
	) -> str:
		"""Save an extraction result to disk.

		Args:
			pipeline_type: "cskg4apt" or "generic"
			result_json: The full JSON result string
			graph_file: Path to the graph HTML file (will be copied to history/)
			input_preview: First ~200 chars of input text
			config_info: Dict with model/provider metadata

		Returns:
			The history entry ID
		"""
		with _lock:
			_ensure_history_dir()

			timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
			ts_compact = time.strftime("%Y%m%d_%H%M%S")
			history_id = f"{pipeline_type}_{ts_compact}"

			# Ensure unique ID (avoid collisions within same second)
			index = _load_index()
			existing_ids = {entry["id"] for entry in index}
			counter = 1
			base_id = history_id
			while history_id in existing_ids:
				history_id = f"{base_id}_{counter}"
				counter += 1

			# Save JSON result
			result_filename = f"{history_id}.json"
			result_path = os.path.join(_get_history_dir(), result_filename)
			try:
				with open(result_path, "w", encoding="utf-8") as f:
					f.write(result_json)
			except OSError as e:
				logger.error(f"Failed to save history result: {e}")
				return ""

			# Copy graph HTML file to history directory
			graph_filename = None
			if graph_file and os.path.exists(graph_file):
				graph_filename = f"{history_id}_graph.html"
				graph_dest = os.path.join(_get_history_dir(), graph_filename)
				try:
					shutil.copy2(graph_file, graph_dest)
				except OSError as e:
					logger.warning(f"Failed to copy graph file to history: {e}")
					graph_filename = None

			# Extract entity/relation counts from result
			entity_count = 0
			relation_count = 0
			try:
				result_dict = json.loads(result_json)
				if pipeline_type == "cskg4apt":
					graph = result_dict.get("graph", {})
					entity_count = graph.get("entities", result_dict.get("entity_count", 0))
					relation_count = graph.get("relations", result_dict.get("relation_count", 0))
					if isinstance(entity_count, list):
						entity_count = len(entity_count)
					if isinstance(relation_count, list):
						relation_count = len(relation_count)
				else:
					ea = result_dict.get("EA", {})
					entity_count = ea.get("entity_num", 0)
					lp = result_dict.get("LP", {})
					links = lp.get("predicted_links", [])
					relation_count = len(links)
			except (json.JSONDecodeError, Exception):
				pass

			# Build index entry
			entry = {
				"id": history_id,
				"pipeline_type": pipeline_type,
				"timestamp": timestamp,
				"model": (config_info or {}).get("model", "unknown"),
				"input_preview": (input_preview or "")[:200],
				"entity_count": entity_count,
				"relation_count": relation_count,
				"result_file": result_filename,
				"graph_file": graph_filename,
			}

			# Prepend to index (newest first)
			index.insert(0, entry)

			# Trim to max entries
			if len(index) > ResultHistory.MAX_HISTORY:
				removed = index[ResultHistory.MAX_HISTORY:]
				index = index[: ResultHistory.MAX_HISTORY]
				# Delete old files
				for old_entry in removed:
					_delete_entry_files(old_entry)

			_save_index(index)
			logger.info(f"Saved history entry: {history_id}")
			return history_id

	@staticmethod
	def load(history_id: str) -> dict | None:
		"""Load a history entry by ID.

		Returns:
			Dict with 'result_json', 'graph_url_path', and index metadata,
			or None if not found.
		"""
		index = _load_index()
		entry = next((e for e in index if e["id"] == history_id), None)
		if not entry:
			return None

		result_path = os.path.join(_get_history_dir(), entry["result_file"])
		if not os.path.exists(result_path):
			logger.warning(f"History result file not found: {result_path}")
			return None

		try:
			with open(result_path, "r", encoding="utf-8") as f:
				result_json = f.read()
		except OSError as e:
			logger.error(f"Failed to read history result: {e}")
			return None

		graph_url_path = None
		if entry.get("graph_file"):
			graph_url_path = f"history/{entry['graph_file']}"

		return {
			**entry,
			"result_json": result_json,
			"graph_url_path": graph_url_path,
		}

	@staticmethod
	def list_entries(pipeline_type: str = None, limit: int = 50) -> list[dict]:
		"""Return recent history entries, newest first.

		Args:
			pipeline_type: Filter by type ("cskg4apt" or "generic"), or None for all
			limit: Max entries to return
		"""
		index = _load_index()
		if pipeline_type:
			index = [e for e in index if e.get("pipeline_type") == pipeline_type]
		return index[:limit]

	@staticmethod
	def delete(history_id: str) -> bool:
		"""Delete a history entry by ID."""
		with _lock:
			index = _load_index()
			entry = next((e for e in index if e["id"] == history_id), None)
			if not entry:
				return False

			_delete_entry_files(entry)
			index = [e for e in index if e["id"] != history_id]
			_save_index(index)
			logger.info(f"Deleted history entry: {history_id}")
			return True

	@staticmethod
	def get_choices(pipeline_type: str = None, limit: int = 50) -> list:
		"""Return Gradio Dropdown choices: [(label, value), ...].

		Label format: "14:32:25 | model-name | 23 entities, 15 relations"
		"""
		entries = ResultHistory.list_entries(pipeline_type=pipeline_type, limit=limit)
		choices = []
		for entry in entries:
			# Extract time from timestamp "2026-04-07 14:32:25" → "14:32:25"
			ts = entry.get("timestamp", "")
			time_short = ts.split(" ")[1] if " " in ts else ts
			model = entry.get("model", "unknown")
			# Strip provider prefix for display
			if "/" in model:
				model = model.split("/", 1)[1]
			ent = entry.get("entity_count", 0)
			rel = entry.get("relation_count", 0)
			label = f"{time_short} | {model} | {ent} entities, {rel} relations"
			choices.append((label, entry["id"]))
		return choices


def _delete_entry_files(entry: dict):
	"""Delete files associated with a history entry."""
	history_dir = _get_history_dir()
	for key in ("result_file", "graph_file"):
		filename = entry.get(key)
		if filename:
			filepath = os.path.join(history_dir, filename)
			if os.path.exists(filepath):
				try:
					os.remove(filepath)
				except OSError:
					pass

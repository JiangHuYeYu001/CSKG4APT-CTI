import json
import os
import traceback
from urllib.parse import urlparse

from hydra import compose, initialize
from omegaconf import DictConfig

from ..cti_processor import PostProcessor, preprocessor
from ..graph_constructor import Linker, Merger, create_graph_visualization
from ..llm_processor import LLMExtractor, LLMTagger, UrlSourceInput
from .history import ResultHistory
from .model_utils import (
	MODELS,
	check_api_key,
	get_embedding_model_choices,
	get_model_choices,
	get_model_provider,
)
from .path_utils import resolve_path

CONFIG_PATH = "../config"


def _get_progress_callback(progress):
	if callable(progress):
		return progress
	return lambda *args, **kwargs: None


def get_metrics_box(
	ie_metrics: str = "",
	et_metrics: str = "",
	ea_metrics: str = "",
	lp_metrics: str = "",
):
	"""Generate metrics box HTML with optional metrics values"""
	return f'<div class="shadowbox"><table style="width: 100%; text-align: center; border-collapse: collapse;"><tr><th style="width: 25%; border-bottom: 1px solid var(--block-border-color);">Intelligence Extraction</th><th style="width: 25%; border-bottom: 1px solid var(--block-border-color);">Entity Tagging</th><th style="width: 25%; border-bottom: 1px solid var(--block-border-color);">Entity Alignment</th><th style="width: 25%; border-bottom: 1px solid var(--block-border-color);">Link Prediction</th></tr><tr><td>{ie_metrics or ""}</td><td>{et_metrics or ""}</td><td>{ea_metrics or ""}</td><td>{lp_metrics or ""}</td></tr></table></div>'


def run_intel_extraction(config: DictConfig, text: str = None) -> dict:
	"""Wrapper for Intelligence Extraction"""
	return LLMExtractor(config).call(text)


def run_entity_tagging(config: DictConfig, result: dict) -> dict:
	"""Wrapper for Entity Tagging"""
	return LLMTagger(config).call(result)


def run_url_source_input(config: DictConfig, source_url: str) -> dict:
	"""Wrapper for URL source ingestion and extraction."""
	return UrlSourceInput(config).call(source_url)


def run_entity_alignment(config: DictConfig, result: dict) -> dict:
	"""Wrapper for Entity Alignment"""
	preprocessed_result = preprocessor(result)
	merged_result = Merger(config).call(preprocessed_result)
	final_result = PostProcessor(config).call(merged_result)
	return final_result


def run_link_prediction(config: DictConfig, result) -> dict:
	"""Wrapper for Link Prediction"""

	if not isinstance(result, dict):
		result = {"subgraphs": result}

	return Linker(config).call(result)


def run_cskg4apt_pipeline(
	text: str = None,
	model: str = None,
	enable_diamond_model: bool = True,
	enable_threat_card: bool = True,
	enable_neo4j: bool = False,
	neo4j_uri: str = None,
	neo4j_user: str = None,
	neo4j_password: str = None,
	custom_base_url: str = None,
	custom_api_key: str = None,
	progress=None,
) -> str:
	"""Run the CSKG4APT extraction pipeline."""
	progress_callback = _get_progress_callback(progress)

	if not text or not text.strip():
		return "Error: No text content provided. Please paste CTI text or upload a PDF file."

	try:
		# CSKG4APT extraction
		config = get_config(model, None, None, custom_base_url=custom_base_url, custom_api_key=custom_api_key)
		progress_callback(0.15, desc="CSKG4APT Entity Extraction...")

		from ..cskg4apt_extractor import CSKG4APTExtractor

		extractor = CSKG4APTExtractor(config)
		kg = extractor.call(text, source_url=None)

		result = {
			"graph": kg.to_dict(),
			"entity_count": len(kg.entities),
			"relation_count": len(kg.relations),
			"summary": kg.summary(),
		}

		# Threat attribution
		if enable_threat_card or enable_diamond_model:
			progress_callback(0.6, desc="APT Threat Attribution...")
			if enable_threat_card:
				from ..attribution.apt_analyzer import APTAttributor

				threat_cards = APTAttributor(config).generate_threat_cards(kg)
				result["threat_cards"] = [tc.model_dump() for tc in threat_cards]
			if enable_diamond_model:
				from ..attribution.diamond_model import DiamondModelAnalyzer

				diamond_vertices = DiamondModelAnalyzer(config).analyze(kg)
				result["diamond_model"] = [dv.model_dump() for dv in diamond_vertices]

		# Neo4j persistence
		if enable_neo4j and neo4j_uri:
			progress_callback(0.85, desc="Saving to Neo4j...")
			from ..graph_db.neo4j_handler import Neo4jHandler

			handler = Neo4jHandler(
				neo4j_uri, neo4j_user or "neo4j", neo4j_password or ""
			)
			if handler.is_available:
				neo4j_stats = handler.upsert_graph(kg)
				result["neo4j_stats"] = neo4j_stats
				handler.close()

		progress_callback(1.0, desc="Complete!")
		return json.dumps(result, indent=4, ensure_ascii=False)

	except Exception as e:
		progress_callback(1.0, desc="Error occurred!")
		traceback.print_exc()
		return f"Error: {str(e)}"


def get_config(model: str = None, embedding_model: str = None, similarity_threshold: float = 0.6,
				custom_base_url: str = None, custom_api_key: str = None) -> DictConfig:
	provider = get_model_provider(model, embedding_model)
	model = model.split("/")[-1] if model else None
	embedding_model = embedding_model.split("/")[-1] if embedding_model else None

	with initialize(version_base="1.2", config_path=CONFIG_PATH):
		overrides = []
		if model:
			overrides.append(f"model={model}")
		if embedding_model:
			overrides.append(f"embedding_model={embedding_model}")
		if similarity_threshold:
			overrides.append(f"similarity_threshold={similarity_threshold}")
		if provider:
			overrides.append(f"provider={provider}")
		if custom_base_url:
			overrides.append(f"custom_base_url={custom_base_url}")
		if custom_api_key:
			overrides.append(f"custom_api_key={custom_api_key}")
		config = compose(config_name="config.yaml", overrides=overrides)
	return config


def run_pipeline(
	text: str = None,
	source_url: str = None,
	ie_model: str = None,
	et_model: str = None,
	ea_model: str = None,
	lp_model: str = None,
	similarity_threshold: float = 0.6,
	custom_base_url: str = None,
	custom_api_key: str = None,
	progress=None,
):
	"""Run the entire pipeline in sequence"""
	progress_callback = _get_progress_callback(progress)

	if not text and not source_url:
		return "Error: Please enter CTI text or provide a report URL."

	if source_url and not is_valid_source_url(source_url):
		return "Error: Invalid URL format. Please provide a valid http/https URL."

	# Helper to pass custom config through all stages
	cfg_kwargs = {"custom_base_url": custom_base_url, "custom_api_key": custom_api_key}

	try:
		url_source_result = None

		if source_url and source_url.strip():
			config = get_config(ie_model, None, None, **cfg_kwargs)
			progress_callback(0.05, desc="Ingesting URL source...")
			url_source_result = run_url_source_input(config, source_url)
			if url_source_result.get("status") != "success":
				error_info = url_source_result.get("error", {})
				error_code = error_info.get("code", "url_ingestion_failed")
				error_message = error_info.get("message", "URL ingestion failed.")
				return f"Error: [{error_code}] {error_message}"
			text = url_source_result.get("final_text") or url_source_result.get("normalized_text")

		if not text:
			return "Error: No usable report content was found from the URL source."

		config = get_config(ie_model, None, None, **cfg_kwargs)
		progress_callback(0.2, desc="Intelligence Extraction...")
		extraction_result = run_intel_extraction(config, text)
		if url_source_result:
			extraction_result["URL_SOURCE"] = url_source_result

		config = get_config(et_model, None, None, **cfg_kwargs)
		progress_callback(0.45, desc="Entity Tagging...")
		tagging_result = run_entity_tagging(config, extraction_result)

		progress_callback(0.7, desc="Entity Alignment...")
		config = get_config(None, ea_model, similarity_threshold, **cfg_kwargs)
		config.similarity_threshold = similarity_threshold
		alignment_result = run_entity_alignment(config, tagging_result)

		config = get_config(lp_model, None, None, **cfg_kwargs)
		progress_callback(0.9, desc="Link Prediction...")
		linking_result = run_link_prediction(config, alignment_result)

		progress_callback(1.0, desc="Processing complete!")

		return json.dumps(linking_result, indent=4)
	except Exception as e:
		progress_callback(1.0, desc="Error occurred!")
		traceback.print_exc()
		return f"Error: {str(e)}"


def process_and_visualize(
	input_source,
	text,
	source_url,
	ie_model,
	et_model,
	ea_model,
	lp_model,
	similarity_threshold,
	provider_dropdown=None,
	custom_model_input=None,
	custom_embedding_model_input=None,
	custom_base_url=None,
	custom_api_key=None,
	progress=None,
):
	if input_source == "CTI Report URL":
		text = None
	else:
		source_url = None

	# Apply custom model only to dropdowns where 'Other' is selected
	custom_model = f"{provider_dropdown}/{custom_model_input}" if provider_dropdown else custom_model_input
	custom_embedding_model = (
		f"{provider_dropdown}/{custom_embedding_model_input}" if provider_dropdown else custom_embedding_model_input
	)

	ie_model = custom_model if ie_model == "Other" else ie_model
	et_model = custom_model if et_model == "Other" else et_model
	lp_model = custom_model if lp_model == "Other" else lp_model
	ea_model = custom_embedding_model if ea_model == "Other" else ea_model

	# Run pipeline with progress tracking
	result = run_pipeline(
		text, source_url, ie_model, et_model, ea_model, lp_model, similarity_threshold,
		custom_base_url=custom_base_url, custom_api_key=custom_api_key, progress=progress
	)
	if result.startswith("Error:"):
		return (
			result,
			None,
			get_metrics_box(),
		)
	try:
		# Create visualization without progress tracking
		result_dict = json.loads(result)
		graph_url, graph_filepath = create_graph_visualization(result_dict)

		# Save to history
		input_text = text or source_url or ""
		ResultHistory.save(
			pipeline_type="generic",
			result_json=result,
			graph_file=graph_filepath,
			input_preview=input_text[:200],
			config_info={"model": ie_model},
		)
		graph_html_content = f"""
        <div style="text-align: center; padding: 10px; margin-top: -20px;">
            <h2 style="margin-bottom: 0.5em;">Entity Relationship Graph</h2>
            <em>Drag nodes • Scroll to zoom • Drag background to pan</em>
        </div>
        <div id="iframe-container"">
            <iframe src="{graph_url}"
            width="100%"
            height="700"
            frameborder="0"
            scrolling="no"
            style="display: block; clip-path: inset(13px 3px 5px 3px); overflow: hidden;">
            </iframe>
        </div>
        <div style="text-align: center; ">
            <a href="{graph_url}" target="_blank" style="color: #7c4dff; text-decoration: none;">
            🚀 Open in New Tab
            </a>
        </div>"""

		ie_metrics = f"Model: {ie_model}<br>Time: {result_dict['IE']['response_time']:.2f}s<br>Cost: ${result_dict['IE']['model_usage']['total']['cost']:.6f}"
		et_metrics = f"Model: {et_model}<br>Time: {result_dict['ET']['response_time']:.2f}s<br>Cost: ${result_dict['ET']['model_usage']['total']['cost']:.6f}"
		ea_metrics = f"Model: {ea_model}<br>Time: {result_dict['EA']['response_time']:.2f}s<br>Cost: ${result_dict['EA']['model_usage']['total']['cost']:.6f}"
		lp_metrics = f"Model: {lp_model}<br>Time: {result_dict['LP']['response_time']:.2f}s<br>Cost: ${result_dict['LP']['model_usage']['total']['cost']:.6f}"

		metrics_table = get_metrics_box(ie_metrics, et_metrics, ea_metrics, lp_metrics)

		return result, graph_html_content, metrics_table
	except Exception as e:
		import traceback

		traceback.print_exc()
		return (
			result,
			f"<div style='color: red; text-align: center; padding: 20px;'>Error creating graph: {str(e)}</div>",
			get_metrics_box(),
		)


def extract_text_from_pdf(file_path: str) -> str:
	"""Extract text content from a PDF file."""
	try:
		import fitz  # PyMuPDF
	except ImportError:
		try:
			from PyPDF2 import PdfReader

			reader = PdfReader(file_path)
			pages = []
			for page in reader.pages:
				page_text = page.extract_text()
				if page_text:
					pages.append(page_text)
			return "\n\n".join(pages)
		except ImportError:
			raise ImportError(
				"PDF extraction requires PyMuPDF or PyPDF2. "
				"Install with: pip install PyMuPDF  or  pip install PyPDF2"
			)

	doc = fitz.open(file_path)
	pages = []
	for page in doc:
		pages.append(page.get_text())
	doc.close()
	return "\n\n".join(pages)


def process_and_visualize_cskg4apt(
	input_source,
	text,
	pdf_file,
	model,
	enable_diamond_model,
	enable_threat_card,
	enable_neo4j,
	neo4j_uri,
	neo4j_user,
	neo4j_password,
	custom_base_url=None,
	custom_api_key=None,
	progress=None,
):
	"""Process CSKG4APT pipeline and create visualization."""
	# Resolve input: PDF upload or direct text
	if input_source == "Upload PDF":
		if not pdf_file:
			return "Error: Please upload a PDF file.", None, "{}", "{}"
		try:
			file_path = pdf_file.name if hasattr(pdf_file, "name") else str(pdf_file)
			text = extract_text_from_pdf(file_path)
			if not text or not text.strip():
				return "Error: Could not extract text from the PDF file.", None, "{}", "{}"
		except ImportError as e:
			return f"Error: {e}", None, "{}", "{}"
		except Exception as e:
			return f"Error: Failed to read PDF: {e}", None, "{}", "{}"

	result = run_cskg4apt_pipeline(
		text=text,
		model=model,
		enable_diamond_model=enable_diamond_model,
		enable_threat_card=enable_threat_card,
		enable_neo4j=enable_neo4j,
		neo4j_uri=neo4j_uri,
		neo4j_user=neo4j_user,
		neo4j_password=neo4j_password,
		custom_base_url=custom_base_url,
		custom_api_key=custom_api_key,
		progress=progress,
	)

	if result.startswith("Error:"):
		return result, None, "{}", "{}"

	try:
		result_dict = json.loads(result)
		graph_dict = result_dict.get("graph", {})

		# Create CSKG4APT visualization
		from ..graph_constructor import create_cskg4apt_graph_visualization

		graph_url, graph_filepath = create_cskg4apt_graph_visualization(graph_dict)

		# Save to history
		input_text = text or ""
		ResultHistory.save(
			pipeline_type="cskg4apt",
			result_json=result,
			graph_file=graph_filepath,
			input_preview=input_text[:200],
			config_info={"model": model},
		)

		graph_html = ""
		if graph_url:
			graph_html = f"""
			<div style="text-align: center; padding: 10px; margin-top: -20px;">
				<h2 style="margin-bottom: 0.5em;">CSKG4APT Knowledge Graph</h2>
				<em>Drag nodes / Scroll to zoom / Drag background to pan</em>
			</div>
			<div id="iframe-container">
				<iframe src="{graph_url}"
				width="100%" height="700" frameborder="0" scrolling="no"
				style="display: block; clip-path: inset(13px 3px 5px 3px); overflow: hidden;">
				</iframe>
			</div>
			<div style="text-align: center;">
				<a href="{graph_url}" target="_blank" style="color: #7c4dff; text-decoration: none;">
				Open in New Tab
				</a>
			</div>"""

		threat_cards_json = json.dumps(
			result_dict.get("threat_cards", []), indent=2, ensure_ascii=False
		)
		diamond_json = json.dumps(
			result_dict.get("diamond_model", []), indent=2, ensure_ascii=False
		)

		return result, graph_html, threat_cards_json, diamond_json
	except Exception as e:
		import traceback
		traceback.print_exc()
		return result, f"<div style='color: red;'>Error creating visualization: {e}</div>", "{}", "{}"


def clear_outputs():
	"""Clear all outputs when run button is clicked"""
	return "", None, get_metrics_box()


def _load_history_entry(history_id: str, pipeline_type: str):
	"""Load a history entry and return results for display."""
	from .http_server_utils import get_current_port

	if not history_id:
		if pipeline_type == "cskg4apt":
			return "", None, "{}", "{}"
		return "", None, get_metrics_box()

	entry = ResultHistory.load(history_id)
	if not entry:
		if pipeline_type == "cskg4apt":
			return "Error: History entry not found.", None, "{}", "{}"
		return "Error: History entry not found.", None, get_metrics_box()

	result_json = entry.get("result_json", "")

	if pipeline_type == "cskg4apt":
		# Build graph HTML from saved graph file
		graph_html = ""
		graph_url_path = entry.get("graph_url_path")
		if graph_url_path:
			http_port = get_current_port()
			graph_url = f"http://localhost:{http_port}/{graph_url_path}"
			graph_html = f"""
			<div style="text-align: center; padding: 10px; margin-top: -20px;">
				<h2 style="margin-bottom: 0.5em;">CSKG4APT Knowledge Graph</h2>
				<em>Drag nodes / Scroll to zoom / Drag background to pan</em>
			</div>
			<div id="iframe-container">
				<iframe src="{graph_url}"
				width="100%" height="700" frameborder="0" scrolling="no"
				style="display: block; clip-path: inset(13px 3px 5px 3px); overflow: hidden;">
				</iframe>
			</div>
			<div style="text-align: center;">
				<a href="{graph_url}" target="_blank" style="color: #7c4dff; text-decoration: none;">
				Open in New Tab
				</a>
			</div>"""

		# Extract threat cards and diamond model from result
		threat_cards_json = "{}"
		diamond_json = "{}"
		try:
			result_dict = json.loads(result_json)
			threat_cards_json = json.dumps(result_dict.get("threat_cards", []), indent=2, ensure_ascii=False)
			diamond_json = json.dumps(result_dict.get("diamond_model", []), indent=2, ensure_ascii=False)
		except (json.JSONDecodeError, Exception):
			pass

		return result_json, graph_html, threat_cards_json, diamond_json
	else:
		# Generic pipeline - build graph + metrics
		graph_html = ""
		graph_url_path = entry.get("graph_url_path")
		if graph_url_path:
			http_port = get_current_port()
			graph_url = f"http://localhost:{http_port}/{graph_url_path}"
			graph_html = f"""
			<div style="text-align: center; padding: 10px; margin-top: -20px;">
				<h2 style="margin-bottom: 0.5em;">Entity Relationship Graph</h2>
				<em>Drag nodes • Scroll to zoom • Drag background to pan</em>
			</div>
			<div id="iframe-container">
				<iframe src="{graph_url}"
				width="100%" height="700" frameborder="0" scrolling="no"
				style="display: block; clip-path: inset(13px 3px 5px 3px); overflow: hidden;">
				</iframe>
			</div>
			<div style="text-align: center;">
				<a href="{graph_url}" target="_blank" style="color: #7c4dff; text-decoration: none;">
				Open in New Tab
				</a>
			</div>"""

		metrics = get_metrics_box()
		try:
			result_dict = json.loads(result_json)
			ie_data = result_dict.get("IE", {})
			et_data = result_dict.get("ET", {})
			ea_data = result_dict.get("EA", {})
			lp_data = result_dict.get("LP", {})
			ie_metrics = f"Model: {ie_data.get('model_usage', {}).get('model', 'N/A')}<br>Time: {ie_data.get('response_time', 0):.2f}s<br>Cost: ${ie_data.get('model_usage', {}).get('total', {}).get('cost', 0):.6f}"
			et_metrics = f"Model: {et_data.get('model_usage', {}).get('model', 'N/A')}<br>Time: {et_data.get('response_time', 0):.2f}s<br>Cost: ${et_data.get('model_usage', {}).get('total', {}).get('cost', 0):.6f}"
			ea_metrics = f"Model: {ea_data.get('model_usage', {}).get('model', 'N/A')}<br>Time: {ea_data.get('response_time', 0):.2f}s<br>Cost: ${ea_data.get('model_usage', {}).get('total', {}).get('cost', 0):.6f}"
			lp_metrics = f"Model: {lp_data.get('model_usage', {}).get('model', 'N/A')}<br>Time: {lp_data.get('response_time', 0):.2f}s<br>Cost: ${lp_data.get('model_usage', {}).get('total', {}).get('cost', 0):.6f}"
			metrics = get_metrics_box(ie_metrics, et_metrics, ea_metrics, lp_metrics)
		except (json.JSONDecodeError, Exception):
			pass

		return result_json, graph_html, metrics


def _delete_history_entry(history_id: str, pipeline_type: str):
	"""Delete a history entry and return updated dropdown choices."""
	if history_id:
		ResultHistory.delete(history_id)
	choices = ResultHistory.get_choices(pipeline_type=pipeline_type)
	return gr.update(choices=choices, value=None)


def _refresh_history_choices(pipeline_type: str = None):
	"""Return updated dropdown choices for history."""
	choices = ResultHistory.get_choices(pipeline_type=pipeline_type)
	return gr.update(choices=choices, value=None)


def is_valid_source_url(source_url: str) -> bool:
	"""Basic URL validation for Gradio input."""
	if not source_url or not isinstance(source_url, str):
		return False
	candidate = source_url.strip()
	if "://" not in candidate:
		candidate = f"https://{candidate}"
	parsed = urlparse(candidate)
	return parsed.scheme in {"http", "https"} and bool(parsed.netloc and " " not in parsed.netloc)


def build_interface(warning: str = None):
	import gradio as gr

	# Ensure MODELS dict is populated before building UI
	if not MODELS:
		check_api_key()

	# ========== CSKG4APT Cyber Theme ==========
	cyber_theme = gr.themes.Base(
		primary_hue=gr.themes.colors.green,
		secondary_hue=gr.themes.colors.emerald,
		neutral_hue=gr.themes.colors.zinc,
		font=gr.themes.GoogleFont("JetBrains Mono"),
	).set(
		body_background_fill="#0a0a0a",
		body_background_fill_dark="#0a0a0a",
		body_text_color="#e0e0e0",
		body_text_color_dark="#e0e0e0",
		block_background_fill="#111111",
		block_background_fill_dark="#111111",
		block_border_color="#1a3a1a",
		block_border_color_dark="#1a3a1a",
		block_label_text_color="#00ff88",
		block_label_text_color_dark="#00ff88",
		block_title_text_color="#00ff88",
		block_title_text_color_dark="#00ff88",
		input_background_fill="#0d1a0d",
		input_background_fill_dark="#0d1a0d",
		input_border_color="#1a3a1a",
		input_border_color_dark="#1a3a1a",
		input_placeholder_color="#3a6b3a",
		input_placeholder_color_dark="#3a6b3a",
		button_primary_background_fill="#00cc66",
		button_primary_background_fill_dark="#00cc66",
		button_primary_background_fill_hover="#00ff88",
		button_primary_background_fill_hover_dark="#00ff88",
		button_primary_text_color="#000000",
		button_primary_text_color_dark="#000000",
		button_secondary_background_fill="#1a2e1a",
		button_secondary_background_fill_dark="#1a2e1a",
		button_secondary_text_color="#00ff88",
		button_secondary_text_color_dark="#00ff88",
		checkbox_background_color="#0d1a0d",
		checkbox_background_color_dark="#0d1a0d",
		checkbox_border_color="#1a3a1a",
		checkbox_border_color_dark="#1a3a1a",
		checkbox_label_text_color="#c0c0c0",
		checkbox_label_text_color_dark="#c0c0c0",
		shadow_drop="0 0 12px rgba(0, 255, 136, 0.08)",
		shadow_drop_lg="0 0 20px rgba(0, 255, 136, 0.12)",
	)

	with gr.Blocks(title="CSKG4APT - Cyber Threat Knowledge Graph", theme=cyber_theme, css="""
		/* Global cyber styling */
		.gradio-container {
			max-width: 1400px !important;
			background: #0a0a0a !important;
		}
		/* Header banner */
		.cyber-header {
			text-align: center;
			padding: 24px 0 16px 0;
			border-bottom: 1px solid #1a3a1a;
			margin-bottom: 16px;
		}
		.cyber-header h1 {
			font-size: 2.2em;
			font-weight: 700;
			color: #00ff88;
			text-shadow: 0 0 20px rgba(0, 255, 136, 0.4), 0 0 40px rgba(0, 255, 136, 0.1);
			letter-spacing: 3px;
			margin: 0;
		}
		.cyber-header .subtitle {
			font-size: 0.85em;
			color: #5a8a5a;
			letter-spacing: 2px;
			margin-top: 4px;
		}
		.cyber-header .version-tag {
			display: inline-block;
			background: #0d1a0d;
			border: 1px solid #1a3a1a;
			border-radius: 4px;
			padding: 2px 10px;
			font-size: 0.7em;
			color: #00cc66;
			margin-top: 8px;
		}
		/* Section headers */
		.section-title {
			color: #00ff88 !important;
			border-left: 3px solid #00cc66;
			padding-left: 10px;
			font-size: 1em !important;
		}
		/* Stat cards */
		.stat-card {
			background: linear-gradient(135deg, #0d1a0d 0%, #111a11 100%);
			border: 1px solid #1a3a1a;
			border-radius: 8px;
			padding: 12px;
			text-align: center;
		}
		.stat-card .stat-value {
			font-size: 1.8em;
			font-weight: 700;
			color: #00ff88;
		}
		.stat-card .stat-label {
			font-size: 0.75em;
			color: #5a8a5a;
			text-transform: uppercase;
			letter-spacing: 1px;
		}
		/* Buttons */
		.run-btn {
			background: linear-gradient(135deg, #00cc66, #00aa55) !important;
			border: none !important;
			font-weight: 700 !important;
			letter-spacing: 1px !important;
			text-transform: uppercase !important;
			box-shadow: 0 0 15px rgba(0, 204, 102, 0.3) !important;
			transition: all 0.3s ease !important;
		}
		.run-btn:hover {
			box-shadow: 0 0 25px rgba(0, 255, 136, 0.5) !important;
		}
		/* Tab styling */
		.tabs > .tab-nav > button {
			color: #5a8a5a !important;
			border-bottom: 2px solid transparent !important;
			font-weight: 600 !important;
			letter-spacing: 1px !important;
		}
		.tabs > .tab-nav > button.selected {
			color: #00ff88 !important;
			border-bottom: 2px solid #00ff88 !important;
		}
		/* Metric table */
		.metric-label th, .metric-label td {
			border: 1px solid #1a3a1a !important;
			color: #b0b0b0 !important;
		}
		.metric-label th {
			color: #00cc66 !important;
		}
		.shadowbox {
			background: #111111 !important;
			border: 1px solid #1a3a1a !important;
			border-radius: 6px !important;
			padding: 8px !important;
		}
		.note-text { text-align: center !important; }
		#resizable-results { resize: both; overflow: auto; min-height: 200px; min-width: 300px; max-width: 100%; }
		/* Image container */
		.image-container {
			background: none !important; border: none !important;
			padding: 0 !important; margin: 0 auto !important;
			display: flex !important; justify-content: center !important;
		}
		.image-container img { border: none !important; box-shadow: none !important; }
		.metric-label .wrap { display: none !important; }
	""") as app:

		# ===== HEADER =====
		gr.HTML("""
			<div class="cyber-header">
				<h1>CSKG4APT</h1>
				<div class="subtitle">CYBERSECURITY KNOWLEDGE GRAPH FOR APT ANALYSIS</div>
				<div class="version-tag">v2.0 // LLM-Driven Threat Intelligence Platform</div>
			</div>
		""")

		if warning:
			gr.Markdown(f"<div style='color: #ff6644; background: #1a1111; border: 1px solid #3a1a1a; border-radius: 6px; padding: 10px; text-align: center;'>{warning}</div>")

		# ===== TABS =====
		with gr.Tabs():
			# ==================== TAB 1: CSKG4APT (PRIMARY) ====================
			with gr.TabItem("APT Threat Analysis"):
				gr.Markdown("<div class='section-title'>INPUT CONFIGURATION</div>")

				with gr.Row():
					with gr.Column(scale=2):
						cskg_input_source = gr.Radio(
							choices=["CTI Text", "Upload PDF"],
							value="CTI Text",
							label="Input Source",
						)
						cskg_text_input = gr.Textbox(
							label="Threat Intelligence Text",
							placeholder="Paste CTI report content here for APT entity and relation extraction...",
							lines=12,
							visible=True,
						)
						cskg_pdf_input = gr.File(
							label="Upload PDF Report",
							file_types=[".pdf"],
							visible=False,
						)

						def toggle_cskg_input(source_choice):
							use_pdf = source_choice == "Upload PDF"
							return gr.update(visible=not use_pdf), gr.update(visible=use_pdf)

						cskg_input_source.change(
							fn=toggle_cskg_input,
							inputs=[cskg_input_source],
							outputs=[cskg_text_input, cskg_pdf_input],
						)

					with gr.Column(scale=1):
						gr.Markdown("<div class='section-title'>MODEL SETTINGS</div>")
						cskg_provider = gr.Dropdown(
							choices=list(MODELS.keys()) if MODELS else [],
							label="AI Provider",
							value="OpenAI" if "OpenAI" in MODELS else (list(MODELS.keys())[0] if MODELS else None),
						)
						_cskg_default_prov = "OpenAI" if "OpenAI" in MODELS else (list(MODELS.keys())[0] if MODELS else None)
						cskg_model = gr.Dropdown(
							choices=get_model_choices(_cskg_default_prov) + [("Other", "Other")]
							if _cskg_default_prov else [],
							label="Model",
							value=get_model_choices(_cskg_default_prov)[0][1]
							if _cskg_default_prov and get_model_choices(_cskg_default_prov) else None,
						)
						cskg_custom_model = gr.Textbox(
							label="Custom Model Name",
							placeholder="e.g. gpt-4o, deepseek-chat",
							visible=False,
						)
						with gr.Group(visible=False) as cskg_custom_endpoint_group:
							cskg_custom_base_url = gr.Textbox(
								label="API Base URL",
								placeholder="https://api.example.com/v1",
								value=os.getenv("CUSTOM_BASE_URL", ""),
							)
							cskg_custom_api_key = gr.Textbox(
								label="API Key",
								type="password",
								value=os.getenv("CUSTOM_API_KEY", ""),
							)

						def update_cskg_models(provider):
							choices = get_model_choices(provider) + [("Other", "Other")]
							model_dd = gr.Dropdown(choices=choices, value=choices[0][1] if choices else None)
							endpoint_visible = (provider == "Custom")
							return model_dd, gr.update(visible=endpoint_visible)

						def toggle_cskg_custom_model(model_value):
							return gr.update(visible=(model_value == "Other"))

						cskg_provider.change(fn=update_cskg_models, inputs=[cskg_provider], outputs=[cskg_model, cskg_custom_endpoint_group])
						cskg_model.change(fn=toggle_cskg_custom_model, inputs=[cskg_model], outputs=[cskg_custom_model])

						gr.Markdown("<div class='section-title' style='margin-top:12px;'>ANALYSIS OPTIONS</div>")
						cskg_diamond = gr.Checkbox(label="Diamond Model Analysis", value=True)
						cskg_threat_card = gr.Checkbox(label="APT Threat Card Generation", value=True)
						cskg_neo4j = gr.Checkbox(label="Neo4j Graph Persistence", value=False)

						with gr.Group(visible=False) as neo4j_config_group:
							cskg_neo4j_uri = gr.Textbox(label="Neo4j URI", value="bolt://localhost:7687")
							cskg_neo4j_user = gr.Textbox(label="Username", value="neo4j")
							cskg_neo4j_pass = gr.Textbox(label="Password", type="password")

						cskg_neo4j.change(fn=lambda x: gr.update(visible=x), inputs=[cskg_neo4j], outputs=[neo4j_config_group])

						cskg_run_btn = gr.Button("EXECUTE ANALYSIS", variant="primary", elem_classes=["run-btn"])

				gr.Markdown("<div class='section-title' style='margin-top:12px;'>EXTRACTION RESULTS</div>")

				with gr.Row():
					with gr.Column(scale=1):
						cskg_results = gr.Code(
							label="Knowledge Graph JSON",
							language="json",
							interactive=False,
							show_line_numbers=False,
						)
					with gr.Column(scale=2):
						cskg_graph = gr.HTML(
							label="Knowledge Graph Visualization",
							value='<div style="text-align: center; padding: 40px; color: #3a6b3a; border: 1px dashed #1a3a1a; border-radius: 8px;"><p style="font-size: 1.1em;">AWAITING INPUT</p><p style="font-size: 0.8em; color: #2a4a2a;">Click EXECUTE ANALYSIS to generate the APT knowledge graph</p></div>',
						)

				gr.Markdown("<div class='section-title' style='margin-top:12px;'>THREAT INTELLIGENCE OUTPUT</div>")

				with gr.Row():
					with gr.Column():
						cskg_threat_cards_output = gr.Code(
							label="APT Threat Cards",
							language="json",
							interactive=False,
							show_line_numbers=False,
						)
					with gr.Column():
						cskg_diamond_output = gr.Code(
							label="Diamond Model Vertices",
							language="json",
							interactive=False,
							show_line_numbers=False,
						)

				# ===== HISTORY SECTION (CSKG4APT Tab) =====
				gr.Markdown("<div class='section-title' style='margin-top:12px;'>EXTRACTION HISTORY</div>")
				with gr.Row():
					with gr.Column(scale=3):
						cskg_history_dropdown = gr.Dropdown(
							choices=ResultHistory.get_choices(pipeline_type="cskg4apt"),
							label="Previous Extractions",
							value=None,
							info="Select a past result to reload",
						)
					with gr.Column(scale=1):
						cskg_load_history_btn = gr.Button("Load Selected", variant="secondary")
						cskg_delete_history_btn = gr.Button("Delete Selected", variant="stop")

				def run_cskg4apt_with_progress(
					input_source, text, pdf_file, provider, model, custom_model,
					custom_base_url, custom_api_key,
					diamond, threat_card, neo4j_enabled,
					neo4j_uri, neo4j_user, neo4j_pass,
					progress=gr.Progress(track_tqdm=False),
				):
					if model == "Other" and custom_model and custom_model.strip():
						resolved_model = f"{provider}/{custom_model.strip()}"
					elif model and provider:
						resolved_model = f"{provider}/{model}"
					else:
						resolved_model = model

					return process_and_visualize_cskg4apt(
						input_source, text, pdf_file, resolved_model,
						diamond, threat_card, neo4j_enabled,
						neo4j_uri, neo4j_user, neo4j_pass,
						custom_base_url=custom_base_url,
						custom_api_key=custom_api_key,
						progress=progress,
					)

				cskg_run_btn.click(
					fn=lambda: ("", None, "", ""),
					inputs=[],
					outputs=[cskg_results, cskg_graph, cskg_threat_cards_output, cskg_diamond_output],
				).then(
					fn=run_cskg4apt_with_progress,
					inputs=[
						cskg_input_source, cskg_text_input, cskg_pdf_input,
						cskg_provider, cskg_model, cskg_custom_model,
						cskg_custom_base_url, cskg_custom_api_key,
						cskg_diamond, cskg_threat_card, cskg_neo4j,
						cskg_neo4j_uri, cskg_neo4j_user, cskg_neo4j_pass,
					],
					outputs=[cskg_results, cskg_graph, cskg_threat_cards_output, cskg_diamond_output],
				)

				def cskg_load_selected(history_id):
					result, graph, tc, dm = _load_history_entry(history_id, "cskg4apt")
					return result, graph, tc, dm

				def cskg_delete_selected(history_id):
					dd_update = _delete_history_entry(history_id, "cskg4apt")
					return dd_update, "", None, "{}", "{}"

				cskg_load_history_btn.click(
					fn=cskg_load_selected,
					inputs=[cskg_history_dropdown],
					outputs=[cskg_results, cskg_graph, cskg_threat_cards_output, cskg_diamond_output],
				)
				cskg_delete_history_btn.click(
					fn=cskg_delete_selected,
					inputs=[cskg_history_dropdown],
					outputs=[cskg_history_dropdown, cskg_results, cskg_graph, cskg_threat_cards_output, cskg_diamond_output],
				)

			# ==================== TAB 2: GENERIC PIPELINE ====================
			with gr.TabItem("Generic CTI Pipeline"):
				gr.Markdown("<div class='section-title'>GENERIC KNOWLEDGE GRAPH EXTRACTION</div>")
				gr.Markdown(
					"Standard 4-stage pipeline: Intelligence Extraction -> Entity Tagging -> Entity Alignment -> Link Prediction",
					elem_classes=["note-text"],
				)

				with gr.Row():
					with gr.Column():
						input_source_selector = gr.Radio(
							choices=["CTI Report URL", "CTI Text"],
							value="CTI Report URL",
							label="Input Source",
						)
						url_input = gr.Textbox(
							label="CTI Report URL",
							placeholder="https://example.com/report",
							lines=1,
							visible=True,
						)
						text_input = gr.Textbox(
							label="Input Threat Intelligence",
							placeholder="Enter text for processing...",
							lines=10,
							visible=False,
						)

						def toggle_input_source(source_choice):
							use_text_input = source_choice == "CTI Text"
							return gr.update(visible=use_text_input), gr.update(visible=not use_text_input)

						input_source_selector.change(
							fn=toggle_input_source,
							inputs=[input_source_selector],
							outputs=[text_input, url_input],
						)

						with gr.Row():
							with gr.Column(scale=1):
								provider_dropdown = gr.Dropdown(
									choices=list(MODELS.keys()) if MODELS else [],
									label="AI Provider",
									value="OpenAI" if "OpenAI" in MODELS else (list(MODELS.keys())[0] if MODELS else None),
								)
							with gr.Column(scale=2):
								ie_dropdown = gr.Dropdown(
									choices=get_model_choices(provider_dropdown.value) + [("Other", "Other")]
									if provider_dropdown.value else [],
									label="Intelligence Extraction Model",
									value=get_model_choices(provider_dropdown.value)[0][1]
									if provider_dropdown.value and get_model_choices(provider_dropdown.value) else None,
								)
							with gr.Column(scale=2):
								et_dropdown = gr.Dropdown(
									choices=get_model_choices(provider_dropdown.value) + [("Other", "Other")]
									if provider_dropdown.value else [],
									label="Entity Tagging Model",
									value=get_model_choices(provider_dropdown.value)[0][1]
									if provider_dropdown.value and get_model_choices(provider_dropdown.value) else None,
								)
						with gr.Row():
							with gr.Column(scale=2):
								ea_dropdown = gr.Dropdown(
									choices=get_embedding_model_choices(provider_dropdown.value) + [("Other", "Other")]
									if provider_dropdown.value else [],
									label="Entity Alignment Model",
									value=get_embedding_model_choices(provider_dropdown.value)[0][1]
									if provider_dropdown.value and get_embedding_model_choices(provider_dropdown.value) else None,
								)
							with gr.Column(scale=1):
								similarity_slider = gr.Slider(
									minimum=0.0, maximum=1.0, value=0.6, step=0.05,
									label="Alignment Threshold",
								)
							with gr.Column(scale=2):
								lp_dropdown = gr.Dropdown(
									choices=get_model_choices(provider_dropdown.value) + [("Other", "Other")]
									if provider_dropdown.value else [],
									label="Link Prediction Model",
									value=get_model_choices(provider_dropdown.value)[0][1]
									if provider_dropdown.value and get_model_choices(provider_dropdown.value) else None,
								)

						with gr.Row():
							with gr.Column(scale=1):
								custom_model_input = gr.Textbox(label="Custom Model", placeholder="Enter custom model name...", visible=False)
							with gr.Column(scale=1):
								custom_embedding_model_input = gr.Textbox(label="Custom Embedding Model", placeholder="Enter custom embedding model name...", visible=False)

						with gr.Group(visible=False) as custom_endpoint_group:
							gr.Markdown("**Custom Endpoint Configuration**")
							with gr.Row():
								custom_base_url_input = gr.Textbox(
									label="API Base URL",
									placeholder="https://api.example.com/v1",
									value=os.getenv("CUSTOM_BASE_URL", ""),
								)
								custom_api_key_input = gr.Textbox(
									label="API Key",
									type="password",
									value=os.getenv("CUSTOM_API_KEY", ""),
								)

						def toggle_custom_model_inputs(ie_value, et_value, ea_value, lp_value):
							show_custom_model = any(value == "Other" for value in [ie_value, et_value, lp_value])
							show_custom_embedding_model = ea_value == "Other"
							return gr.update(visible=show_custom_model), gr.update(visible=show_custom_embedding_model)

						ie_dropdown.change(fn=toggle_custom_model_inputs, inputs=[ie_dropdown, et_dropdown, ea_dropdown, lp_dropdown], outputs=[custom_model_input, custom_embedding_model_input])
						et_dropdown.change(fn=toggle_custom_model_inputs, inputs=[ie_dropdown, et_dropdown, ea_dropdown, lp_dropdown], outputs=[custom_model_input, custom_embedding_model_input])
						ea_dropdown.change(fn=toggle_custom_model_inputs, inputs=[ie_dropdown, et_dropdown, ea_dropdown, lp_dropdown], outputs=[custom_model_input, custom_embedding_model_input])
						lp_dropdown.change(fn=toggle_custom_model_inputs, inputs=[ie_dropdown, et_dropdown, ea_dropdown, lp_dropdown], outputs=[custom_model_input, custom_embedding_model_input])

						run_all_button = gr.Button("RUN PIPELINE", variant="primary", elem_classes=["run-btn"])

				with gr.Row():
					metrics_table = gr.Markdown(value=get_metrics_box(), elem_classes=["metric-label"])

				with gr.Row():
					with gr.Column(scale=1):
						results_box = gr.Code(label="Results", language="json", interactive=False, show_line_numbers=False, elem_id="resizable-results")
					with gr.Column(scale=2):
						graph_output = gr.HTML(
							label="Entity Relationship Graph",
							value='<div style="text-align: center; padding: 40px; color: #3a6b3a; border: 1px dashed #1a3a1a; border-radius: 8px;"><p>AWAITING INPUT</p><p style="font-size: 0.8em; color: #2a4a2a;">Click RUN PIPELINE to generate a visualization</p></div>',
						)

				def update_model_choices(provider):
					model_choices = get_model_choices(provider) + [("Other", "Other")]
					embedding_choices = get_embedding_model_choices(provider) + [("Other", "Other")]
					return (
						gr.Dropdown(choices=model_choices, value=model_choices[0][1] if model_choices else None),
						gr.Dropdown(choices=model_choices, value=model_choices[0][1] if model_choices else None),
						gr.Dropdown(choices=embedding_choices, value=embedding_choices[0][1] if embedding_choices else None),
						gr.Dropdown(choices=model_choices, value=model_choices[0][1] if model_choices else None),
						gr.update(visible=(provider == "Custom")),
					)

				provider_dropdown.change(fn=update_model_choices, inputs=[provider_dropdown], outputs=[ie_dropdown, et_dropdown, ea_dropdown, lp_dropdown, custom_endpoint_group])

				def process_and_visualize_with_progress(
					input_source, text, source_url, ie_model, et_model, ea_model, lp_model,
					similarity_threshold, provider_dropdown, custom_model_input, custom_embedding_model_input,
					custom_base_url, custom_api_key,
					progress=gr.Progress(track_tqdm=False),
				):
					return process_and_visualize(
						input_source, text, source_url, ie_model, et_model, ea_model, lp_model,
						similarity_threshold, provider_dropdown, custom_model_input, custom_embedding_model_input,
						custom_base_url, custom_api_key,
						progress=progress,
					)

				run_all_button.click(
					fn=clear_outputs, inputs=[], outputs=[results_box, graph_output, metrics_table],
				).then(
					fn=process_and_visualize_with_progress,
					inputs=[input_source_selector, text_input, url_input, ie_dropdown, et_dropdown, ea_dropdown, lp_dropdown,
						similarity_slider, provider_dropdown, custom_model_input, custom_embedding_model_input,
						custom_base_url_input, custom_api_key_input],
					outputs=[results_box, graph_output, metrics_table],
				)

				# ===== HISTORY SECTION (Generic Tab) =====
				gr.Markdown("<div class='section-title' style='margin-top:12px;'>PIPELINE HISTORY</div>")
				with gr.Row():
					with gr.Column(scale=3):
						generic_history_dropdown = gr.Dropdown(
							choices=ResultHistory.get_choices(pipeline_type="generic"),
							label="Previous Pipeline Runs",
							value=None,
							info="Select a past result to reload",
						)
					with gr.Column(scale=1):
						generic_load_history_btn = gr.Button("Load Selected", variant="secondary")
						generic_delete_history_btn = gr.Button("Delete Selected", variant="stop")

				def generic_load_selected(history_id):
					result, graph, metrics = _load_history_entry(history_id, "generic")
					return result, graph, metrics

				def generic_delete_selected(history_id):
					dd_update = _delete_history_entry(history_id, "generic")
					return dd_update, "", None, get_metrics_box()

				generic_load_history_btn.click(
					fn=generic_load_selected,
					inputs=[generic_history_dropdown],
					outputs=[results_box, graph_output, metrics_table],
				)
				generic_delete_history_btn.click(
					fn=generic_delete_selected,
					inputs=[generic_history_dropdown],
					outputs=[generic_history_dropdown, results_box, graph_output, metrics_table],
				)

		# ===== FOOTER =====
		gr.HTML("""
			<div style="text-align: center; padding: 16px 0; border-top: 1px solid #1a3a1a; margin-top: 16px;">
				<span style="color: #2a4a2a; font-size: 0.75em; letter-spacing: 2px;">
					CSKG4APT // CYBERSECURITY KNOWLEDGE GRAPH FOR ADVANCED PERSISTENT THREAT ANALYSIS
				</span>
			</div>
		""")

		def _refresh_all_history():
			cskg_choices = ResultHistory.get_choices(pipeline_type="cskg4apt")
			generic_choices = ResultHistory.get_choices(pipeline_type="generic")
			return gr.update(choices=cskg_choices, value=None), gr.update(choices=generic_choices, value=None)

		app.load(
			fn=_refresh_all_history,
			outputs=[cskg_history_dropdown, generic_history_dropdown],
		)

	return app

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CSKG4APT-CTI: APT threat intelligence knowledge graph construction platform. Uses LLMs to extract entities and relations from unstructured CTI reports, builds cybersecurity knowledge graphs (12 entity types, 7 relation types), and supports APT attribution analysis.

## Commands

All commands run from `cskg4apt/` subdirectory (where `pyproject.toml` lives).

```bash
# Install
pip install -e .                # basic
pip install -e ".[dev]"         # with dev tools (ruff, pytest, pre-commit)
pip install -e ".[neo4j]"       # with Neo4j driver

# Run Web UI
cd .. && python start_cskg4apt.py
# Or: cskg4apt (CLI entry point)

# Tests
pytest tests/ -v                                    # all tests
pytest tests/unit/test_cskg4apt_schema.py -v        # single file
pytest tests/unit/test_cskg4apt_schema.py::TestEntityType::test_all_12_types_exist -v  # single test
pytest tests/ -m unit -v                            # by marker (unit|integration|slow)
pytest tests/ --cov=cskg4apt --cov-report=term-missing  # with coverage

# Lint / Format
ruff check . --fix
ruff format .
pre-commit run --all-files
```

## Architecture

### Two Extraction Modes

**Default Pipeline** (IE → ET → EA → LP) — orchestrated by `utils/gradio_utils.py:run_pipeline()`:
1. **IE** (`LLMExtractor`): Extract subject-relation-object triplets from CTI text → `prompts/ie.jinja`
2. **ET** (`LLMTagger`): Classify each entity into types → `prompts/et.jinja`
3. **EA** (`Merger`): Embed mentions, merge by cosine similarity (threshold 0.6); `PostProcessor` adds IOC detection
4. **LP** (`Linker` + `LLMLinker`): Find disconnected subgraphs via DFS, predict missing relations → `prompts/link.jinja`

**CSKG4APT Mode** — `cskg4apt_extractor.py:CSKG4APTExtractor`:
1. Extract entities (12 types) → `prompts/cskg4apt_entity.jinja`
2. Extract relations (7 types with source→target constraints) → `prompts/cskg4apt_relation.jinja`

Both modes produce graphs visualized via Pyvis (saved to `cskg4apt_output/`).

### Key Source Files

| File | Role |
|------|------|
| `app.py` | Gradio UI + CLI entry point (`main()`) |
| `llm_processor.py` | All LLM interaction: `LLMCaller`, `LLMExtractor`, `LLMTagger`, `LLMLinker`, `UrlSourceInput`, prompt construction, response parsing, cost tracking |
| `cti_processor.py` | `preprocessor()` (ET→EA transform), `PostProcessor` (IOC detection + dedup), `IOC_detect()` (regex-based) |
| `graph_constructor.py` | `Merger` (embedding alignment), `Linker` (subgraph DFS), `create_*_graph_visualization()` (Pyvis) |
| `cskg4apt_extractor.py` | CSKG4APT mode: entity + relation extraction with Pydantic validation |
| `utils/gradio_utils.py` | `run_pipeline()`, `run_cskg4apt_pipeline()`, `build_interface()`, Hydra config loading |

### Submodules

- `schemas/cskg4apt_ontology.py` — EntityType enum (12), RelationType enum (7), `RELATION_TYPE_CONSTRAINTS`, `CSKGEntity`, `CSKGRelation`, `CSKG4APTGraph`
- `schemas/apt_attributes.py` — `APTThreatCard`, `AttackChain`, `DiamondModelVertex`
- `attribution/` — `APTAttributor` (threat cards, attack chains), `DiamondModelAnalyzer`
- `graph_db/neo4j_handler.py` — Optional Neo4j persistence with graceful fallback
- `prompts/` — Jinja2 templates for all LLM prompts
- `config/config.yaml` — Hydra/OmegaConf defaults; `config/cost.json` — per-model pricing

## Code Conventions

- **Indentation**: Tabs (not spaces) — enforced by ruff
- **Quotes**: Double quotes — enforced by ruff
- **Line length**: 120
- **Target Python**: 3.10+
- **Schema validation**: Pydantic v2 with `field_validator`
- **Config**: Hydra/OmegaConf (`config.yaml`)
- **LLM calls**: Always via `litellm` through `LLMCaller` or `call_litellm_completion()` — never call LLM APIs directly
- **Prompts**: Jinja2 templates in `prompts/` directory — never inline prompt text in Python
- **Path resolution**: Use `resolve_path()` from `utils/path_utils.py` for any file paths relative to package root
- **Logging**: `logging.getLogger(__name__)` — no print statements
- **Language**: Code in English; UI strings and comments may be in Chinese

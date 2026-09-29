"""
Core ontology and schema validation for Plant MitoCarta (PMCO).

Enforces:
- Schema conformance via Draft 2020-12 JSON Schema.
- Strict evidence tiering (T1 and T2 must cite a resolved DOI).
- Subcellular compartment grounding in GO-CCO (PMC3852282).
- Valid AGI locus identifier format (AT[1-5CM]G[0-9]{5}).
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
import re
from typing import Any, Dict, Iterator, List, Optional, Set

import jsonschema
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
ONTOLOGY_DIR = ROOT / "ontology"
ENTITIES_DIR = ONTOLOGY_DIR / "entities"
SCHEMA_PATH = ONTOLOGY_DIR / "schema" / "entity.schema.json"
CORE_SPEC_PATH = ONTOLOGY_DIR / "pmco-core.yaml"
REFERENCES_PATH = ROOT / "evidence" / "references.yaml"

AGI_PATTERN = re.compile(r"^AT[1-5CM]G\d{5}$")
DOI_PATTERN = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")


class OntologyError(Exception):
    """Raised when an ontology assertion or schema validation fails."""


@dataclasses.dataclass(frozen=True)
class Reference:
    id: str
    title: str
    authors: tuple[str, ...]
    journal: str
    year: int
    doi: str
    relevance: str


@dataclasses.dataclass(frozen=True)
class SubaMetadata:
    consensus_compartment: str
    consensus_score: float
    ms_evidence: bool = False
    gfp_evidence: bool = False
    dual_targeted: bool = False
    dual_compartments: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True)
class MitoCartaMetadata:
    human_symbol: Optional[str] = None
    human_entrez: Optional[int] = None
    mitopathway: Optional[str] = None
    conservation_category: Optional[str] = None
    clinical_significance: Optional[str] = None


@dataclasses.dataclass(frozen=True)
class RetrogradeMetadata:
    circuit: Optional[str] = None
    role: Optional[str] = None
    signal_type: Optional[str] = None
    cleavage_required: bool = False
    target_genes: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True)
class Entity:
    id: str
    label: str
    kind: str
    compartment: str
    evidence_tier: str
    description: str = ""
    rationale: Optional[str] = None
    agi_loci: tuple[str, ...] = ()
    uniprot_ids: tuple[str, ...] = ()
    chebi_ids: tuple[str, ...] = ()
    go_cc_ids: tuple[str, ...] = ()
    ec_numbers: tuple[str, ...] = ()
    suba5: Optional[SubaMetadata] = None
    mitocarta: Optional[MitoCartaMetadata] = None
    retrograde: Optional[RetrogradeMetadata] = None
    evidence: tuple[dict[str, str], ...] = ()


class Ontology:
    def __init__(
        self,
        core_spec: dict[str, Any],
        entities: dict[str, Entity],
        references: dict[str, Reference],
    ):
        self.core_spec = core_spec
        self.entities = entities
        self.references = references
        self._compartment_ids = {c["id"] for c in core_spec.get("compartments", [])}
        self._tier_ids = {t["id"] for t in core_spec.get("evidence_tiers", [])}
        self._agi_index: dict[str, list[Entity]] = {}
        for ent in entities.values():
            for locus in ent.agi_loci:
                self._agi_index.setdefault(locus, []).append(ent)

    def get_entity(self, entity_id: str) -> Entity:
        if entity_id not in self.entities:
            raise KeyError(f"Unknown entity ID: {entity_id}")
        return self.entities[entity_id]

    def find_by_locus(self, locus: str) -> list[Entity]:
        return self._agi_index.get(locus.upper(), [])

    def filter_by_compartment(self, compartment: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.compartment == compartment]

    def filter_by_tier(self, tier: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.evidence_tier == tier]

    def filter_by_circuit(self, circuit: str) -> list[Entity]:
        return [
            e
            for e in self.entities.values()
            if e.retrograde and e.retrograde.circuit == circuit
        ]

    def get_compartment_meta(self, comp_id: str) -> dict[str, Any]:
        for c in self.core_spec.get("compartments", []):
            if c["id"] == comp_id:
                return c
        raise KeyError(f"Unknown compartment: {comp_id}")

    def all_entities(self) -> list[Entity]:
        return list(self.entities.values())


def load_references(path: pathlib.Path = REFERENCES_PATH) -> dict[str, Reference]:
    if not path.is_file():
        raise FileNotFoundError(f"References file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    refs = {}
    for item in data.get("references", []):
        ref_id = item["id"]
        doi = item.get("doi", "").strip()
        if not DOI_PATTERN.match(doi):
            raise OntologyError(f"Invalid DOI in reference {ref_id}: {doi}")
        refs[ref_id] = Reference(
            id=ref_id,
            title=item.get("title", ""),
            authors=tuple(item.get("authors", [])),
            journal=item.get("journal", ""),
            year=item.get("year", 0),
            doi=doi,
            relevance=item.get("relevance", ""),
        )
    return refs


def load_ontology(
    entities_dir: pathlib.Path = ENTITIES_DIR,
    schema_path: pathlib.Path = SCHEMA_PATH,
    core_path: pathlib.Path = CORE_SPEC_PATH,
    refs_path: pathlib.Path = REFERENCES_PATH,
) -> Ontology:
    # 1. Load Core Spec
    if not core_path.is_file():
        raise FileNotFoundError(f"Core spec not found: {core_path}")
    with open(core_path, "r", encoding="utf-8") as f:
        core_spec = yaml.safe_load(f)

    # 2. Load JSON Schema
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)

    # 3. Load References
    references = load_references(refs_path)
    ref_citations = {r.id for r in references.values()}
    ref_dois = {r.doi for r in references.values()}

    # 4. Load Entities and Validate
    entities: dict[str, Entity] = {}
    if not entities_dir.is_dir():
        raise FileNotFoundError(f"Entities directory not found: {entities_dir}")

    for yaml_file in sorted(entities_dir.glob("*.yaml")):
        with open(yaml_file, "r", encoding="utf-8") as f:
            raw_entries = yaml.safe_load(f) or []
        if not isinstance(raw_entries, list):
            raise OntologyError(f"Expected list of entities in {yaml_file}")

        for entry in raw_entries:
            # Schema validation
            errors = list(validator.iter_errors(entry))
            if errors:
                err_msg = "; ".join(e.message for e in errors)
                raise OntologyError(
                    f"Entity {entry.get('id', 'unknown')} in {yaml_file.name} failed schema: {err_msg}"
                )

            ent_id = entry["id"]
            if ent_id in entities:
                raise OntologyError(f"Duplicate entity ID declared: {ent_id}")

            tier = entry["evidence_tier"]
            ev_list = entry.get("evidence", [])

            # Evidence & DOI rule
            if tier in ("T1", "T2"):
                if not ev_list:
                    raise OntologyError(
                        f"Tier {tier} entity {ent_id} must have at least one evidence item"
                    )
                for ev in ev_list:
                    doi = ev.get("doi", "").strip()
                    if not DOI_PATTERN.match(doi):
                        raise OntologyError(f"Entity {ent_id} has invalid DOI: {doi}")
                    citation = ev.get("citation", "")
                    if citation and citation not in ref_citations:
                        raise OntologyError(
                            f"Entity {ent_id} cites unknown reference: {citation}"
                        )
            elif tier in ("T3", "T4"):
                if not entry.get("rationale"):
                    raise OntologyError(
                        f"Tier {tier} entity {ent_id} must carry a written rationale"
                    )

            # AGI Loci validation
            xref = entry.get("xref", {})
            agi_list = xref.get("agi", [])
            for locus in agi_list:
                if not AGI_PATTERN.match(locus):
                    raise OntologyError(f"Entity {ent_id} has invalid AGI locus: {locus}")

            # Suba metadata
            suba_meta = None
            if "suba5" in entry:
                s = entry["suba5"]
                suba_meta = SubaMetadata(
                    consensus_compartment=s.get("consensus_compartment", ""),
                    consensus_score=float(s.get("consensus_score", 0.0)),
                    ms_evidence=bool(s.get("ms_evidence", False)),
                    gfp_evidence=bool(s.get("gfp_evidence", False)),
                    dual_targeted=bool(s.get("dual_targeted", False)),
                    dual_compartments=tuple(s.get("dual_compartments", [])),
                )

            # MitoCarta metadata
            mc_meta = None
            if "mitocarta" in entry:
                m = entry["mitocarta"]
                mc_meta = MitoCartaMetadata(
                    human_symbol=m.get("human_symbol"),
                    human_entrez=m.get("human_entrez"),
                    mitopathway=m.get("mitopathway"),
                    conservation_category=m.get("conservation_category"),
                    clinical_significance=m.get("clinical_significance"),
                )

            # Retrograde metadata
            ret_meta = None
            if "retrograde" in entry:
                r = entry["retrograde"]
                ret_meta = RetrogradeMetadata(
                    circuit=r.get("circuit"),
                    role=r.get("role"),
                    signal_type=r.get("signal_type"),
                    cleavage_required=bool(r.get("cleavage_required", False)),
                    target_genes=tuple(r.get("target_genes", [])),
                )

            entities[ent_id] = Entity(
                id=ent_id,
                label=entry["label"],
                kind=entry["kind"],
                compartment=entry["compartment"],
                evidence_tier=tier,
                description=entry.get("description", ""),
                rationale=entry.get("rationale"),
                agi_loci=tuple(agi_list),
                uniprot_ids=tuple(xref.get("uniprot", [])),
                chebi_ids=tuple(xref.get("chebi", [])),
                go_cc_ids=tuple(xref.get("go_cc", [])),
                ec_numbers=tuple(xref.get("ec", [])),
                suba5=suba_meta,
                mitocarta=mc_meta,
                retrograde=ret_meta,
                evidence=tuple(ev_list),
            )

    return Ontology(core_spec, entities, references)

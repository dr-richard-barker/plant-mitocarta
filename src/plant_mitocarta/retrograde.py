"""
Retrograde Signaling & Inter-Organellar Crosstalk Network Engine.

Models the 5 fundamental organellar communication circuits:
1. Mito-to-Nucleus Retrograde Response (MRR): Protease cleavage of ANAC017/013, MDRE binding, AOX1a induction.
2. Plasto-to-Nucleus Retrograde Response (PRR): SAL1-PAP-XRN2/3, GUN1-ABI4, MEcPP, Singlet Oxygen-EXECUTER 1.
3. Plasma Membrane-to-Organelle Systemic Waves: Mechanical strain (WAK/FER) -> GLR Ca2+ spike -> RBOHD ROS wave -> PIP2;1 channeling.
4. The 3-Organelle Photorespiratory Loop: Chloroplast (glycolate) <-> Peroxisome (glycine) <-> Mitochondria (GDC/SHMT serine).
5. Physical Contact Sites: Stromules channeling concentrated H2O2 to the nuclear envelope, and MEAMs.
"""
from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional, Tuple


@dataclasses.dataclass(frozen=True)
class RetroNode:
    id: str
    label: str
    compartment: str
    node_type: str  # sensor, messenger, translocator, transcription_factor, promoter_target, bypass
    agi_locus: Optional[str] = None
    description: str = ""


@dataclasses.dataclass(frozen=True)
class RetroEdge:
    src: str
    dst: str
    interaction: str  # cleavage, translocation, phosphorylation, activation, inhibition, metabolite_flux
    label: str = ""
    circuit: str = ""


@dataclasses.dataclass
class RetrogradeCircuit:
    id: str
    title: str
    description: str
    nodes: list[RetroNode]
    edges: list[RetroEdge]


def build_mrr_circuit() -> RetrogradeCircuit:
    nodes = [
        RetroNode("MITO_STRESS", "Mitochondrial Stress / ROS", "cristae", "sensor", description="Complex I/III inhibition, membrane depolarization, ROS accumulation"),
        RetroNode("RHOMBOID_PROTEASE", "Rhomboid-Like Protease", "mitochondrial_outer_membrane", "sensor", description="Membrane-embedded protease activated by mitochondrial dysfunction"),
        RetroNode("ANAC017_MEMBRANE", "Tethered ANAC017", "mitochondrial_outer_membrane", "transcription_factor", "AT1G34190", "ER/OMM-anchored precursor form"),
        RetroNode("ANAC017_CLEAVED", "Soluble ANAC017 (NAC domain)", "cytosol", "messenger", "AT1G34190", "Cleaved cytoplasmic fragment migrating towards nucleus"),
        RetroNode("NPC_TRANSIT", "Nuclear Pore Complex", "nuclear_pore_complex", "translocator", description="Mediates active nuclear import of cleaved ANAC017/013"),
        RetroNode("ANAC017_NUCLEAR", "Nuclear ANAC017", "nucleoplasm", "transcription_factor", "AT1G34190", "Active nuclear transcription factor"),
        RetroNode("MDRE_PROMOTER", "MDRE Promoter Motif", "nucleoplasm", "promoter_target", description="Conserved CTTGNNNNNCAG palindromic regulatory element"),
        RetroNode("AOX1A_GENE", "AOX1a Gene Induction", "nucleoplasm", "promoter_target", "AT3G22370", "Alternative oxidase - primary bioenergetic relief valve"),
        RetroNode("UPM1_GENE", "UPM1 / Stress Chaperones", "nucleoplasm", "promoter_target", "AT5G40850", "Mitochondrial protein folding and proteostasis"),
        RetroNode("DTC_EXPORT", "DTC Carrier", "mitochondrial_inner_membrane", "translocator", "AT5G19760", "Exports matrix citrate and 2-OG to cytosol/nucleus"),
    ]
    edges = [
        RetroEdge("MITO_STRESS", "RHOMBOID_PROTEASE", "activation", "ROS trigger", "mrr_mito_nuclear"),
        RetroEdge("RHOMBOID_PROTEASE", "ANAC017_MEMBRANE", "cleavage", "cleaves C-anchor", "mrr_mito_nuclear"),
        RetroEdge("ANAC017_MEMBRANE", "ANAC017_CLEAVED", "translocation", "releases to cytosol", "mrr_mito_nuclear"),
        RetroEdge("ANAC017_CLEAVED", "NPC_TRANSIT", "translocation", "nuclear entry", "mrr_mito_nuclear"),
        RetroEdge("NPC_TRANSIT", "ANAC017_NUCLEAR", "translocation", "enters nucleoplasm", "mrr_mito_nuclear"),
        RetroEdge("ANAC017_NUCLEAR", "MDRE_PROMOTER", "activation", "binds CTTGNNNNNCAG", "mrr_mito_nuclear"),
        RetroEdge("MDRE_PROMOTER", "AOX1A_GENE", "activation", "transcription", "mrr_mito_nuclear"),
        RetroEdge("MDRE_PROMOTER", "UPM1_GENE", "activation", "transcription", "mrr_mito_nuclear"),
        RetroEdge("MITO_STRESS", "DTC_EXPORT", "metabolite_flux", "citrate accumulation", "mrr_mito_nuclear"),
        RetroEdge("DTC_EXPORT", "ANAC017_NUCLEAR", "activation", "epigenetic priming", "mrr_mito_nuclear"),
    ]
    return RetrogradeCircuit(
        id="mrr_mito_nuclear",
        title="Mitochondrial Retrograde Response (MRR)",
        description="The canonical ANAC017/013 proteolytic cleavage and nuclear translocation pathway activating AOX1a.",
        nodes=nodes,
        edges=edges,
    )


def build_prr_circuit() -> RetrogradeCircuit:
    nodes = [
        RetroNode("CHLORO_LIGHT_STRESS", "High Light / Excess Excitation", "thylakoid_membrane", "sensor", description="Over-reduction of plastoquinone pool and ROS release"),
        RetroNode("SAL1_OXIDIZED", "SAL1 Phosphatase Inactivation", "chloroplast_stroma", "sensor", "AT5G63980", "SAL1 is oxidized and inactivated under oxidative stress"),
        RetroNode("PAP_ACCUMULATION", "PAP (3'-Phosphoadenosine 5'-phosphate)", "chloroplast_stroma", "messenger", description="Retrograde metabolite accumulating in stroma"),
        RetroNode("PAPST1_EXPORT", "PAPST1 Transporter", "chloroplast_inner_envelope", "translocator", "AT5G01500", "Exports PAP across chloroplast inner envelope"),
        RetroNode("XRN2_3_INHIBITION", "Nuclear XRN2/XRN3 Exoribonucleases", "nucleoplasm", "transcription_factor", "AT5G42540", "Inhibited by PAP, stabilizing stress transcripts"),
        RetroNode("GUN1_PPR_HUB", "GUN1 Hub", "chloroplast_stroma", "transcription_factor", "AT2G31490", "Integrates plastid protein homeostasis and tetrapyrroles"),
        RetroNode("ABI4_REPRESSOR", "ABI4 Transcription Factor", "nucleoplasm", "transcription_factor", "AT2G40220", "Nuclear repressor of PhANGs downstream of GUN1"),
        RetroNode("PHANGS_GENES", "PhANGs (Lhcb, RbcS)", "nucleoplasm", "promoter_target", description="Photosynthesis-associated nuclear genes repressed under stress"),
        RetroNode("MECPP_ACCUMULATION", "MEcPP Metabolite", "chloroplast_stroma", "messenger", description="MEP pathway intermediate inducing stress responses"),
        RetroNode("EX1_OXYGEN_SENSOR", "EXECUTER 1 (EX1)", "thylakoid_membrane", "sensor", "AT4G33630", "Senses singlet oxygen (1O2) generated at PSII"),
    ]
    edges = [
        RetroEdge("CHLORO_LIGHT_STRESS", "SAL1_OXIDIZED", "inhibition", "disulfide oxidation", "prr_plasto_nuclear"),
        RetroEdge("SAL1_OXIDIZED", "PAP_ACCUMULATION", "activation", "stops catabolism", "prr_plasto_nuclear"),
        RetroEdge("PAP_ACCUMULATION", "PAPST1_EXPORT", "metabolite_flux", "stromal export", "prr_plasto_nuclear"),
        RetroEdge("PAPST1_EXPORT", "XRN2_3_INHIBITION", "inhibition", "direct PAP inhibition", "prr_plasto_nuclear"),
        RetroEdge("CHLORO_LIGHT_STRESS", "GUN1_PPR_HUB", "activation", "protein stress", "prr_plasto_nuclear"),
        RetroEdge("GUN1_PPR_HUB", "ABI4_REPRESSOR", "activation", "signals to nucleus", "prr_plasto_nuclear"),
        RetroEdge("ABI4_REPRESSOR", "PHANGS_GENES", "inhibition", "represses transcription", "prr_plasto_nuclear"),
        RetroEdge("CHLORO_LIGHT_STRESS", "MECPP_ACCUMULATION", "activation", "MEP bottleneck", "prr_plasto_nuclear"),
        RetroEdge("CHLORO_LIGHT_STRESS", "EX1_OXYGEN_SENSOR", "activation", "1O2 generation", "prr_plasto_nuclear"),
    ]
    return RetrogradeCircuit(
        id="prr_plasto_nuclear",
        title="Plastid-to-Nucleus Retrograde Response (PRR)",
        description="Dual-branch plastid retrograde signaling comprising the SAL1-PAP-XRN2/3 pathway and the GUN1-ABI4 hub.",
        nodes=nodes,
        edges=edges,
    )


def build_photorespiration_circuit() -> RetrogradeCircuit:
    nodes = [
        RetroNode("RUBISCO_OXYGENATION", "RuBisCO Oxygenase Activity", "chloroplast_stroma", "sensor", description="Fixes O2 instead of CO2, producing 2-phosphoglycolate"),
        RetroNode("PLGG1_CHLORO", "PLGG1 Translocator", "chloroplast_inner_envelope", "translocator", "AT1G32080", "Exports glycolate from chloroplast to peroxisome"),
        RetroNode("PEROXISOME_CORE", "Peroxisomal Glycolate Oxidase (GOX)", "peroxisome", "sensor", "AT3G14420", "Converts glycolate to glyoxylate and transaminates to glycine"),
        RetroNode("GDC_MATRIX", "Mitochondrial GDC Complex", "mitochondrial_matrix", "sensor", "AT4G33010", "Converts 2 glycine to serine + NADH + CO2 + NH3"),
        RetroNode("SHMT1_MATRIX", "SHMT1", "mitochondrial_matrix", "sensor", "AT4G37930", "Coupled serine synthesis feeding back to peroxisome"),
        RetroNode("DIT1_CHLORO", "DiT1 Translocator", "chloroplast_inner_envelope", "translocator", "AT5G12860", "Imports glycerate and balances 2-OG/malate shuttle"),
    ]
    edges = [
        RetroEdge("RUBISCO_OXYGENATION", "PLGG1_CHLORO", "metabolite_flux", "glycolate", "photorespiration"),
        RetroEdge("PLGG1_CHLORO", "PEROXISOME_CORE", "metabolite_flux", "glycolate -> glycine", "photorespiration"),
        RetroEdge("PEROXISOME_CORE", "GDC_MATRIX", "metabolite_flux", "glycine import", "photorespiration"),
        RetroEdge("GDC_MATRIX", "SHMT1_MATRIX", "metabolite_flux", "5,10-CH2-THF", "photorespiration"),
        RetroEdge("SHMT1_MATRIX", "PEROXISOME_CORE", "metabolite_flux", "serine return", "photorespiration"),
        RetroEdge("PEROXISOME_CORE", "DIT1_CHLORO", "metabolite_flux", "glycerate -> 3-PGA", "photorespiration"),
    ]
    return RetrogradeCircuit(
        id="photorespiration",
        title="The 3-Organelle Photorespiratory Metabolic Highway",
        description="Crucial inter-organellar metabolic shuttle linking Chloroplast, Peroxisome, and Mitochondria.",
        nodes=nodes,
        edges=edges,
    )


def build_retrograde_graph() -> dict[str, Any]:
    """Compile all circuits into a unified graph format for Cytoscape.js."""
    mrr = build_mrr_circuit()
    prr = build_prr_circuit()
    photo = build_photorespiration_circuit()

    circuits = [mrr, prr, photo]
    elements = []

    seen_nodes = set()
    for circ in circuits:
        for n in circ.nodes:
            if n.id not in seen_nodes:
                seen_nodes.add(n.id)
                elements.append({
                    "data": {
                        "id": n.id,
                        "label": n.label,
                        "compartment": n.compartment,
                        "node_type": n.node_type,
                        "agi_locus": n.agi_locus,
                        "description": n.description,
                        "circuit": circ.id,
                    }
                })
        for e in circ.edges:
            elements.append({
                "data": {
                    "id": f"{e.src}_{e.dst}_{e.circuit}",
                    "source": e.src,
                    "target": e.dst,
                    "interaction": e.interaction,
                    "label": e.label,
                    "circuit": e.circuit,
                }
            })

    return {
        "circuits": [c.id for c in circuits],
        "elements": elements,
    }

"""
Digital Double specifications and coordinate models for Plant Subcellular Organelles:
1. Mitochondrion (Plant MitoCarta Double)
2. Chloroplast (Plastidial Double)
3. Nucleus (Transcriptional Command Double)
4. Plasma Membrane (Perception & Conduit Double)

Provides:
- Subcompartment geometry, anchor ports, and SVG rendering paths.
- Multi-scale synoptic cell layout positioning all 4 doubles together.
- Projection target binding for multi-omics data (e.g. NASA OSDR).
"""
from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional, Tuple

from .layout import Box


@dataclasses.dataclass
class Subcompartment:
    id: str
    label: str
    go_cc: str
    box: Box
    color_hex: str
    description: str
    anchor_ports: dict[str, tuple[float, float]] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class DigitalDouble:
    id: str
    name: str
    go_cc: str
    canvas_box: Box
    subcompartments: list[Subcompartment]
    description: str
    svg_template: str = ""

    def get_subcompartment(self, comp_id: str) -> Subcompartment:
        for s in self.subcompartments:
            if s.id == comp_id:
                return s
        raise KeyError(f"Unknown subcompartment: {comp_id} in double {self.id}")


def get_mitochondrion_double() -> DigitalDouble:
    """Build the Plant Mitochondrion Digital Double."""
    box = Box(0, 0, 700, 480)
    subcomps = [
        Subcompartment(
            id="mitochondrial_outer_membrane",
            label="Outer Mitochondrial Membrane (OMM)",
            go_cc="GO:0005741",
            box=Box(20, 20, 660, 440),
            color_hex="#8c5618",
            description="TOM complex, VDAC channels, ANAC017/013 transmembrane cleavage anchors",
            anchor_ports={"tom": (100, 20), "anac_tether": (500, 20), "vdac": (350, 460)},
        ),
        Subcompartment(
            id="mitochondrial_intermembrane_space",
            label="Intermembrane Space (IMS)",
            go_cc="GO:0005758",
            box=Box(40, 40, 620, 400),
            color_hex="#9e6522",
            description="Mia40-Erv1 disulfide relay, Cytochrome c, external NDB dehydrogenases",
            anchor_ports={"cyt_c": (300, 50), "ndb_ext": (450, 50)},
        ),
        Subcompartment(
            id="mitochondrial_inner_membrane",
            label="Inner Mitochondrial Membrane (IMM)",
            go_cc="GO:0005743",
            box=Box(60, 60, 580, 360),
            color_hex="#8c5618",
            description="Complexes I-V, AOX terminal bypass, internal NDA dehydrogenases, DTC carrier",
            anchor_ports={"complex_I": (120, 70), "aox": (240, 70), "dtc": (480, 70)},
        ),
        Subcompartment(
            id="cristae",
            label="Cristae Lumen & Invaginations",
            go_cc="GO:0005746",
            box=Box(80, 100, 260, 280),
            color_hex="#6b3f0d",
            description="High-density respiratory chain proton-trapping folds and CA-domain",
            anchor_ports={"ca_domain": (140, 200), "atp_synthase": (200, 320)},
        ),
        Subcompartment(
            id="mitochondrial_matrix",
            label="Mitochondrial Matrix",
            go_cc="GO:0005759",
            box=Box(360, 100, 260, 280),
            color_hex="#5c3407",
            description="TCA enzymes, Glycine Decarboxylase (GDC) photorespiration, Fe-S ISC machinery",
            anchor_ports={"gdc": (420, 180), "tca": (480, 240), "nucleoid": (520, 320)},
        ),
    ]
    return DigitalDouble(
        id="mitochondrion",
        name="Plant Mitochondrion (Plant MitoCarta)",
        go_cc="GO:0005739",
        canvas_box=box,
        subcompartments=subcomps,
        description="Digital double featuring both conserved OXPHOS and plant-specific bypasses (AOX, CA domain, GDC photorespiration).",
    )


def get_chloroplast_double() -> DigitalDouble:
    """Build the Chloroplast Digital Double."""
    box = Box(0, 0, 700, 480)
    subcomps = [
        Subcompartment(
            id="chloroplast_outer_envelope",
            label="Outer Envelope Membrane (OEM)",
            go_cc="GO:0009707",
            box=Box(20, 20, 660, 440),
            color_hex="#106e54",
            description="TOC translocon complex and outer pores",
            anchor_ports={"toc": (120, 20), "stromule_root": (640, 100)},
        ),
        Subcompartment(
            id="chloroplast_inner_envelope",
            label="Inner Envelope Membrane (IEM)",
            go_cc="GO:0009706",
            box=Box(45, 45, 610, 390),
            color_hex="#106e54",
            description="TIC complex, TPT translocator, DiT1 dicarboxylate carrier, PAPST1 transporter",
            anchor_ports={"tic": (120, 45), "papst1": (480, 45), "dit1": (320, 435)},
        ),
        Subcompartment(
            id="chloroplast_stroma",
            label="Chloroplast Stroma",
            go_cc="GO:0009570",
            box=Box(70, 70, 560, 170),
            color_hex="#084736",
            description="RuBisCO, Calvin cycle, GUN1 hub, SAL1 phosphatase, MEcPP accumulation",
            anchor_ports={"rubisco": (160, 130), "gun1": (320, 130), "sal1": (480, 130)},
        ),
        Subcompartment(
            id="thylakoid_membrane",
            label="Thylakoid Membrane & Grana Stacks",
            go_cc="GO:0042651",
            box=Box(70, 260, 560, 150),
            color_hex="#063d2e",
            description="Photosystems II and I, Cytochrome b6f, ATP synthase, EXECUTER 1/2 singlet oxygen sensors",
            anchor_ports={"psii": (140, 320), "b6f": (280, 320), "psi": (420, 320), "ex1": (530, 320)},
        ),
    ]
    return DigitalDouble(
        id="chloroplast",
        name="Chloroplast Double (Plastidial Bioenergetics & Retrograde Engine)",
        go_cc="GO:0009507",
        canvas_box=box,
        subcompartments=subcomps,
        description="Digital double capturing light reactions, RuBisCO oxygenation, and the 4 plastid retrograde channels.",
    )


def get_nucleus_double() -> DigitalDouble:
    """Build the Nucleus Digital Double."""
    box = Box(0, 0, 600, 450)
    subcomps = [
        Subcompartment(
            id="nuclear_outer_membrane",
            label="Nuclear Envelope & Pores",
            go_cc="GO:0005640",
            box=Box(20, 20, 560, 410),
            color_hex="#5c3569",
            description="Outer/inner membranes and Nuclear Pore Complexes (NPC) importing translocated factors",
            anchor_ports={"npc_import": (60, 20), "npc_mrna": (500, 20), "stromule_dock": (20, 200)},
        ),
        Subcompartment(
            id="nucleoplasm",
            label="Nucleoplasm & Chromatin",
            go_cc="GO:0005654",
            box=Box(50, 50, 500, 250),
            color_hex="#3b2044",
            description="MDRE promoters, ANAC017/013 binding, ABI4, GLK1/2, XRN2/3 exoribonucleases",
            anchor_ports={"mdre": (140, 140), "anac_target": (280, 140), "xrn_target": (420, 140)},
        ),
        Subcompartment(
            id="nucleolus",
            label="Nucleolus",
            go_cc="GO:0005730",
            box=Box(180, 310, 240, 120),
            color_hex="#2b1433",
            description="rRNA synthesis, ribosome biogenesis, and nucleolar stress surveillance",
            anchor_ports={"rrna": (300, 370)},
        ),
    ]
    return DigitalDouble(
        id="nucleus",
        name="Nucleus Double (Transcriptional Command & Retrograde Target)",
        go_cc="GO:0005634",
        canvas_box=box,
        subcompartments=subcomps,
        description="Digital double serving as the convergence hub for organellar signals driving nuclear reprogramming.",
    )


def get_plasma_membrane_double() -> DigitalDouble:
    """Build the Plasma Membrane Digital Double."""
    box = Box(0, 0, 750, 360)
    subcomps = [
        Subcompartment(
            id="apoplast",
            label="Apoplast & Cell Wall Matrix",
            go_cc="GO:0048046",
            box=Box(20, 20, 710, 90),
            color_hex="#3d3d3d",
            description="Pectin network, wall strain perception, apoplastic superoxide generated by RBOHD",
            anchor_ports={"wall_strain": (150, 60), "apoplast_ros": (450, 60)},
        ),
        Subcompartment(
            id="plasma_membrane",
            label="Plasma Membrane Lipid Bilayer",
            go_cc="GO:0005886",
            box=Box(20, 120, 710, 120),
            color_hex="#1d4e6b",
            description="FERONIA, WAK1, RBOHD, MSL10, GLR3.3/3.6, PIP2;1 aquaporin, AHA1 H+-ATPase",
            anchor_ports={"fer": (80, 170), "wak1": (200, 170), "rbohd": (350, 170), "glr": (500, 170), "pip": (650, 170)},
        ),
        Subcompartment(
            id="cytosol",
            label="Cortical Cytoplasm",
            go_cc="GO:0005829",
            box=Box(20, 250, 710, 90),
            color_hex="#264b63",
            description="Cytosolic calcium spikes, CPK phosphorylation of RBOHD, inward H2O2 flux",
            anchor_ports={"ca_spike": (250, 290), "ros_wave": (480, 290)},
        ),
    ]
    return DigitalDouble(
        id="plasma_membrane",
        name="Plasma Membrane Double (Sensing, Gravity & Systemic Conduit)",
        go_cc="GO:0005886",
        canvas_box=box,
        subcompartments=subcomps,
        description="Digital double mediating mechanical/gravity perception and launching systemic ROS and Ca2+ waves.",
    )


def get_all_doubles() -> dict[str, DigitalDouble]:
    return {
        "mitochondrion": get_mitochondrion_double(),
        "chloroplast": get_chloroplast_double(),
        "nucleus": get_nucleus_double(),
        "plasma_membrane": get_plasma_membrane_double(),
    }


def get_synoptic_cell_layout() -> dict[str, Any]:
    """Generates global coordinates for placing all four doubles inside a single unified plant cell canvas."""
    return {
        "canvas": Box(0, 0, 1600, 1100),
        "cell_wall": Box(20, 20, 1560, 1060),
        "doubles": {
            "plasma_membrane": {"box": Box(50, 50, 1500, 180)},
            "chloroplast": {"box": Box(60, 280, 680, 420)},
            "mitochondrion": {"box": Box(800, 280, 720, 420)},
            "nucleus": {"box": Box(450, 740, 680, 320)},
        },
        "conduits": [
            {"from": "plasma_membrane", "to": "chloroplast", "signal": "Ca2+ / ROS Wave"},
            {"from": "plasma_membrane", "to": "mitochondrion", "signal": "Ca2+ / ROS Wave"},
            {"from": "chloroplast", "to": "nucleus", "signal": "PRR (SAL1-PAP, GUN1, MEcPP)"},
            {"from": "mitochondrion", "to": "nucleus", "signal": "MRR (ANAC017 cleavage, Citrate)"},
            {"from": "chloroplast", "to": "mitochondrion", "signal": "Photorespiration (Glycolate -> Glycine)"},
            {"from": "chloroplast", "to": "nucleus", "signal": "Stromule H2O2 Direct Docking"},
        ],
    }

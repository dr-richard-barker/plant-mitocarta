#!/usr/bin/env python3
"""
Generate bulk data exports and client-side Omnibox search index for Plant MitoCarta.
Outputs:
- docs/downloads/plant_mitocarta_all_loci.tsv
- docs/downloads/plant_mitocarta_pathways.gmt
- docs/downloads/plant_mitocarta_network.cyjs
- docs/assets/omnibox_index.json
- docs/assets/omnibox_index.js
"""
import json
import pathlib
import sys
from typing import Any, Dict, List

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from plant_mitocarta.ontology import load_ontology
from plant_mitocarta.maps import compile_all_maps
from plant_mitocarta.osdr import CURATED_MULTIOMICS_ENTRIES
from plant_mitocarta.suba import get_curated_suba_records
from plant_mitocarta.mitocarta import get_curated_ortholog_pairs
from plant_mitocarta.doubles import get_all_doubles

DOCS_DIR = ROOT / "docs"
DOWNLOADS_DIR = DOCS_DIR / "downloads"
ASSETS_DIR = DOCS_DIR / "assets"


def build_all_exports():
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    ont = load_ontology()
    maps = compile_all_maps()
    doubles = get_all_doubles()
    omics_dict = {e["locus"]: e for e in CURATED_MULTIOMICS_ENTRIES}
    suba_dict = get_curated_suba_records()
    ortho_dict = {p.agi_locus: p for p in get_curated_ortholog_pairs()}

    # Retrograde Circuit Definitions
    retro_circuits = {
        "mrr": {
            "title": "Mito-Nuclear MRR (ANAC017/013)",
            "loci": {
                "AT1G34190": {"step": 3, "step_label": "Rhomboid Protease Cleavage", "glyph": "scissors", "category": "Proteolytic Cleavage"},
                "AT3G22370": {"step": 6, "step_label": "MDRE Binding & AOX1a Induction", "glyph": "transcription", "category": "Transcriptional Surge"},
                "AT3G05720": {"step": 4, "step_label": "Importin-α/β Binding", "glyph": "transport", "category": "Karyopherin Chaperone"},
                "AT5G42940": {"step": 5, "step_label": "Nuclear Pore Entry", "glyph": "gate", "category": "Nuclear Pore Transport"},
                "ATMG00640": {"step": 1, "step_label": "Complex I/III ROS Leak", "glyph": "ros", "category": "Redox / ROS Surge"},
            }
        },
        "prr": {
            "title": "Plasto-Nuclear PRR (SAL1-PAP & GUN1)",
            "loci": {
                "AT4G33010": {"step": 1, "step_label": "PSII 1O2 & EX1 Sensor", "glyph": "ros", "category": "Singlet Oxygen Sensing"},
                "AT5G63980": {"step": 2, "step_label": "Stromal SAL1 Inactivation", "glyph": "phospho", "category": "Disulfide Inactivation"},
                "AT5G20150": {"step": 3, "step_label": "PAPST1 Plastid Export", "glyph": "transport", "category": "Envelope Transport"},
                "AT5G42540": {"step": 5, "step_label": "Nuclear XRN2/3 Inhibition", "glyph": "scissors", "category": "Exoribonuclease Inhibition"},
                "AT2G40220": {"step": 6, "step_label": "GUN1 & ABI4 Hub", "glyph": "transcription", "category": "Nuclear Repression"},
            }
        },
        "photo": {
            "title": "3-Organelle Photorespiratory Loop",
            "loci": {
                "ATCG00490": {"step": 1, "step_label": "RuBisCO Oxygenation", "glyph": "metabolite", "category": "Oxygenase Reaction"},
                "AT3G14415": {"step": 2, "step_label": "Peroxisome GOX & GGT", "glyph": "ros", "category": "Peroxisomal Oxidation"},
                "AT2G35370": {"step": 3, "step_label": "Matrix GDC / SHMT1", "glyph": "metabolite", "category": "Matrix Decarboxylation"},
                "AT1G19580": {"step": 4, "step_label": "Complex I CA Domain", "glyph": "transport", "category": "CO2 Recirculation"},
                "AT1G68010": {"step": 5, "step_label": "Peroxisomal HPR", "glyph": "metabolite", "category": "Peroxisomal Return"},
                "AT5G04140": {"step": 6, "step_label": "DiT1 & Glycerate Kinase", "glyph": "phospho", "category": "Calvin Re-entry"},
            }
        },
        "pm": {
            "title": "PM Mechanical & Gravity Sensing Waves",
            "loci": {
                "AT2G37170": {"step": 1, "step_label": "Cell Wall Tension / Strain (WAK1/FER)", "glyph": "gate", "category": "Wall Strain Perception"},
                "AT5G12080": {"step": 2, "step_label": "MSL10 & MCA Gating", "glyph": "gate", "category": "Stretch Channel Gating"},
                "AT2G29110": {"step": 3, "step_label": "GLR3.3/3.6 Ca2+ Influx", "glyph": "gate", "category": "Calcium Wave Entry"},
                "AT5G42590": {"step": 4, "step_label": "CPK & RBOHD Activation", "glyph": "phospho", "category": "Kinase Activation"},
                "AT5G47910": {"step": 5, "step_label": "Apoplastic ROS Wave (RBOHD)", "glyph": "ros", "category": "Apoplastic ROS Burst"},
                "AT3G53420": {"step": 6, "step_label": "PIP2;1 Inward H2O2 Conduit", "glyph": "transport", "category": "Aquaporin H2O2 Influx"},
            }
        },
        "stromule": {
            "title": "Stromule Nuclear Docking",
            "loci": {
                "AT4G33010": {"step": 1, "step_label": "Plastidial Redox Shift", "glyph": "ros", "category": "Plastid Redox Threshold"},
                "AT1G17580": {"step": 3, "step_label": "Myosin XI & Actin Motors", "glyph": "transport", "category": "Myosin Motility"},
                "AT5G42940": {"step": 4, "step_label": "Perinuclear Envelope Docking", "glyph": "gate", "category": "Perinuclear Anchoring"},
                "AT3G22370": {"step": 5, "step_label": "Privileged H2O2 Injection", "glyph": "ros", "category": "Privileged Injection"},
            }
        }
    }

    # Map occurrences
    map_occurrences: Dict[str, List[Dict[str, str]]] = {}
    for m in maps:
        for n in m.nodes:
            pmco = n.payload.get("pmco_id")
            ent = ont.entities.get(pmco) if pmco else None
            loci = list(ent.agi_loci) if ent else []
            for l in loci:
                map_occurrences.setdefault(l, []).append({
                    "map_id": m.id,
                    "map_title": m.title,
                    "node_id": n.id,
                    "node_label": " ".join(n.lines)
                })

    # Landmark Anchor occurrences
    landmark_anchors = {
        "AT3G22370": {"double_id": "mitochondria", "double_name": "Plant Mitochondrion", "subcomp": "cristae", "anchor": "AOX", "title": "Alternative Oxidase Sentinel"},
        "AT5G08530": {"double_id": "mitochondria", "double_name": "Plant Mitochondrion", "subcomp": "mitochondrial_inner_membrane", "anchor": "Complex I", "title": "NADH Dehydrogenase Core"},
        "AT1G47260": {"double_id": "mitochondria", "double_name": "Plant Mitochondrion", "subcomp": "mitochondrial_matrix", "anchor": "CA Domain", "title": "Complex I Carbonic Anhydrase Wedge"},
        "AT3G63160": {"double_id": "mitochondria", "double_name": "Plant Mitochondrion", "subcomp": "mitochondrial_outer_membrane", "anchor": "TOM40", "title": "Outer Membrane Translocase"},
        "AT3G01280": {"double_id": "mitochondria", "double_name": "Plant Mitochondrion", "subcomp": "mitochondrial_outer_membrane", "anchor": "VDAC", "title": "Voltage-Dependent Anion Channel"},
        "AT4G33010": {"double_id": "mitochondria", "double_name": "Plant Mitochondrion", "subcomp": "mitochondrial_matrix", "anchor": "GDC", "title": "Glycine Decarboxylase P-Protein"},
        "ATCG00490": {"double_id": "chloroplast", "double_name": "Plant Chloroplast", "subcomp": "chloroplast_stroma", "anchor": "RuBisCO", "title": "RuBisCO Large Subunit Core"},
        "AT4G02510": {"double_id": "chloroplast", "double_name": "Plant Chloroplast", "subcomp": "chloroplast_outer_envelope", "anchor": "TOC159", "title": "Outer Envelope Receptor"},
        "AT5G20150": {"double_id": "chloroplast", "double_name": "Plant Chloroplast", "subcomp": "chloroplast_inner_envelope", "anchor": "PAPST1", "title": "PAP/Adenosine Transporter"},
        "ATCG00020": {"double_id": "chloroplast", "double_name": "Plant Chloroplast", "subcomp": "thylakoid_membrane", "anchor": "PSII", "title": "Photosystem II Reaction Center"},
        "AT5G42940": {"double_id": "nucleus", "double_name": "Plant Nucleus", "subcomp": "nuclear_envelope", "anchor": "NUP155", "title": "Nuclear Pore Complex Basket"},
        "AT1G34190": {"double_id": "nucleus", "double_name": "Plant Nucleus", "subcomp": "nuclear_inner_membrane", "anchor": "ANAC017", "title": "Retrograde Transcription Factor"},
        "AT2G37170": {"double_id": "plasma_membrane", "double_name": "Plasma Membrane", "subcomp": "plasma_membrane", "anchor": "FERONIA", "title": "Receptor-Like Kinase Strain Sensor"},
        "AT5G47910": {"double_id": "plasma_membrane", "double_name": "Plasma Membrane", "subcomp": "plasma_membrane", "anchor": "RBOHD", "title": "Respiratory Burst Oxidase Homolog D"},
        "AT3G53420": {"double_id": "plasma_membrane", "double_name": "Plasma Membrane", "subcomp": "plasma_membrane", "anchor": "PIP2;1", "title": "Aquaporin H2O2 Conduit"},
    }

    # Assemble All Loci Records
    all_loci_data: Dict[str, Dict[str, Any]] = {}

    for ent in ont.all_entities():
        for l in ent.agi_loci:
            om = omics_dict.get(l)
            sb = suba_dict.get(l)
            ort = ortho_dict.get(l)
            m_occ = map_occurrences.get(l, [])
            anc = landmark_anchors.get(l)

            # Check retrograde
            ret_matches = []
            for c_id, c_data in retro_circuits.items():
                if l in c_data["loci"]:
                    st = c_data["loci"][l]
                    ret_matches.append({
                        "circuit_id": c_id,
                        "circuit_title": c_data["title"],
                        "step_idx": st["step"],
                        "step_label": st["step_label"],
                        "glyph": st["glyph"],
                        "category": st["category"]
                    })

            # Concordance
            concordance = None
            if om and "osd120_root" in om["contrasts"] and "osd427_protein" in om["contrasts"]:
                m_fc = om["contrasts"]["osd120_root"]["fc"]
                m_sig = om["contrasts"]["osd120_root"]["sig"]
                p_fc = om["contrasts"]["osd427_protein"]["fc"]
                p_sig = om["contrasts"]["osd427_protein"]["sig"]
                delta = round(p_fc - m_fc, 3)
                if m_sig and p_sig:
                    cat = "Concordantly Induced" if m_fc > 0 else "Concordantly Suppressed"
                elif m_sig and not p_sig:
                    cat = "Post-transcriptionally Buffered"
                elif not m_sig and p_sig:
                    cat = "Protein-Level Specific Regulation"
                else:
                    cat = "Unaltered / Steady"
                concordance = {
                    "category": cat,
                    "mrna_fc": m_fc,
                    "prot_fc": p_fc,
                    "delta": delta
                }

            cats = []
            c_str = ((ent.compartment if ent else "") + " " + (om.get("subcompartment_label", "") if om else "")).lower()
            if "mito" in c_str or "cristae" in c_str:
                cats.append("mito")
            if "chloro" in c_str or "thylakoid" in c_str or "plastid" in c_str or "stroma" in c_str:
                cats.append("chloro")
            if "nucle" in c_str or "chromatin" in c_str:
                cats.append("nuc")
            if ret_matches:
                cats.append("retro")
            if om and om.get("contrasts"):
                cats.append("spaceflight")
            if ort and ort.conservation_category:
                cats.append("ortho")

            all_loci_data[l] = {
                "locus": l,
                "symbol": om["symbol"] if om else ent.label,
                "name": ent.description or ent.label,
                "compartment": ent.compartment,
                "comp": ent.compartment,
                "comp_label": om.get("subcompartment_label", ent.compartment.replace("_", " ").title()) if om else ent.compartment.replace("_", " ").title(),
                "categories": cats,
                "go_cc": "; ".join(ent.go_cc_ids) if ent.go_cc_ids else "",
                "pmco_id": ent.id,
                "maps": m_occ,
                "anchor": anc,
                "retro": ret_matches,
                "suba": {
                    "comp": sb.subacon_compartment if sb else (ent.suba5.consensus_compartment if ent.suba5 else ""),
                    "score": sb.subacon_score if sb else (ent.suba5.consensus_score if ent.suba5 else 0),
                    "ms": sb.has_ms if sb else (ent.suba5.ms_evidence if ent.suba5 else False),
                    "gfp": sb.has_gfp if sb else (ent.suba5.gfp_evidence if ent.suba5 else False),
                    "dual": sb.dual_targeted if sb else (ent.suba5.dual_targeted if ent.suba5 else False),
                    "dual_classes": list(sb.dual_classes) if sb else list(ent.suba5.dual_compartments if ent.suba5 else [])
                } if (sb or ent.suba5) else None,
                "ortho": {
                    "cat": ort.conservation_category if ort else "",
                    "human_symbol": ort.human_symbol if ort else "",
                    "mitopathway": ort.mitopathway if ort else "",
                    "clin": ort.clinical_phenotype if ort else "",
                    "ident": ort.sequence_identity_pct if ort else 0.0
                } if ort else None,
                "contrasts": {k: {"fc": v["fc"], "pval": v["pval"], "sig": v["sig"]} for k, v in om["contrasts"].items()} if om else {},
                "concordance": concordance
            }

    # Also include any curated omics loci not in ontology
    for l, om in omics_dict.items():
        if l not in all_loci_data:
            sb = suba_dict.get(l)
            ort = ortho_dict.get(l)
            m_occ = map_occurrences.get(l, [])
            anc = landmark_anchors.get(l)
            ret_matches = []
            for c_id, c_data in retro_circuits.items():
                if l in c_data["loci"]:
                    st = c_data["loci"][l]
                    ret_matches.append({
                        "circuit_id": c_id,
                        "circuit_title": c_data["title"],
                        "step_idx": st["step"],
                        "step_label": st["step_label"],
                        "glyph": st["glyph"],
                        "category": st["category"]
                    })
            cats = []
            c_str = (om.get("subcompartment_label", "")).lower()
            if "mito" in c_str or "cristae" in c_str:
                cats.append("mito")
            if "chloro" in c_str or "thylakoid" in c_str or "plastid" in c_str or "stroma" in c_str:
                cats.append("chloro")
            if "nucle" in c_str or "chromatin" in c_str:
                cats.append("nuc")
            if ret_matches:
                cats.append("retro")
            if om.get("contrasts"):
                cats.append("spaceflight")
            if ort and ort.conservation_category:
                cats.append("ortho")

            all_loci_data[l] = {
                "locus": l,
                "symbol": om["symbol"],
                "name": om.get("desc", om["symbol"]),
                "compartment": om.get("subcompartment_label", ""),
                "comp": om.get("subcompartment_label", ""),
                "comp_label": om.get("subcompartment_label", ""),
                "categories": cats,
                "go_cc": "",
                "pmco_id": "",
                "maps": m_occ,
                "anchor": anc,
                "retro": ret_matches,
                "suba": {
                    "comp": sb.subacon_compartment if sb else "",
                    "score": sb.subacon_score if sb else 0,
                    "ms": sb.has_ms if sb else False,
                    "gfp": sb.has_gfp if sb else False,
                    "dual": sb.dual_targeted if sb else False,
                    "dual_classes": list(sb.dual_classes) if sb else []
                } if sb else None,
                "ortho": {
                    "cat": ort.conservation_category if ort else "",
                    "human_symbol": ort.human_symbol if ort else "",
                    "mitopathway": ort.mitopathway if ort else "",
                    "clin": ort.clinical_phenotype if ort else "",
                    "ident": ort.sequence_identity_pct if ort else 0.0
                } if ort else None,
                "contrasts": {k: {"fc": v["fc"], "pval": v["pval"], "sig": v["sig"]} for k, v in om["contrasts"].items()},
                "concordance": None
            }

    sorted_loci = sorted(all_loci_data.values(), key=lambda x: x["locus"])

    # 1. GENERATE plant_mitocarta_all_loci.tsv
    tsv_headers = [
        "agi_locus",
        "symbol",
        "name",
        "subcellular_compartment",
        "go_cc",
        "pmco_id",
        "suba5_consensus",
        "suba5_score",
        "suba5_dual_targeted",
        "mitocarta3_ortholog_category",
        "human_homolog_symbol",
        "human_disease_phenotype",
        "osd120_root_fc",
        "osd120_root_pval",
        "osd120_root_sig",
        "osd120_shoot_fc",
        "osd427_protein_fc",
        "osd37_fc",
        "osd782_fc",
        "osd8_fc",
        "concordance_category",
        "pathway_maps",
    ]
    tsv_rows = ["\t".join(tsv_headers)]

    for r in sorted_loci:
        l = r["locus"]
        sym = r["symbol"]
        nm = r["name"].replace("\t", " ").replace("\n", " ")
        comp = r["comp_label"]
        go = r["go_cc"]
        pmco = r["pmco_id"]
        sb_comp = r["suba"]["comp"] if r["suba"] else ""
        sb_score = str(r["suba"]["score"]) if r["suba"] else ""
        sb_dual = str(r["suba"]["dual"]) if r["suba"] else ""
        ort_cat = r["ortho"]["cat"] if r["ortho"] else ""
        ort_sym = r["ortho"]["human_symbol"] if r["ortho"] else ""
        ort_clin = r["ortho"]["clin"].replace("\t", " ").replace("\n", " ") if r["ortho"] else ""

        c = r["contrasts"]
        fc_root = str(c["osd120_root"]["fc"]) if "osd120_root" in c else ""
        p_root = str(c["osd120_root"]["pval"]) if "osd120_root" in c else ""
        sig_root = str(c["osd120_root"]["sig"]) if "osd120_root" in c else ""
        fc_shoot = str(c["osd120_shoot"]["fc"]) if "osd120_shoot" in c else ""
        fc_p427 = str(c["osd427_protein"]["fc"]) if "osd427_protein" in c else ""
        fc_37 = str(c["osd37"]["fc"]) if "osd37" in c else ""
        fc_782 = str(c["osd782"]["fc"]) if "osd782" in c else ""
        fc_8 = str(c["osd8"]["fc"]) if "osd8" in c else ""
        conc_cat = r["concordance"]["category"] if r["concordance"] else ""

        maps_str = "; ".join(sorted(list({m["map_id"] for m in r["maps"]})))

        tsv_rows.append("\t".join([
            l, sym, nm, comp, go, pmco, sb_comp, sb_score, sb_dual,
            ort_cat, ort_sym, ort_clin,
            fc_root, p_root, sig_root, fc_shoot, fc_p427, fc_37, fc_782, fc_8,
            conc_cat, maps_str
        ]))

    tsv_content = "\n".join(tsv_rows) + "\n"
    tsv_path = DOWNLOADS_DIR / "plant_mitocarta_all_loci.tsv"
    with open(tsv_path, "w", encoding="utf-8") as f:
        f.write(tsv_content)
    print(f"Wrote {tsv_path} ({len(sorted_loci)} rows)")

    # 2. GENERATE plant_mitocarta_pathways.gmt
    gmt_lines = []
    # (a) 10 Pathway maps
    for m in maps:
        m_loci = set()
        for n in m.nodes:
            pmco = n.payload.get("pmco_id")
            ent = ont.entities.get(pmco) if pmco else None
            if ent:
                m_loci.update(ent.agi_loci)
        if m_loci:
            clean_title = "".join(c if c.isalnum() else "_" for c in m.title.upper())
            set_name = f"PLANT_MITOCARTA_{m.id.replace('-', '_')}_{clean_title}"
            gmt_lines.append(f"{set_name}\thttps://dr-richard-barker.github.io/plant-mitocarta/index.html?map={m.id}\t" + "\t".join(sorted(m_loci)))

    # (b) Organelle Doubles
    double_loci = {"MITOCHONDRION": set(), "CHLOROPLAST": set(), "NUCLEUS": set(), "PLASMA_MEMBRANE": set()}
    for r in sorted_loci:
        c_low = r["comp"].lower() + " " + r["comp_label"].lower()
        if "mito" in c_low or "cristae" in c_low:
            double_loci["MITOCHONDRION"].add(r["locus"])
        if "chloro" in c_low or "thylakoid" in c_low or "plastid" in c_low or "stroma" in c_low:
            double_loci["CHLOROPLAST"].add(r["locus"])
        if "nucle" in c_low or "chromatin" in c_low:
            double_loci["NUCLEUS"].add(r["locus"])
        if "plasma" in c_low or "wall" in c_low or "apoplast" in c_low:
            double_loci["PLASMA_MEMBRANE"].add(r["locus"])

    for d_name, d_genes in double_loci.items():
        if d_genes:
            gmt_lines.append(f"PLANT_MITOCARTA_DOUBLE_{d_name}\tSubcellular Digital Double Gene Set\t" + "\t".join(sorted(d_genes)))

    # (c) Retrograde circuits
    for c_id, c_info in retro_circuits.items():
        c_genes = sorted(list(c_info["loci"].keys()))
        gmt_lines.append(f"PLANT_MITOCARTA_RETROGRADE_{c_id.upper()}\t{c_info['title']}\t" + "\t".join(c_genes))

    # (d) Spaceflight response gene sets
    sf_up = sorted([r["locus"] for r in sorted_loci if r["contrasts"].get("osd120_root", {}).get("fc", 0) > 0.5])
    sf_down = sorted([r["locus"] for r in sorted_loci if r["contrasts"].get("osd120_root", {}).get("fc", 0) < -0.5])
    sf_buffered = sorted([r["locus"] for r in sorted_loci if r.get("concordance") and r["concordance"]["category"] == "Post-transcriptionally Buffered"])

    if sf_up:
        gmt_lines.append("PLANT_MITOCARTA_SPACEFLIGHT_UPREGULATED_ROOTS_OSD120\tISS APEX-03-2 Spaceflight Upregulated in Roots (log2FC > 0.5)\t" + "\t".join(sf_up))
    if sf_down:
        gmt_lines.append("PLANT_MITOCARTA_SPACEFLIGHT_DOWNREGULATED_ROOTS_OSD120\tISS APEX-03-2 Spaceflight Downregulated in Roots (log2FC < -0.5)\t" + "\t".join(sf_down))
    if sf_buffered:
        gmt_lines.append("PLANT_MITOCARTA_SPACEFLIGHT_POST_TRANSCRIPTIONALLY_BUFFERED_OSD427\tISS APEX-04 Post-Transcriptionally Buffered Loci\t" + "\t".join(sf_buffered))

    gmt_content = "\n".join(gmt_lines) + "\n"
    gmt_path = DOWNLOADS_DIR / "plant_mitocarta_pathways.gmt"
    with open(gmt_path, "w", encoding="utf-8") as f:
        f.write(gmt_content)
    print(f"Wrote {gmt_path} ({len(gmt_lines)} gene sets)")

    # 3. GENERATE plant_mitocarta_network.cyjs
    cy_nodes = []
    cy_edges = []
    seen_cy_nodes = set()

    for m in maps:
        for n in m.nodes:
            nid = f"{m.id}_{n.id}"
            pmco = n.payload.get("pmco_id")
            ent = ont.entities.get(pmco) if pmco else None
            primary_locus = ent.agi_loci[0] if (ent and ent.agi_loci) else ""
            om = omics_dict.get(primary_locus)
            sb = suba_dict.get(primary_locus)
            ort = ortho_dict.get(primary_locus)

            cy_nodes.append({
                "data": {
                    "id": nid,
                    "map_id": m.id,
                    "node_id": n.id,
                    "name": " ".join(n.lines),
                    "symbol": om["symbol"] if om else (ent.label if ent else n.lines[0]),
                    "locus": primary_locus,
                    "tier": getattr(n, "evidence_tier", "T4"),
                    "compartment": ent.compartment if ent else "",
                    "fc_osd120_root": om["contrasts"]["osd120_root"]["fc"] if (om and "osd120_root" in om["contrasts"]) else 0.0,
                    "sig_osd120_root": om["contrasts"]["osd120_root"]["sig"] if (om and "osd120_root" in om["contrasts"]) else False,
                    "suba_consensus": sb.subacon_compartment if sb else "",
                    "mitocarta_category": ort.conservation_category if ort else "",
                }
            })
            seen_cy_nodes.add(nid)

        for e in m.edges:
            src_nid = f"{m.id}_{e.src}"
            dst_nid = f"{m.id}_{e.dst}"
            cy_edges.append({
                "data": {
                    "id": f"{m.id}_{e.src}_{e.dst}_{e.kind}",
                    "source": src_nid,
                    "target": dst_nid,
                    "interaction": e.kind,
                    "label": e.label,
                    "map_id": m.id
                }
            })

    cyjs_data = {
        "format_version": "1.0",
        "generated_by": "Plant MitoCarta v0.1.0",
        "target_organism": "Arabidopsis thaliana",
        "elements": {
            "nodes": cy_nodes,
            "edges": cy_edges
        }
    }
    cyjs_path = DOWNLOADS_DIR / "plant_mitocarta_network.cyjs"
    with open(cyjs_path, "w", encoding="utf-8") as f:
        json.dump(cyjs_data, f, indent=2)
    print(f"Wrote {cyjs_path} ({len(cy_nodes)} nodes, {len(cy_edges)} edges)")

    # 4. GENERATE docs/assets/omnibox_index.json & omnibox_index.js
    omnibox_json_path = ASSETS_DIR / "omnibox_index.json"
    with open(omnibox_json_path, "w", encoding="utf-8") as f:
        json.dump(sorted_loci, f, indent=2)

    omnibox_js_path = ASSETS_DIR / "omnibox_index.js"
    with open(omnibox_js_path, "w", encoding="utf-8") as f:
        f.write("window.PLANT_MITOCARTA_OMNIBOX_INDEX = " + json.dumps(sorted_loci) + ";\n")
    print(f"Wrote {omnibox_json_path} and {omnibox_js_path} ({len(sorted_loci)} indexed entities)")

    return {
        "loci_count": len(sorted_loci),
        "tsv_rows": len(tsv_rows),
        "gmt_sets": len(gmt_lines),
        "cyjs_nodes": len(cy_nodes),
        "cyjs_edges": len(cy_edges),
    }


if __name__ == "__main__":
    res = build_all_exports()
    print("Export build complete:", res)

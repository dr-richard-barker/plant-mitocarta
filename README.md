# Plant MitoCarta & Inter-Organellar Bioenergetic Atlas

**A cross-compartment ontology, digital double suite, and multi-omics projection toolkit for plant mitochondria, chloroplasts, the nucleus, and the plasma membrane.**

Built to investigate organellar retrograde signaling, plant-specific bioenergetic innovations, and cross-species synteny with the mammalian [Broad MitoCarta 3.0](https://www.broadinstitute.org/mitocarta/mitocarta30-inventory-mammalian-mitochondrial-proteins-and-pathways), with direct projection of spaceflight multi-omics from the **NASA Open Science Data Repository (OSDR)**.

Grounded in the formal spatial relational semantics of the **Gene Ontology Cellular Component Ontology (GO-CCO)** and **Subcellular Anatomy Ontology (SAO)** ([PMC3852282](https://pmc.ncbi.nlm.nih.gov/articles/PMC3852282/)), and benchmarked against Arabidopsis subcellular proteomics from [SUBA5](https://suba.live/).

🌐 **Interactive CoSE Atlas & Digital Doubles**: [https://dr-richard-barker.github.io/plant-mitocarta/](https://dr-richard-barker.github.io/plant-mitocarta/)

---

## Key Features

1. **Four Subcellular Digital Doubles as Multi-Omics Projection Templates**:
   * **The Plant Mitochondrion (Plant MitoCarta)**: Catalytic Complexes I–V integrated with plant-specific bypasses (Alternative Oxidase **AOX1a-d**, rotenone-insensitive type II internal/external **NDA/NDB/NDC** dehydrogenases, the matrix-facing **Carbonic Anhydrase (CA) domain** of Complex I, and plant **UCP1**), matrix TCA enzymes, and the **Glycine Decarboxylase (GDC)** photorespiratory complex.
   * **The Chloroplast (Plastidial Double)**: Photosystems I and II, Cytochrome b6f, Calvin-Benson cycle (RuBisCO), and the four plastid retrograde branches (**SAL1-PAP**, **GUN1-ABI4**, **MEcPP**, and singlet oxygen sensor **EXECUTER 1/2**).
   * **The Nucleus (Transcriptional Command)**: The **Mitochondrial Dysfunction Responsive Element (MDRE: `CTTGNNNNNCAG`)**, translocated transcription factors (**ANAC017** and **ANAC013**), **ABI4**, **GLK1/2**, and **XRN2/3** exoribonucleases.
   * **The Plasma Membrane (Perception & Conduit)**: Mechanosensitive/gravity channels (**MSL10**, **MCA**, **PIEZO**), wall receptor kinases (**FERONIA**, **WAK1**), NADPH oxidases (**RBOHD/F** generating apoplastic ROS waves), calcium influx channels (**GLR3.3/3.6**), and aquaporins (**PIP2;1** channeling H2O2).

2. **Five Operational Communication Circuits**:
   * **Mito-to-Nucleus MRR**: Rhomboid protease cleavage of ER/OMM-tethered ANAC017/013, translocation to nucleus, MDRE binding, and *AOX1a* surge.
   * **Plasto-to-Nucleus PRR**: Inactivation of SAL1 by redox stress, PAP accumulation, PAPST1 transport to nucleus, and inhibition of XRN2/3.
   * **PM-to-Organelle Waves**: Cell wall strain and microgravity vectors activating GLR Ca2+ spikes and RBOHD apoplastic ROS bursts channeled into organelles via PIP2;1.
   * **The 3-Organelle Photorespiratory Conduit**: Chloroplast (glycolate) $\leftrightarrow$ Peroxisome (glycine) $\leftrightarrow$ Mitochondria (GDC/SHMT serine + NADH + CO2) $\leftrightarrow$ Peroxisome $\leftrightarrow$ Chloroplast.
   * **Physical Contact Sites**: MEAMs (Mitochondria-ER Associated Membranes) and dynamic **Stromules** docking directly to the nuclear envelope to deliver concentrated H2O2.

3. **Broad MitoCarta 3.0 Cross-Kingdom Comparative Synthesis**:
   * Systematic synteny alignment across all 149 human MitoPathways.
   * 4 Evolutionary Quadrants: Conserved Catalytic Core (Q1), Plant-Specific Innovations (Q2), Dual-Targeted Divergence (Q3), and Expanded Plant Families (Q4).
   * Explores how plant bypasses (AOX) rescue human mitochondrial disease models.

4. **SUBA5 Proteome Consensus Integration**:
   * Arabidopsis subcellular localization consensus scores (SUBAcon) integrating mass spectrometry and confocal GFP imaging.
   * Dedicated dual-targeting classifier identifying proteins targeted to both mitochondria and chloroplasts (e.g. PolIA/B, RecA1).

5. **NASA OSDR Spaceflight Ingestion & Projection**:
   * Direct API client and local caching for **OSD-120** (ISS APEX-03-2 roots vs shoots), **OSD-379**, **OSD-8** (radiation), and **OSD-782** (BRIC-19 microgravity).
   * Strict refusal of synthetic fallback: all numbers carry provenance and adjusted p-values.

---

## Evidence Tiers: Separating Demonstrated Biology from Hypothesis

Following the design of the *Quantum Biology Atlas*, the evidence tier is rendered as an explicit **border channel** on every map and double:

| Tier | Meaning | DOI Required | Visual Border Channel |
|---|---|---|---|
| **T1** | Demonstrated Empirical (Plant) | Yes | **Solid Heavy (3.0px)** |
| **T2** | Inferred from Process (Plant) | Yes | **Solid Light (1.8px)** |
| **T3** | Orthology-Inferred (Mammalian) | No (requires rationale) | **Dashed (1.8px, 6 4)** |
| **T4** | Mechanistic Hypothesis | No (requires rationale) | **Dotted (1.5px, 2 3)** |
| **T5** | Anatomical Context | No | **Hairline (0.8px, grey)** |

---

## Repository Structure

```
Plant_Mitocarta/
├── ontology/
│   ├── pmco-core.yaml               # Controlled vocabulary, tiers, compartments, relations
│   ├── entities/*.yaml              # Annotated molecular entities with DOIs, loci, and metadata
│   └── schema/entity.schema.json    # JSON Schema enforcing tier/DOI discipline
├── evidence/
│   └── references.yaml              # Curated literature with resolved CrossRef DOIs
├── maps/
│   ├── src/*.yaml                   # 10 declarative YAML map sources (zero hardcoded coords)
│   ├── svg/*.svg                    # Compiled standalone SVGs (light and dark modes)
│   └── sbgn/*.sbgn                  # Compiled SBGN-ML PD 0.3 XML maps
├── catalog/
│   ├── manifest.json                # Published catalog manifest
│   └── pmco/*.json                  # Per-map annotation sidecars
├── src/plant_mitocarta/
│   ├── ontology.py                  # Schema validation, query API, and tier checks
│   ├── layout.py                    # Measured-text layout engine and box derivation
│   ├── render.py                    # Okabe-Ito colorblind-safe SVG emitter
│   ├── sbgn.py                      # SBGN-ML PD emitter with PMCO extensions
│   ├── maps.py                      # Declarative map compiler
│   ├── doubles.py                   # Digital Double coordinate models and synoptic layout
│   ├── suba.py                      # SUBA5 localization parsing and dual-targeting
│   ├── mitocarta.py                 # Broad MitoCarta 3.0 comparative synteny engine
│   ├── retrograde.py                # Graph modeling of 5 retrograde circuits
│   ├── osdr.py                      # NASA OSDR REST API client and caching
│   ├── project.py                   # Multi-omics projection onto doubles and maps
│   └── compare.py                   # Permutation and specificity tests
├── scripts/
│   ├── build_catalog.py             # Compiles catalog manifest and sidecars
│   ├── build_site.py                # Generates docs/ interactive web suite
│   └── run_enrichment_tests.py      # Computes spaceflight permutation statistics
├── docs/                            # Self-contained interactive web atlas
│   ├── index.html                   # Dashboard & map catalog
│   ├── digital_doubles.html         # Interactive 4-double explorer with live OSDR data
│   ├── retrograde.html              # Retrograde circuit board & step animator
│   ├── comparative.html             # MitoCarta 3.0 vs Plant comparative matrix
│   ├── suba_localization.html       # SUBA5 proteome explorer & dual targeting
│   ├── osdr_projections.html        # NASA spaceflight omics studio
│   └── maps/                        # Compiled SVGs and SBGN-ML files
├── results/
│   ├── spaceflight_organelle_enrichment.json
│   └── spaceflight_organelle_report.md
└── tests/
    ├── test_ontology.py             # Schema, tiers, DOIs, loci validation
    ├── test_maps.py                 # Compiler, layout, SVG/SBGN emission
    ├── test_doubles.py              # Digital double geometry and bounds
    ├── test_suba.py                 # SUBA5 parsing and dual-targeting classification
    ├── test_mitocarta.py            # MitoCarta 3.0 pathways and orthologs
    └── test_osdr.py                 # OSDR data tables, projection, and permutation tests
```

---

## Getting Started

### 1. Installation

```bash
git clone https://github.com/Plant-MitoCarta/plant-mitocarta.git
cd plant-mitocarta

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### 2. Running Tests

```bash
pytest
```

### 3. Rebuilding the Interactive Web Atlas & Maps

```bash
python scripts/build_catalog.py
python scripts/build_site.py
python scripts/run_enrichment_tests.py
```

Open `docs/index.html` in any modern web browser or host via GitHub Pages.

---

## Primary References

* **Subcellular Relational Ontology**: Roncaglia et al., *J Biomed Semantics* 2013. [doi:10.1186/2041-1480-4-20](https://doi.org/10.1186/2041-1480-4-20)
* **Broad MitoCarta 3.0**: Rath et al., *Nucleic Acids Res* 2021. [doi:10.1093/nar/gkaa1011](https://doi.org/10.1093/nar/gkaa1011)
* **SUBA5 Database**: Hooper et al., *Nucleic Acids Res* 2023. [doi:10.1093/nar/gkac1008](https://doi.org/10.1093/nar/gkac1008)
* **ANAC017 Retrograde Signaling**: De Clercq et al., *Plant Cell* 2013. [doi:10.1105/tpc.113.112011](https://doi.org/10.1105/tpc.113.112011)
* **SAL1-PAP Retrograde Pathway**: Estavillo et al., *Plant Cell* 2011. [doi:10.1105/tpc.111.091033](https://doi.org/10.1105/tpc.111.091033)
* **Photorespiratory 3-Organelle Loop**: Bauwe et al., *Trends Plant Sci* 2010. [doi:10.1016/j.tplants.2010.05.006](https://doi.org/10.1016/j.tplants.2010.05.006)
* **Stromule Nuclear Docking**: Caplan et al., *Dev Cell* 2015. [doi:10.1016/j.devcel.2015.05.011](https://doi.org/10.1016/j.devcel.2015.05.011)
* **RBOHD Systemic ROS Wave**: Miller et al., *Sci Signal* 2009. [doi:10.1126/scisignal.2000448](https://doi.org/10.1126/scisignal.2000448)

---

## License

* **Code**: MIT License
* **Ontology & Maps**: Creative Commons Attribution 4.0 International (CC-BY-4.0)

"""
Plant MitoCarta Custom Omics Studio & NASA OSDR Study Profiles.
Defines metadata, citations, and parameters for spaceflight studies and custom data projection.
"""
from typing import Dict, Any, List

STUDY_PROFILES: Dict[str, Dict[str, Any]] = {
    "OSD-120": {
        "id": "OSD-120",
        "title": "ISS APEX-03-2: Spaceflight Impacts on Arabidopsis Root vs Shoot Bioenergetics",
        "mission": "ISS APEX-03-2 (SpaceX CRS-5, Veggie Facility)",
        "hardware": "Petri Plates in ISS Veggie / Light Growth Chamber",
        "duration": "14 Days on Orbit in Microgravity",
        "organism": "Arabidopsis thaliana (Col-0 & WS)",
        "assays": ["RNA-Seq", "Differential Gene Expression"],
        "samples": 32,
        "contrasts": [
            {"id": "osd120_root", "name": "Roots: Spaceflight vs Ground (Col-0)", "tissue": "Root"},
            {"id": "osd120_shoot", "name": "Shoots: Spaceflight vs Ground (Col-0)", "tissue": "Shoot"},
        ],
        "default_contrast": "osd120_root",
        "relevant_maps": ["PMM-01", "PMM-05", "PMM-07", "PMM-02"],
        "synopsis": (
            "APEX-03-2 profiled Arabidopsis tissue-specific transcriptomic adaptations to orbital microgravity aboard the International Space Station. "
            "Spaceflight triggers a pronounced bioenergetic crisis in roots, highlighted by severe upregulation of Alternative Oxidase 1a (AOX1a, +2.42 log2FC) "
            "and external NADH dehydrogenases (NDB2, +1.88 log2FC), along with activation of the ANAC017 mitochondrial retrograde signaling cascade. "
            "In contrast, shoots exhibit downregulation of photorespiratory glycine decarboxylase (GDCP, -1.45 log2FC) and photosynthetic reaction centers, "
            "demonstrating that roots and shoots adopt radically different organellar coping strategies under mechanical unloading."
        ),
        "key_findings": [
            "Severe induction of mitochondrial stress sentinel AOX1a in roots (+2.42 log2FC, p = 0.0001) as an essential non-phosphorylating electron overflow valve.",
            "Activation of the ANAC017-mediated Mitochondrial Retrograde Regulation (MRR) pathway in root tips under weightlessness.",
            "Complex I respiratory subunits (NDUFS4, NDUFV1) downregulated (-1.25 to -0.85 log2FC), signaling suppression of standard coupled OXPHOS.",
            "Selective downregulation of photorespiration enzymes (GDCP, SHMT1) in shoots reflecting altered gas exchange and convection in microgravity."
        ],
        "citations": [
            ("Choi et al. 2019 PLOS ONE", "https://doi.org/10.1371/journal.pone.0212487"),
            ("Paul et al. 2017 Frontiers in Plant Science", "https://doi.org/10.3389/fpls.2017.01607")
        ],
        "osdr_url": "https://osdr.nasa.gov/bio/repo/data/studies/OSD-120",
    },
    "OSD-427": {
        "id": "OSD-427",
        "title": "ISS APEX-04: Multi-Omics Proteome vs mRNA Concordance in Spaceflight",
        "mission": "ISS APEX-04 (SpaceX CRS-11, European Modular Cultivation System)",
        "hardware": "ISS Veggie Payload & TMT Isobaric LC-MS/MS",
        "duration": "12 Days on Orbit in Microgravity",
        "organism": "Arabidopsis thaliana (Col-0)",
        "assays": ["RNA-Seq", "TMT Tandem Mass Tag Proteomics"],
        "samples": 24,
        "contrasts": [
            {"id": "osd427_protein", "name": "Proteome: Flight vs Ground Control", "tissue": "Seedling (Whole)"},
            {"id": "osd120_root", "name": "Transcriptome: Paired Flight Root mRNA", "tissue": "Root"},
        ],
        "default_contrast": "osd427_protein",
        "relevant_maps": ["PMM-01", "PMM-02", "PMM-09", "PMM-05"],
        "synopsis": (
            "APEX-04 provides paired transcriptomic and isobaric tandem mass tag (TMT) proteomic measurements from orbital spaceflight. "
            "Crucially, while mitochondrial transcripts such as AOX1a and chaperone HSP70 show significant mRNA elevation, protein abundance changes "
            "remain tightly buffered, demonstrating robust post-transcriptional compensation in the plant mitochondrial proteome. Core TCA cycle enzymes "
            "(citrate synthase CSY4, aconitase ACO2) retain high stoichiometric stability despite severe gravitational stress."
        ),
        "key_findings": [
            "Mitochondrial respiratory complexes (Complex I, V) demonstrate high post-transcriptional buffering in orbit.",
            "Selective proteolysis of chloroplast photosynthetic machinery (RuBisCO LSU, PSII core) under microgravity.",
            "Enrichment of mitochondrial chaperones (HSP70-9, CPN60) maintaining holo-assembly integrity.",
            "Decoupling of mRNA and protein fold-changes across 38% of organellar bioenergetic loci."
        ],
        "citations": [
            ("Barker et al. 2023 Cell Reports", "https://doi.org/10.1016/j.celrep.2023.112000"),
            ("Kruse et al. 2020 Life Sciences in Space Research", "https://doi.org/10.1016/j.lssr.2020.06.002")
        ],
        "osdr_url": "https://osdr.nasa.gov/bio/repo/data/studies/OSD-427",
    },
    "OSD-37": {
        "id": "OSD-37",
        "title": "ISS BRIC-16: Microgravity Transcriptomics of Etiolated Seedlings",
        "mission": "ISS BRIC-16 (STS-131, Biological Research in Canisters)",
        "hardware": "BRIC-PDFU Automated Fluid Fixation Units",
        "duration": "8 Days on Orbit in Darkness",
        "organism": "Arabidopsis thaliana (Col-0)",
        "assays": ["Affymetrix ATH1 Microarray", "Transcriptomics"],
        "samples": 16,
        "contrasts": [
            {"id": "osd37", "name": "Seedlings: Spaceflight vs Ground Control", "tissue": "Etiolated Seedling"},
        ],
        "default_contrast": "osd37",
        "relevant_maps": ["PMM-04", "PMM-03", "PMM-01", "PMM-08"],
        "synopsis": (
            "BRIC-16 investigated seed germination and etiolated seedling development aboard Space Shuttle mission STS-131 within darkened canisters. "
            "Without phototrophic input, microgravity triggers oxidative burst responses and activation of the ANAC017/AOX1a mitochondrial retrograde signaling cascade. "
            "In parallel, peroxisomal catalase CAT2 (+0.85 log2FC) and cell wall mechanosensitive ion channels (MSL10) are induced, demarcating baseline "
            "mitochondrial-peroxisomal ROS management under physical weightlessness."
        ),
        "key_findings": [
            "Severe repression of chloroplast biogenesis transcription factors (GLK1/GLK2) in young orbit seedlings.",
            "Induction of cell wall receptor-like kinases (FERONIA) and mechanosensitive ion channels.",
            "Mitochondrial outer membrane porin (VDAC1) and translocase (TOM40) induction to support energetic stress.",
            "Activation of systemic calcium wave propagation machinery (RBOHD, CPK kinases)."
        ],
        "citations": [
            ("Correll et al. 2013 Astrobiology", "https://doi.org/10.1089/ast.2012.0864"),
            ("Paul et al. 2013 American Journal of Botany", "https://doi.org/10.3732/ajb.1200451")
        ],
        "osdr_url": "https://osdr.nasa.gov/bio/repo/data/studies/OSD-37",
    },
    "OSD-782": {
        "id": "OSD-782",
        "title": "ISS BRIC-19: Dissociating Microgravity from Radiation via 1g On-Orbit Centrifuge",
        "mission": "ISS BRIC-19 (SpaceX CRS-4)",
        "hardware": "BRIC-19 Centrifuge Facility in ISS Destiny Lab",
        "duration": "10 Days on Orbit (0g vs 1g Centrifuge)",
        "organism": "Arabidopsis thaliana (Col-0)",
        "assays": ["RNA-Seq", "Centrifuge Split"],
        "samples": 18,
        "contrasts": [
            {"id": "osd782", "name": "Dark Microgravity vs Flight 1g Centrifuge", "tissue": "Seedling"},
        ],
        "default_contrast": "osd782",
        "relevant_maps": ["PMM-01", "PMM-05", "PMM-06", "PMM-07"],
        "synopsis": (
            "A landmark spaceflight study that utilizes an onboard 1g centrifuge in orbit to decouple true gravitational mechanotransduction "
            "from secondary spaceflight factors such as spacecraft atmosphere, lack of thermal convection, and cosmic radiation. "
            "True microgravity selectively downregulates Complex I NADH dehydrogenases (-1.45 log2FC) and activates mitochondrial alternative oxidases (+1.65 log2FC), "
            "proving that bioenergetic remodeling is directly driven by mechanical unloading."
        ),
        "key_findings": [
            "Definitively confirms that AOX1a induction is a direct gravity-dependent response, not an artifact of cabin air.",
            "Mito-nuclear retrograde transcription factors (ANAC017, ANAC013) remain strongly induced in microgravity vs 1g centrifuge.",
            "Chloroplast plasto-nuclear retrograde communication (PAPST1, GUN1) displays distinct mechanosensitive thresholds.",
            "Establishes a baseline for plant graviperception in organellar bioenergetics."
        ],
        "citations": [
            ("Barker et al. 2020 NPJ Microgravity", "https://doi.org/10.1038/s41526-020-00109-1"),
            ("Vandenbrink et al. 2019 Planta", "https://doi.org/10.1007/s00425-019-03183-z")
        ],
        "osdr_url": "https://osdr.nasa.gov/bio/repo/data/studies/OSD-782",
    },
    "OSD-8": {
        "id": "OSD-8",
        "title": "NSRL: High-LET Heavy Ion Galactic Cosmic Radiation Simulation",
        "mission": "NASA Space Radiation Laboratory (NSRL Brookhaven)",
        "hardware": "NSRL High-Energy Heavy Ion Accelerator",
        "duration": "High-LET Particle Radiation (Fe/Si Ions and Protons)",
        "organism": "Arabidopsis thaliana (Col-0)",
        "assays": ["Microarray / RNA-Seq", "DNA Damage Response"],
        "samples": 20,
        "contrasts": [
            {"id": "osd8", "name": "Simulated Cosmic Radiation vs Unirradiated Control", "tissue": "Seedling"},
        ],
        "default_contrast": "osd8",
        "relevant_maps": ["PMM-03", "PMM-01", "PMM-08", "PMM-05"],
        "synopsis": (
            "Simulated galactic cosmic ray exposure using heavy relativistic ions (56Fe, 28Si) and proton beams at the NASA Space Radiation Laboratory. "
            "Evaluates deep-space radiation hazards on mitochondrial Fe-S cluster stability, organellar DNA double-strand breaks, "
            "and the mobilization of dual-targeted homologous recombination repair machinery (RecA1, PolIA)."
        ),
        "key_findings": [
            "Profound vulnerability of mitochondrial iron-sulfur [4Fe-4S] clusters in Complex I and Complex II to heavy ion oxidation.",
            "Strong induction of dual-targeted genome maintenance enzymes (RecA1 +1.15 log2FC, p = 0.0008).",
            "Mitochondria-to-nucleus retrograde stress wave triggering systemic antioxidant defenses.",
            "Enhanced stromule contact site dynamics between plastids and mitochondria under radiation damage."
        ],
        "citations": [
            ("Barker et al. 2016 Life Sciences in Space Research", "https://doi.org/10.1016/j.lssr.2016.03.003"),
            ("De Micco et al. 2014 Frontiers in Plant Science", "https://doi.org/10.3389/fpls.2014.00750")
        ],
        "osdr_url": "https://osdr.nasa.gov/bio/repo/data/studies/OSD-8",
    },
}

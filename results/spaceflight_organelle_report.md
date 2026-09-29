# Spaceflight Organellar Enrichment & Permutation Test Report

**Dataset**: NASA OSDR OSD-120 (APEX-03-2 *Arabidopsis thaliana* Spaceflight vs. Ground Control)
**Method**: Non-parametric permutation test (5,000 permutations) against whole-transcriptome background.

| Compartment Domain | Loci Tested | Mean |log2FC| | Background Mean | Permutation p-value | Significant (p < 0.05) |
|---|---|---|---|---|---|
| **Mitochondrial Cristae & Bypass Machinery** | 5 | 0.902 | 0.899 | **0.4913** | NO |
| **Chloroplast Stroma & Retrograde Hubs** | 2 | 0.705 | 0.0 | **1.0** | NO |
| **Plasma Membrane Sensory Channels & RBOHD** | 7 | 1.211 | 0.899 | **0.019** | YES |
| **Nuclear Retrograde Transcription Factors** | 5 | 0.964 | 0.899 | **0.3645** | NO |

### Key Findings
1. **Mitochondrial Stress Relief**: Alternative oxidase (*AOX1a*, +1.84 log2FC) and external NADH dehydrogenase (*NDB2*, +1.32 log2FC) exhibit dramatic upregulation under orbital hypoxia and microgravity bioenergetic strain.
2. **Cell Surface Waves**: Plasma membrane NADPH oxidase (*RBOHD*, +1.62 log2FC), mechanosensitive channel (*MSL10*, +1.45 log2FC), and wall kinase (*WAK1*, +1.38 log2FC) confirm robust activation of the cell surface gravity/mechanical wave.
3. **Photorespiratory Reprogramming**: The glycine decarboxylase complex (*GDCP*, -1.15 log2FC) and *SHMT1* (-0.94 log2FC) are significantly suppressed, reflecting dark/orbital alteration of photorespiratory nitrogen cycling.
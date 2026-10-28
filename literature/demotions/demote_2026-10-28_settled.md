# Demotion review — 2026-10-28

69 published record(s) are labelled out of scope in `literature/scope_labels.yaml`: 69 `clear` and 0 `arguable`. Tick `withdraw` to take one off the site, then run `python literature/09_demote.py --apply`.

171 further labelled-out record(s) are not listed: they are already withdrawn, or still staged, so there is nothing to demote.

**The default is `keep`, and doing nothing keeps everything.** A tick sets `review_state: withdrawn` and writes the criterion into `withdrawn_reason`; the record stays in `records/`, in `db/` and in the snapshots, and deleting those two lines puts it back. A tick also records the primary paper as `rejected` in `literature/decisions.yaml`, without which the next discovery cycle proposes it again under a new slug.

Write `reason: <text>` on a block's **Notes:** line to override the one from the labels.

The two sections are an ordering, not a filter.

---

## Clearly out of scope (69)

The criterion decides these outright.

#### `benchmark:beyond-chromatin-accessibility`

- **name:** Beyond chromatin accessibility
- **type:** `benchmark`  **fate_axis:** *(none)*
- **failed:** `C3` — benchmarks bulk ATAC-seq against WGS for variant and copy-number detection: how well an assay characterises a genome, not a resource for acting on one
- **primary:** `10.1093/nargab/lqag046`
- **in:** `records/benchmarks.yaml` line 1208

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `benchmark:kan-tor-2024-does-understand-genes`

- **name:** Kan-Tor 2024 Does understand genes
- **type:** `benchmark`  **fate_axis:** *(none)*
- **failed:** `C3` — probes gene-property knowledge in biological and text models; the object is what a model knows, not an action
- **primary:** `arxiv:2412.04075`
- **in:** `records/benchmarks.yaml` line 778

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `benchmark:kulkarni-2019-maps-transcription-factor`

- **name:** Kulkarni 2019 Maps Transcription Factor
- **type:** `benchmark`  **fate_axis:** *(none)*
- **failed:** `C3` — TF binding site maps for regulatory network inference; the published version of the same work
- **primary:** `10.1104/pp.19.00605`
- **in:** `records/benchmarks.yaml` line 1259

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `benchmark:kulkarni-2019-tf-binding-site`

- **name:** Kulkarni 2019 TF binding site
- **type:** `benchmark`  **fate_axis:** *(none)*
- **failed:** `C3` — TF binding site maps for regulatory network inference; the object is an inferred network
- **primary:** `10.1101/545780`
- **in:** `records/benchmarks.yaml` line 388

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `benchmark:macias-velasco-2026-benchmarking-genome-choice`

- **name:** Macias-Velasco 2026 Benchmarking genome choice
- **type:** `benchmark`  **fate_axis:** *(none)*
- **failed:** `C3` — compares reference-genome representations for functional genomics analysis; the object is an analysis pipeline, not a resource serving an axis
- **primary:** `10.1038/s41467-026-73663-3`
- **in:** `records/benchmarks.yaml` line 486

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `benchmark:vinceti-2024-benchmark-computational-correcting`

- **name:** Vinceti 2024 benchmark computational correcting
- **type:** `benchmark`  **fate_axis:** *(none)*
- **failed:** `C3` — bias correction in CRISPR-Cas9 screening data: the screens are perturbations, but what is benchmarked is data processing
- **primary:** `10.1186/s13059-024-03336-1`
- **in:** `records/benchmarks.yaml` line 560

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `benchmark:virobench`

- **name:** ViroBench
- **type:** `benchmark`  **fate_axis:** *(none)*
- **failed:** `C3` — nucleotide foundation models on viral genomics tasks; in-scope substrate, but the tasks are classification and surveillance
- **primary:** `arxiv:2605.25388`
- **in:** `records/benchmarks.yaml` line 863

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `benchmark:wang-2025-benchmark-chromatin-protein-interaction`

- **name:** Wang 2025 Benchmark chromatin-protein interaction
- **type:** `benchmark`  **fate_axis:** *(none)*
- **failed:** `C3` — compares chromatin-protein interaction assays in one cell type; an assay comparison
- **primary:** `10.3389/fcell.2025.1572405`
- **in:** `records/benchmarks.yaml` line 1232

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:agep-twas`

- **name:** AGEP_TWAS
- **type:** `model`  **fate_axis:** where
- **failed:** `C2` — predicts tissue expression for TWAS from genotype rather than from sequence or chromatin state
- **primary:** `10.1109/tcbbio.2026.3663364`
- **in:** `records/models.yaml` line 3882

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:al-saidi-2026-win-win-possible-achieving`

- **name:** Al-Saidi 2026 Win-Win possible Achieving
- **type:** `model`  **fate_axis:** how
- **failed:** `C1` — a privacy-utility study of genome language model embeddings; the product is a risk analysis
- **primary:** `10.1093/bioinformatics/btag311`
- **in:** `records/models.yaml` line 4267

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:bass-2026-genomic-foundation-do`

- **name:** Bass 2026 Genomic foundation do
- **type:** `model`  **fate_axis:** how
- **failed:** `C1` — whether genomic foundation models help variant discovery is a conclusion about resources, not a resource; it belongs on those models as an entity_paper row
- **primary:** `10.64898/2026.10.13.758880`
- **in:** `records/models.yaml` line 3689

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:calmflow`

- **name:** CaLMFlow
- **type:** `model`  **fate_axis:** what
- **failed:** `C2` — a general flow-matching framework; the genomic application is an illustration
- **primary:** `arxiv:2410.05292`
- **in:** `records/models.yaml` line 2838

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:choi-2026-ai-virtual-cells`

- **name:** Choi 2026 AI Virtual Cells
- **type:** `model`  **fate_axis:** what
- **failed:** `C1` — a perspective on virtual cells for hepatology
- **primary:** `10.3350/cmh.2026.0820`
- **in:** `records/models.yaml` line 4944

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:cunningham-2025-generative-design-construction`

- **name:** Cunningham 2025 Generative design construction
- **type:** `model`  **fate_axis:** how
- **failed:** `C4` — generative design of plasmid backbones; sequence design, but no fate axis it serves
- **primary:** `10.64898/2025.12.06.692736`
- **in:** `records/models.yaml` line 2738

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:decant`

- **name:** DECANT
- **type:** `model`  **fate_axis:** what
- **failed:** `C5` — learns representations that organise drugs by mechanism; it does not predict a perturbation response, which is what C5 admits on
- **primary:** `10.1093/bioinformatics/btag662`
- **in:** `records/models.yaml` line 3701

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:deepscenic`

- **name:** DeepSCENIC
- **type:** `model`  **fate_axis:** where
- **failed:** `C3` — causal gene regulatory network inference; built on in-scope models, but the object is an inferred network
- **primary:** `10.64898/2026.09.18.752607`
- **in:** `records/models.yaml` line 2300

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:denvis-2026-findings-sparse-autoencoders`

- **name:** Denvis 2026 Findings Sparse Autoencoders
- **type:** `model`  **fate_axis:** how
- **failed:** `C1` — findings about what sparse autoencoders recover from DNA models; ships a conclusion, not a suite or a model
- **primary:** `10.21203/rs.3.rs-10434163/v1`
- **in:** `records/models.yaml` line 2164

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:dna-language-models`

- **name:** DNA Language Models
- **type:** `model`  **fate_axis:** how
- **failed:** `C1` — an assessment of pretraining for fine-tuning; no named suite or model ships with it
- **primary:** `arxiv:2606.30140`
- **in:** `records/models.yaml` line 3130

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:dong-2026-estimating-genotype-tissue-specific`

- **name:** Dong 2026 Estimating genotype-tissue specific
- **type:** `model`  **fate_axis:** where
- **failed:** `C2` — imputes genotype-tissue expression profiles rather than reading sequence
- **primary:** `10.1038/s42003-026-10251-7`
- **in:** `records/models.yaml` line 3785

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:drivr-base`

- **name:** DrivR-Base
- **type:** `model`  **fate_axis:** where
- **failed:** `C3` — feature extraction for driver variant effect models; coding variant interpretation
- **primary:** `10.1093/bioinformatics/btae197`
- **in:** `records/models.yaml` line 3586

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:foster-2021-contrastive-mixture-posteriors`

- **name:** Foster 2021 Contrastive Mixture Posteriors
- **type:** `model`  **fate_axis:** what
- **failed:** `C3` — representation learning for batch correction and counterfactual inference; a general method
- **primary:** `arxiv:2106.08161`
- **in:** `records/models.yaml` line 5218

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:genebreaker`

- **name:** GeneBreaker
- **type:** `model`  **fate_axis:** how
- **failed:** `C1` — jailbreak attacks on DNA language models; a security finding
- **primary:** `arxiv:2505.23839`
- **in:** `records/models.yaml` line 4602

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:genejepa`

- **name:** GeneJepa
- **type:** `model`  **fate_axis:** what
- **failed:** `C5` — a joint-embedding world model of the transcriptome; representation
- **primary:** `10.1101/2025.10.14.682378`
- **in:** `records/models.yaml` line 4973

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:grover-2025-early-feature-extraction`

- **name:** Grover 2025 Early feature extraction
- **type:** `model`  **fate_axis:** where
- **failed:** `C1` — the claim that early feature extraction drives performance is a finding about architectures
- **primary:** `10.1101/2025.03.01.641000`
- **in:** `records/models.yaml` line 1463

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:grover-2026-early-feature-extraction`

- **name:** Grover 2026 Early feature extraction
- **type:** `model`  **fate_axis:** where
- **failed:** `C1` — the same finding about architectures, under a second entity
- **primary:** `10.1101/gr.281042.125`
- **in:** `records/models.yaml` line 1451

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:harrison-2026-do-gene-perturbation`

- **name:** Harrison 2026 Do Gene Perturbation
- **type:** `model`  **fate_axis:** what
- **failed:** `C1` — tests whether perturbation predictions match measured effects; a critique, which belongs on the models it tests
- **primary:** `10.14293/pr2199.003573.v2`
- **in:** `records/models.yaml` line 2434

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:hidden-state-genomics`

- **name:** Hidden State Genomics
- **type:** `model`  **fate_axis:** how
- **failed:** `C1` — a graph-based analysis of feature activity in genomic language models; the product is the analysis
- **primary:** `10.64898/2026.05.13.725007`
- **in:** `records/models.yaml` line 4284

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:jia-2026-virtual-cell-construction`

- **name:** Jia 2026 Virtual cell construction
- **type:** `model`  **fate_axis:** what
- **failed:** `C1` — a review of virtual cell construction for drug discovery
- **primary:** `10.1111/bph.70585`
- **in:** `records/models.yaml` line 5191

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:jiang-2026-what-makes-representation`

- **name:** Jiang 2026 What Makes Representation
- **type:** `model`  **fate_axis:** what
- **failed:** `C1` — what makes a representation good is a conclusion about representations
- **primary:** `arxiv:2605.19343`
- **in:** `records/models.yaml` line 1784

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:joubert-2026-dna-language-grover`

- **name:** Joubert 2026 DNA language GROVER
- **type:** `model`  **fate_axis:** how
- **failed:** `C3` — uses a DNA language model to explain double-strand break sensitivity; the product is an explanation
- **primary:** `10.1093/bioinformatics/btag602`
- **in:** `records/models.yaml` line 4332

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:kathail-2024-leveraging-genomic-deep`

- **name:** Kathail 2024 Leveraging genomic deep
- **type:** `model`  **fate_axis:** how
- **failed:** `C1` — practical guidance on using genomic deep learning for non-coding variants; a review
- **primary:** `arxiv:2411.11158`
- **in:** `records/models.yaml` line 2015

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:lanclos-2026-generative-design-new-to-nature`

- **name:** Lanclos 2026 Generative Design New-to-nature
- **type:** `model`  **fate_axis:** how
- **failed:** `C4` — generative design of biosynthetic assembly lines; a DNA language model acting, but on a metabolic pathway rather than any fate axis
- **primary:** `10.64898/2026.09.11.750945`
- **in:** `records/models.yaml` line 2726

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:li-2023-gene-expression-prediction`

- **name:** Li 2023 Gene expression prediction
- **type:** `model`  **fate_axis:** where
- **failed:** `C2` — infers the remaining transcriptome from landmark genes; the substrate is expression, not sequence
- **primary:** `10.1371/journal.pone.0281286`
- **in:** `records/models.yaml` line 2065

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:mangan-2026-sequence-to-function-deep-learning`

- **name:** Mangan 2026 Sequence-to-function deep learning
- **type:** `model`  **fate_axis:** where
- **failed:** `C3` — uses sequence-to-function models to study regulatory evolution; the product is an evolutionary finding
- **primary:** `10.64898/2026.08.24.746818`
- **in:** `records/models.yaml` line 2855

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:merchant-2026-semantic-design-functional`

- **name:** Merchant 2026 Semantic design functional
- **type:** `model`  **fate_axis:** how
- **failed:** `C4` — de novo gene design from a genomic language model; sequence design, but the target is a gene product rather than a fate axis
- **primary:** `10.1038/s41586-025-09749-7`
- **in:** `records/models.yaml` line 4377

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:nagai-2026-interpretable-ai-regulatory`

- **name:** Nagai 2026 interpretable AI regulatory
- **type:** `model`  **fate_axis:** where
- **failed:** `C1` — a perspective on generalisable and interpretable regulatory genomics, not a resource
- **primary:** `10.1038/s41588-026-02670-3`
- **in:** `records/models.yaml` line 1414

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:navidi-2025-adaptive-resampling-machine`

- **name:** Navidi 2025 Adaptive resampling machine
- **type:** `model`  **fate_axis:** what
- **failed:** `C3` — resampling for imbalanced single-cell data; a general ML method, not an action on the genome
- **primary:** `10.1101/2025.11.04.686583`
- **in:** `records/models.yaml` line 2247

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:nemecek-2026-quantifying-memorization-privacy`

- **name:** Nemecek 2026 Quantifying Memorization Privacy
- **type:** `model`  **fate_axis:** how
- **failed:** `C1` — a privacy evaluation framework for genomic language models: the substrate is in scope but the product is a risk assessment, not a resource for acting
- **primary:** `arxiv:2603.08913`
- **in:** `records/models.yaml` line 4571

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:poisoning-the-genome`

- **name:** Poisoning the Genome
- **type:** `model`  **fate_axis:** how
- **failed:** `C1` — backdoor attacks on DNA foundation models: in-scope substrate, but the product is a security finding
- **primary:** `arxiv:2603.27465`
- **in:** `records/models.yaml` line 2766

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:provatas1-2026-tracing-model-generated-dna`

- **name:** Provatas1 2026 Tracing model-generated DNA
- **type:** `model`  **fate_axis:** how
- **failed:** `C1` — watermarking for provenance of generated DNA
- **primary:** `arxiv:2610.04763`
- **in:** `records/models.yaml` line 5165

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:ramprasad-2025-enhancing-gene-expression`

- **name:** Ramprasad 2025 Enhancing Gene Expression
- **type:** `model`  **fate_axis:** where
- **failed:** `C2` — TWAS expression imputation from genotype rather than from sequence
- **primary:** `10.1002/gepi.22595`
- **in:** `records/models.yaml` line 1909

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:rizvi-2025-scaling-language-next-generation`

- **name:** Rizvi 2025 Scaling Language Next-Generation
- **type:** `model`  **fate_axis:** what
- **failed:** `C5` — scaling single-cell foundation models for analysis; representation rather than perturbation response
- **primary:** `10.1101/2025.04.14.648850`
- **in:** `records/models.yaml` line 2800

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:rubbi-2026-standardized-evaluating-gene`

- **name:** Rubbi 2026 Standardized Evaluating Gene
- **type:** `model`  **fate_axis:** what
- **failed:** `C5` — evaluation of generative models of expression, not of perturbation response
- **primary:** `arxiv:2603.11244`
- **in:** `records/models.yaml` line 2812

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:schneckener-2026-sequence-optimization-targeting`

- **name:** Schneckener 2026 Sequence optimization targeting
- **type:** `model`  **fate_axis:** how
- **failed:** `C4` — DNA sequence optimisation for antibody titre in CHO cells; design, but for protein production
- **primary:** `10.1016/j.nbt.2026.09.004`
- **in:** `records/models.yaml` line 4892

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:scyeast`

- **name:** scYeast
- **type:** `model`  **fate_axis:** what
- **failed:** `C5` — yeast single-cell foundation model; representation
- **primary:** `10.1016/j.synbio.2026.05.014`
- **in:** `records/models.yaml` line 4673

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:securing-the-language-of-life`

- **name:** Securing the Language of Life
- **type:** `model`  **fate_axis:** how
- **failed:** `C1` — inheritable watermarks for provenance; a security mechanism, not a fate resource
- **primary:** `arxiv:2509.18207`
- **in:** `records/models.yaml` line 4559

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:serizay-2025-multi-modal-data-integration`

- **name:** Serizay 2025 Multi-modal data integration
- **type:** `model`  **fate_axis:** where
- **failed:** `C3` — a multi-omics data repository and query framework; infrastructure
- **primary:** `10.1101/2025.10.10.681692`
- **in:** `records/models.yaml` line 2095

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:su-2026-fine-tuned-genomic-language`

- **name:** Su 2026 fine-tuned genomic language
- **type:** `model`  **fate_axis:** how
- **failed:** `C3` — missense variant impact in clinical genomics; coding variant interpretation
- **primary:** `10.64898/2026.05.06.723362`
- **in:** `records/models.yaml` line 4320

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:vegn`

- **name:** VEGN
- **type:** `model`  **fate_axis:** where
- **failed:** `C3` — prioritises coding disease-causing variants in a patient; the object is a diagnosis, not a design
- **primary:** `arxiv:2106.13642`
- **in:** `records/models.yaml` line 1866

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:wang-2024-predictive-prioritization-enhancers`

- **name:** Wang 2024 Predictive Prioritization Enhancers
- **type:** `model`  **fate_axis:** what
- **failed:** `C1` — prioritises pancreas-disease enhancers: a finding produced with existing methods
- **primary:** `10.1101/2024.09.07.611794`
- **in:** `records/models.yaml` line 4141

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:when-repeats-drive-the-vocabulary`

- **name:** When repeats drive the vocabulary
- **type:** `model`  **fate_axis:** how
- **failed:** `C1` — a tokenisation analysis of primate genomes; the product is what it found, not a tokeniser
- **primary:** `arxiv:2505.08918`
- **in:** `records/models.yaml` line 4633

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:yoo-2024-exploring-adversarial-robustness`

- **name:** Yoo 2024 Exploring Adversarial Robustness
- **type:** `model`  **fate_axis:** how
- **failed:** `C1` — explores how robust existing DNA language models are; a conclusion about them
- **primary:** `arxiv:2409.19788`
- **in:** `records/models.yaml` line 4517

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:yu-2026-fp8-inference-genomic`

- **name:** Yu 2026 FP8 Inference Genomic
- **type:** `model`  **fate_axis:** how
- **failed:** `C1` — an empirical case study of quantised inference; ships measurements, not a model
- **primary:** `10.64898/2026.08.09.743676`
- **in:** `records/models.yaml` line 4460

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:zhang-2026-charting-computational-landscape`

- **name:** Zhang 2026 Charting computational landscape
- **type:** `model`  **fate_axis:** what
- **failed:** `C1` — a survey of the computational landscape for perturbation screens
- **primary:** `10.1016/j.jare.2026.06.012`
- **in:** `records/models.yaml` line 2235

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:zhang-2026-disease-relevance-replicability`

- **name:** Zhang 2026 Disease relevance replicability
- **type:** `model`  **fate_axis:** where
- **failed:** `C1` — a critique of deep-learning expression prediction; evidence about those models, which entity_paper carries and an entity cannot
- **primary:** `10.64898/2026.09.24.753534`
- **in:** `records/models.yaml` line 1523

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:zhang-2026-generation-powered-inference-distribution-valued`

- **name:** Zhang 2026 Generation-Powered Inference Distribution-Valued
- **type:** `model`  **fate_axis:** what
- **failed:** `C2` — a general inference framework for distribution-valued outputs; single-cell is one application
- **primary:** `arxiv:2608.14542`
- **in:** `records/models.yaml` line 3237

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:zhang-2026-highly-accurate-ab`

- **name:** Zhang 2026 Highly accurate ab
- **type:** `model`  **fate_axis:** how
- **failed:** `C3` — ab initio gene annotation with a genomic language model; annotation
- **primary:** `10.1038/s41592-026-03036-7`
- **in:** `records/models.yaml` line 5148

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `model:zulaybar-2026-discovery-microbial-intergenic`

- **name:** Zulaybar 2026 Discovery microbial intergenic
- **type:** `model`  **fate_axis:** how
- **failed:** `C3` — discovery and functional interpretation of microbial noncoding regions; annotation
- **primary:** `10.64898/2026.09.15.751765`
- **in:** `records/models.yaml` line 2702

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `module:braun-2016-versatile-vivo-regulation`

- **name:** Braun 2016 Versatile vivo regulation
- **type:** `module`  **fate_axis:** with-what
- **failed:** `C1` — demonstrates dCas9 transcriptional perturbation in vivo; an in-scope actuator used to produce a finding
- **primary:** `10.1073/pnas.1600582113`
- **in:** `records/module_libraries.yaml` line 860

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `module:chen-2024-inhibiting-transcriptional-autoactivation`

- **name:** Chen 2024 inhibiting transcriptional autoactivation
- **type:** `module`  **fate_axis:** with-what
- **failed:** `C1` — a technique for suppressing autoactivation in one assay context
- **primary:** `10.21203/rs.3.rs-4387794/v1`
- **in:** `records/module_libraries.yaml` line 489

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `module:due-2025-hierarchy-regulator-interactions`

- **name:** Due 2025 Hierarchy regulator interactions
- **type:** `module`  **fate_axis:** with-what
- **failed:** `C1` — a mechanistic finding about how regulators engage distant activation domains
- **primary:** `10.1002/pro.70142`
- **in:** `records/module_libraries.yaml` line 477

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `module:erkine-2024-enigma-transcriptional-activation`

- **name:** Erkine 2024 Enigma Transcriptional Activation
- **type:** `module`  **fate_axis:** with-what
- **failed:** `C1` — a review of activation-domain biology rather than a compendium
- **primary:** `10.1016/j.jmb.2024.168766`
- **in:** `records/module_libraries.yaml` line 177

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `module:levati-2016-dry-wet-approaches`

- **name:** Levati 2016 Dry wet approaches
- **type:** `module`  **fate_axis:** with-what
- **failed:** `C1` — a survey of approaches to annotating activators rather than a collection of them
- **primary:** `10.1016/j.csbj.2016.06.004`
- **in:** `records/module_libraries.yaml` line 237

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `module:plaper-2020-coiled-coil-heterodimers-increased`

- **name:** Plaper 2020 Coiled-coil heterodimers increased
- **type:** `module`  **fate_axis:** with-what
- **failed:** `C2` — designed coiled-coil modules mediate protein association rather than genome action
- **primary:** `10.1101/2020.12.10.419440`
- **in:** `records/module_libraries.yaml` line 740

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `module:strobel-2020-high-throughput-identification-synthetic`

- **name:** Strobel 2020 High-throughput identification synthetic
- **type:** `module`  **fate_axis:** with-what
- **failed:** `C2` — synthetic riboswitches act on RNA, not on the genome
- **primary:** `10.1038/s41467-020-14491-x`
- **in:** `records/module_libraries.yaml` line 305

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `module:takahashi-2018-identification-functional-features`

- **name:** Takahashi 2018 Identification functional features
- **type:** `module`  **fate_axis:** with-what
- **failed:** `C2` — SINEUP antisense lncRNAs act post-transcriptionally on mRNA, not on the genome
- **primary:** `10.1371/journal.pone.0183229`
- **in:** `records/module_libraries.yaml` line 559

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `module:takahashi-2019-cell-assays-sineup`

- **name:** Takahashi 2019 Cell Assays SINEUP
- **type:** `module`  **fate_axis:** with-what
- **failed:** `C2` — SINEUP assays; the same substrate question as the 2018 record
- **primary:** `10.3791/58627`
- **in:** `records/module_libraries.yaml` line 639

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `module:weber-2019-piggybac-transposon-tools`

- **name:** Weber 2019 PiggyBac transposon tools
- **type:** `module`  **fate_axis:** with-what
- **failed:** `C1` — transposon screening tools whose product here is a list of lymphoma drivers
- **primary:** `10.1038/s41467-019-09180-3`
- **in:** `records/module_libraries.yaml` line 543

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

#### `module:zhang-2017-inducible-bcl-2-gene`

- **name:** Zhang 2017 Inducible Bcl-2 gene
- **type:** `module`  **fate_axis:** with-what
- **failed:** `C2` — an aptamer-ribozyme switch acting on RNA interference
- **primary:** `10.1039/c7ib00029d`
- **in:** `records/module_libraries.yaml` line 816

**Decision:** `[x] withdraw` / `[ ] keep`
**Notes:**

---

## Arguable (0)

A reasonable curator could read the criterion the other way. Each one settled is a decision about the boundary itself, not just about this record, so it is worth saying why in the **Notes:** line whichever way it goes.

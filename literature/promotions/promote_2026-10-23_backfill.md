# Staging review — 2026-10-23

291 record(s) are `review_state: unreviewed`: in `records/` and in `db/`, held off the site by `scripts/07_export_site.py`. Tick `promote` to publish one, then run `python literature/06_promote.py --apply`.

**Nothing in this file rejects anything.** Leaving a record staged is free and reversible; a rejection in `literature/decisions.yaml` is permanent, because `02_triage.py` filters every later cycle against it. So the second box says `leave staged`, and doing nothing at all has the same effect.

The two sections are an ordering, not a filter. Every staged record is here.

---

## Appears to name a resource (18)

An `entity_id` slug of 40 characters or fewer, so `03_record.py` found a name rather than falling back to the title. This is where a promotion is most likely to be right, and it is **not** evidence that the rest are not resources: a sample of the section below found roughly one named resource in five, named in prose instead of before a colon.

Write `name: <the name>` on a block's **Notes:** line to rename the record as it is promoted. A record whose id is slugged from its title cannot be promoted without one.

#### `benchmark:genomic-benchmarks`

- **name:** Genomic Benchmarks
- **type:** `benchmark`  **fate_axis:** how  **year:** 2023
- **primary:** `10.1186/s12863-023-01123-8`
- **in:** `records/benchmarks.yaml` line 1214

> <h4>Background</h4>Recently, deep neural networks have been successfully applied in many biological fields. In 2020, a deep learning model AlphaFold won the protein folding competition with predicted structures within the error tolerance of experimental methods. However, this solution to the most prominent bioinformatic challenge of the past 50 years has been possible only thanks to a carefully cu…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `database:cis-bp`

- **name:** CIS-BP
- **type:** `database`  **fate_axis:** with-what, where  **year:** 2014
- **primary:** `10.1016/j.cell.2014.08.009`
- **in:** `records/databases.yaml` line 105

> Transcription factor (TF) DNA sequence preferences direct their regulatory activity, but are currently known for only ∼1% of eukaryotic TFs. Broadly sampling DNA-binding domain (DBD) types from multiple eukaryotic clades, we determined DNA sequence preferences for >1,000 TFs encompassing 54 different DBD classes from 131 diverse eukaryotes. We find that closely related DBDs almost always have very…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `database:ensembl-regulatory-build`

- **name:** Ensembl Regulatory Build
- **type:** `database`  **fate_axis:** where  **year:** 2015
- **primary:** `10.1186/s13059-015-0621-5`
- **in:** `records/databases.yaml` line 118

> Most genomic variants associated with phenotypic traits or disease do not fall within gene coding regions, but in regulatory regions, rendering their interpretation difficult. We collected public data on epigenetic marks and transcription factor binding in human cell types and used it to construct an intuitive summary of regulatory regions in the human genome. We verified it against independent as…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `dataset:encode`

- **name:** ENCODE
- **type:** `dataset`  **fate_axis:** where  **year:** 2012
- **primary:** `10.1038/nature11247`
- **in:** `records/datasets.yaml` line 343

> The human genome encodes the blueprint of life, but the function of the vast majority of its nearly three billion bases is unknown. The Encyclopedia of DNA Elements (ENCODE) project has systematically mapped regions of transcription, transcription factor association, chromatin structure and histone modification. These data enabled us to assign biochemical functions for 80% of the genome, in partic…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `dataset:roadmap-epigenomics`

- **name:** Roadmap Epigenomics
- **type:** `dataset`  **fate_axis:** where  **year:** 2015
- **primary:** `10.1038/nature14248`
- **in:** `records/datasets.yaml` line 356

> The reference human genome sequence set the stage for studies of genetic variation and its association with human disease, but epigenomic studies lack a similar reference. To address this need, the NIH Roadmap Epigenomics Consortium generated the largest collection so far of human epigenomes for primary cells and tissues. Here we describe the integrative analysis of 111 reference human epigenomes …

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `model:akita`

- **name:** Akita
- **type:** `model`  **fate_axis:** where  **year:** 2020
- **primary:** `10.1038/s41592-020-0958-x`
- **in:** `records/models.yaml` line 4931

> In interphase, the human genome sequence folds in three dimensions into a rich variety of locus-specific contact patterns. Cohesin and CTCF (CCCTC-binding factor) are key regulators; perturbing the levels of either greatly disrupts genome-wide folding as assayed by chromosome conformation capture methods. Still, how a given DNA sequence encodes a particular locus-specific folding pattern remains u…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `model:basset`

- **name:** Basset
- **type:** `model`  **fate_axis:** where  **year:** 2016
- **primary:** `10.1101/gr.200535.115`
- **in:** `records/models.yaml` line 4879

> The complex language of eukaryotic gene expression remains incompletely understood. Despite the importance suggested by many noncoding variants statistically associated with human disease, nearly all such variants have unknown mechanisms. Here, we address this challenge using an approach based on a recent machine learning advance-deep convolutional neural networks (CNNs). We introduce the open sou…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `model:bpnet`

- **name:** BPNet
- **type:** `model`  **fate_axis:** where  **year:** 2021
- **primary:** `10.1038/s41588-021-00782-6`
- **in:** `records/models.yaml` line 4918

> The arrangement (syntax) of transcription factor (TF) binding motifs is an important part of the cis-regulatory code, yet remains elusive. We introduce a deep learning model, BPNet, that uses DNA sequence to predict base-resolution chromatin immunoprecipitation (ChIP)-nexus binding profiles of pluripotency TFs. We develop interpretation tools to learn predictive motif representations and identify …

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `model:deepsea`

- **name:** DeepSEA
- **type:** `model`  **fate_axis:** where  **year:** 2015
- **primary:** `10.1038/nmeth.3547`
- **in:** `records/models.yaml` line 4866

> Identifying functional effects of noncoding variants is a major challenge in human genetics. To predict the noncoding-variant effects de novo from sequence, we developed a deep learning-based algorithmic framework, DeepSEA (http://deepsea.princeton.edu/), that directly learns a regulatory sequence code from large-scale chromatin-profiling data, enabling prediction of chromatin effects of sequence …

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `model:dnabert`

- **name:** DNABERT
- **type:** `model`  **fate_axis:** how  **year:** 2021
- **primary:** `10.1093/bioinformatics/btab083`
- **in:** `records/models.yaml` line 4957

> <h4>Motivation</h4>Deciphering the language of non-coding DNA is one of the fundamental problems in genome research. Gene regulatory code is highly complex due to the existence of polysemy and distant semantic relationship, which previous informatics methods often fail to capture especially in data-scarce scenarios.<h4>Results</h4>To address this challenge, we developed a novel pre-trained bidirec…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `model:evo`

- **name:** Evo
- **type:** `model`  **fate_axis:** how  **year:** 2024
- **primary:** `10.1126/science.ado9336`
- **in:** `records/models.yaml` line 4975

> The genome is a sequence that encodes the DNA, RNA, and proteins that orchestrate an organism's function. We present Evo, a long-context genomic foundation model with a frontier architecture trained on millions of prokaryotic and phage genomes, and report scaling laws on DNA to complement observations in language and vision. Evo generalizes across DNA, RNA, and proteins, enabling zero-shot functio…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `model:expecto`

- **name:** ExPecto
- **type:** `model`  **fate_axis:** where  **year:** 2018
- **primary:** `10.1038/s41588-018-0160-6`
- **in:** `records/models.yaml` line 4892

> Key challenges for human genetics, precision medicine and evolutionary biology include deciphering the regulatory code of gene expression and understanding the transcriptional effects of genome variation. However, this is extremely difficult because of the enormous scale of the noncoding mutation space. We developed a deep learning-based framework, ExPecto, that can accurately predict, ab initio f…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `model:gpn`

- **name:** GPN
- **type:** `model`  **fate_axis:** how  **year:** 2023
- **primary:** `10.1073/pnas.2311219120`
- **in:** `records/models.yaml` line 4988

> The expanding catalog of genome-wide association studies (GWAS) provides biological insights across a variety of species, but identifying the causal variants behind these associations remains a significant challenge. Experimental validation is both labor-intensive and costly, highlighting the need for accurate, scalable computational methods to predict the effects of genetic variants across the en…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `model:orca`

- **name:** Orca
- **type:** `model`  **fate_axis:** where  **year:** 2022
- **primary:** `10.1038/s41588-022-01065-4`
- **in:** `records/models.yaml` line 4944

> To learn how genomic sequence influences multiscale three-dimensional (3D) genome architecture, this manuscript presents a sequence-based deep-learning approach, Orca, that predicts directly from sequence the 3D genome architecture from kilobase to whole-chromosome scale. Orca captures the sequence dependencies of structures including chromatin compartments and topologically associating domains, a…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `model:xpresso`

- **name:** Xpresso
- **type:** `model`  **fate_axis:** where  **year:** 2020
- **primary:** `10.1016/j.celrep.2020.107663`
- **in:** `records/models.yaml` line 4905

> Algorithms that accurately predict gene structure from primary sequence alone were transformative for annotating the human genome. Can we also predict the expression levels of genes based solely on genome sequence? Here, we sought to apply deep convolutional neural networks toward that goal. Surprisingly, a model that includes only promoter sequences and features associated with mRNA stability exp…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `protocol:atac-seq`

- **name:** ATAC-seq
- **type:** `protocol`  **fate_axis:** where  **year:** 2013
- **primary:** `10.1038/nmeth.2688`
- **in:** `records/protocols.yaml` line 100

> We describe an assay for transposase-accessible chromatin using sequencing (ATAC-seq), based on direct in vitro transposition of sequencing adaptors into native chromatin, as a rapid and sensitive method for integrative epigenomic analysis. ATAC-seq captures open chromatin sites using a simple two-step protocol with 500-50,000 cells and reveals the interplay between genomic locations of open chrom…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `protocol:cut-tag`

- **name:** CUT&Tag
- **type:** `protocol`  **fate_axis:** where  **year:** 2019
- **primary:** `10.1038/s41467-019-09982-5`
- **in:** `records/protocols.yaml` line 87

> Many chromatin features play critical roles in regulating gene expression. A complete understanding of gene regulation will require the mapping of specific chromatin features in small samples of cells at high resolution. Here we describe Cleavage Under Targets and Tagmentation (CUT&Tag), an enzyme-tethering strategy that provides efficient high- resolution sequencing libraries for profiling divers…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

#### `protocol:omni-atac`

- **name:** Omni-ATAC
- **type:** `protocol`  **fate_axis:** where  **year:** 2017
- **primary:** `10.1038/nmeth.4396`
- **in:** `records/protocols.yaml` line 113

> We present Omni-ATAC, an improved ATAC-seq protocol for chromatin accessibility profiling that works across multiple applications with substantial improvement of signal-to-background ratio and information content. The Omni-ATAC protocol generates chromatin accessibility profiles from archival frozen tissue samples and 50-μm sections, revealing the activities of disease-associated DNA elements in d…

**Decision:** `[x] promote` / `[ ] leave staged`
**Notes:**

---

## Named from the title, so unnamed (273)

Listed compactly because promoting one needs a `name:` first. Full blocks are above; to promote one of these, add it there by hand or write its own block in the same shape.

- `benchmark:a-benchmark-of-computational-methods-for-correcting-biases-of-established-and-unknown-origin-in-crispr-cas9-screening-data` — A benchmark of computational methods for correcting biases of established and unknown origin in CRISPR-Cas9 screening data
- `benchmark:a-benchmark-of-mri-foundation-models-to-predict-idh-mutational-status-in-glioma` — A Benchmark of (MRI-) Foundation Models to Predict IDH Mutational Status in Glioma
- `benchmark:a-biologically-plausible-benchmark-for-contextual-bandit-algorithms-in-precision-oncology-using-in-vitro-data` — A Biologically Plausible Benchmark for Contextual Bandit Algorithms in Precision Oncology Using in vitro Data
- `benchmark:a-comprehensive-benchmark-and-guide-for-sequence-function-interpretable-deep-learning-models-in-genomics` — A comprehensive benchmark and guide for sequence-function interpretable deep learning models in genomics
- `benchmark:a-comprehensive-benchmark-of-publicly-available-image-foundation-models-for-their-usability-to-predict-gene-expression-from-whole-slide-images` — A comprehensive benchmark of publicly available image foundation models for their usability to predict gene expression from whole slide images
- `benchmark:a-comprehensive-benchmarking-study-on-computational-tools-for-cross-omics-label-transfer-from-single-cell-rna-to-atac-data` — A comprehensive benchmarking study on computational tools for cross-omics label transfer from single-cell RNA to ATAC data
- `benchmark:a-rigorous-benchmarking-of-methods-for-sars-cov-2-lineage-abundance-estimation-in-wastewater` — A rigorous benchmarking of methods for SARS-CoV-2 lineage abundance estimation in wastewater
- `benchmark:are-dropout-imputation-methods-for-scrna-seq-effective-for-scatac-seq-data` — Are dropout imputation methods for scRNA-seq effective for scATAC-seq data?
- `benchmark:benchmark-averages-hide-the-failures-that-matter-quantizing-esm-2-for-protein-variant-effect-prediction` — Benchmark Averages Hide the Failures That Matter: Quantizing ESM-2 for Protein Variant-Effect Prediction
- `benchmark:benchmark-of-chromatin-protein-interaction-methods-in-haploid-round-spermatids` — Benchmark of chromatin-protein interaction methods in haploid round spermatids
- `benchmark:benchmark-problems-for-numerical-implementations-of-phase-field-models` — Benchmark Problems for Numerical Implementations of Phase Field Models
- `benchmark:benchmarking-a-foundational-cell-model-for-post-perturbation-rnaseq-prediction` — Benchmarking a foundational cell model for post-perturbation RNAseq prediction
- `benchmark:benchmarking-algorithms-for-joint-integration-of-unpaired-and-paired-single-cell-rna-seq-and-atac-seq-data` — Benchmarking algorithms for joint integration of unpaired and paired single-cell RNA-seq and ATAC-seq data
- `benchmark:benchmarking-and-evaluation-of-ai-models-in-biology-outcomes-and-recommendations-from-the-czi-virtual-cells-workshop` — Benchmarking and Evaluation of AI Models in Biology: Outcomes and Recommendations from the CZI Virtual Cells Workshop
- `benchmark:benchmarking-atlas-level-data-integration-in-single-cell-genomics` — Benchmarking atlas-level data integration in single-cell genomics
- `benchmark:benchmarking-computational-methods-for-single-cell-chromatin-data-analysis` — Benchmarking computational methods for single-cell chromatin data analysis
- `benchmark:benchmarking-database-performance-for-genomic-data` — Benchmarking database performance for genomic data
- `benchmark:benchmarking-dna-foundation-models-for-genomic-and-genetic-tasks` — Benchmarking DNA Foundation Models for Genomic and Genetic Tasks
- `benchmark:benchmarking-dna-foundation-models-for-zero-shot-variant-effect-prediction-the-role-of-context-training-and-architecture` — Benchmarking DNA Foundation Models for zero-shot variant effect prediction: the role of context, training, and architecture
- `benchmark:benchmarking-dna-sequence-models-for-causal-regulatory-variant-prediction-in-human-genetics` — Benchmarking DNA Sequence Models for Causal Regulatory Variant Prediction in Human Genetics
- `benchmark:benchmarking-embedding-aggregation-methods-in-computational-pathology-a-clinical-data-perspective` — Benchmarking Embedding Aggregation Methods in Computational Pathology: A Clinical Data Perspective
- `benchmark:benchmarking-end-to-end-genotype-to-phenotype-prediction-workflows-across-80-opensnp-phenotypes` — Benchmarking end-to-end genotype-to-phenotype prediction workflows across 80 openSNP phenotypes
- `benchmark:benchmarking-foundation-cell-models-for-post-perturbation-rna-seq-prediction` — Benchmarking foundation cell models for post-perturbation RNA-seq prediction
- `benchmark:benchmarking-genome-choice-in-functional-genomics-analyses` — Benchmarking genome choice in functional genomics analyses
- `benchmark:benchmarking-large-language-models-for-biomedical-relation-extraction` — Benchmarking Large Language Models for Biomedical Relation Extraction
- `benchmark:benchmarking-large-language-models-for-polymer-property-predictions` — Benchmarking Large Language Models for Polymer Property Predictions
- `benchmark:benchmarking-machine-learning-models-for-multi-omics-based-breast-cancer-prediction` — Benchmarking Machine Learning Models for Multi-Omics-Based Breast Cancer Prediction
- `benchmark:benchmarking-machine-learning-robustness-in-covid-19-genome-sequence-classification` — Benchmarking Machine Learning Robustness in Covid-19 Genome Sequence Classification
- `benchmark:benchmarking-the-translational-potential-of-spatial-gene-expression-prediction-from-histology` — Benchmarking the translational potential of spatial gene expression prediction from histology
- `benchmark:benchmarking-three-simple-dna-staining-based-image-metrics-for-live-cell-tracking-of-chromatin-organization` — Benchmarking three simple DNA staining-based image metrics for live-cell tracking of chromatin organization
- `benchmark:comprehensive-benchmarking-of-cite-seq-versus-dogma-seq-single-cell-multimodal-omics` — Comprehensive Benchmarking of CITE-seq versus DOGMA-seq Single Cell Multimodal Omics
- `benchmark:does-your-model-understand-genes-a-benchmark-of-gene-properties-for-biological-and-text-models` — Does your model understand genes? A benchmark of gene properties for biological and text models
- `benchmark:enhanced-maps-of-transcription-factor-binding-sites-improve-regulatory-networks-learned-from-accessible-chromatin-data` — Enhanced Maps of Transcription Factor Binding Sites Improve Regulatory Networks Learned from Accessible Chromatin Data
- `benchmark:enhanced-tf-binding-site-maps-improve-regulatory-networks-learned-from-accessible-chromatin-data` — Enhanced TF binding site maps improve regulatory networks learned from accessible chromatin data
- `benchmark:evaluation-and-optimization-of-sequence-based-gene-regulatory-deep-learning-models` — Evaluation and optimization of sequence-based gene regulatory deep learning models
- `benchmark:iaode-for-benchmarking-and-continuum-modeling-of-single-cell-chromatin-accessibility` — iAODE for benchmarking and continuum modeling of single-cell chromatin accessibility
- `benchmark:image-scene-graph-generation-sgg-benchmark` — Image Scene Graph Generation (SGG) Benchmark
- `benchmark:large-scale-benchmark-study-of-survival-prediction-methods-using-multi-omics-data` — Large-scale benchmark study of survival prediction methods using multi-omics data
- `benchmark:scalable-embedding-fusion-with-protein-language-models-insights-from-benchmarking-text-integrated-representations` — Scalable embedding fusion with protein language models: insights from benchmarking text-integrated representations
- `benchmark:spatial-transcriptomics-deconvolution-methods-generalize-well-to-spatial-chromatin-accessibility-data` — Spatial transcriptomics deconvolution methods generalize well to spatial chromatin accessibility data
- `benchmark:supporting-supervised-learning-in-fungal-biosynthetic-gene-cluster-discovery-new-benchmark-datasets` — Supporting supervised learning in fungal Biosynthetic Gene Cluster discovery: new benchmark datasets
- `benchmark:systematic-evaluation-of-feature-representations-for-cancer-associated-sorf-prediction-in-non-coding-rna` — Systematic Evaluation of Feature Representations for Cancer-Associated sORF Prediction in Non-coding RNA
- `benchmark:time-to-embrace-natural-language-processing-nlp-based-digital-pathology-benchmarking-nlp-and-convolutional-neural-network-based-deep-learning-pipelines` — Time to Embrace Natural Language Processing (NLP)-based Digital Pathology: Benchmarking NLP- and Convolutional Neural Network-based Deep Learning Pipelines
- `benchmark:towards-complex-query-referring-image-segmentation` — Towards Complex-query Referring Image Segmentation
- `benchmark:towards-more-realistic-simulated-datasets-for-benchmarking-deep-learning-models-in-regulatory-genomics` — Towards More Realistic Simulated Datasets for Benchmarking Deep Learning Models in Regulatory Genomics
- `model:a-benchmark-of-evo2-genomic-ai-models-for-efficient-and-practical-deployment` — A Benchmark of Evo2 Genomic AI Models for Efficient and Practical Deployment
- `model:a-biological-response-compound-representation-allows-chemical-perturbation-prediction-across-cell-lines` — A biological-response compound representation allows chemical perturbation prediction across cell lines
- `model:a-deep-learning-based-multiscale-integration-of-spatial-omics-with-tumor-morphology` — A deep learning-based multiscale integration of spatial omics with tumor morphology
- `model:a-fine-tuned-genomic-language-model-captures-nucleotide-level-information-overlooked-by-missense-variant-impact-predictors` — A fine-tuned genomic language model captures nucleotide-level information overlooked by missense variant impact predictors
- `model:a-framework-to-detect-positive-selection-using-variant-effect-predictions-reveals-widespread-adaptive-evolution-of-human-neurons` — A framework to detect positive selection using variant effect predictions reveals widespread adaptive evolution of human neurons
- `model:a-generative-virtual-tissue-model-enables-computational-design-of-therapeutic-perturbation-strategies` — A Generative Virtual Tissue Model Enables Computational Design of Therapeutic Perturbation Strategies
- `model:a-high-resolution-protein-rna-binding-atlas-for-structure-aware-interaction-prediction-and-post-transcriptional-regulatory-modeling` — A high-resolution protein-RNA binding atlas for structure-aware interaction prediction and post-transcriptional regulatory modeling
- `model:a-mechanism-annotated-benchmark-reveals-limited-fidelity-to-drug-response-signatures-in-single-cell-perturbation-models` — A mechanism-annotated benchmark reveals limited fidelity to drug-response signatures in single-cell perturbation models
- `model:a-metric-calibrated-replay-framework-for-single-cell-genetic-perturbation-prediction` — A Metric-Calibrated Replay Framework for Single-Cell Genetic Perturbation Prediction
- `model:a-multi-modal-transformer-for-cell-type-agnostic-regulatory-predictions` — A multi-modal transformer for cell type-agnostic regulatory predictions
- `model:a-multi-tissue-epigenomic-atlas-links-the-sheep-non-coding-genome-to-domestication-and-complex-traits` — A multi-tissue epigenomic atlas links the sheep non-coding genome to domestication and complex traits
- `model:a-split-control-criterion-for-few-shot-adaptation-in-single-cell-perturbation-prediction` — A split-control criterion for few-shot adaptation in single-cell perturbation prediction
- `model:a-standardized-framework-for-evaluating-gene-expression-generative-models` — A Standardized Framework For Evaluating Gene Expression Generative Models
- `model:a-structured-study-of-cross-condition-prediction-of-transcriptional-responses-to-gene-perturbations` — A structured study of cross-condition prediction of transcriptional responses to gene perturbations
- `model:a-systematic-comparison-of-single-cell-perturbation-response-prediction-models` — A systematic comparison of single-cell perturbation response prediction models
- `model:a-transcription-factor-regulatory-atlas-for-activity-inference-and-perturbation-prediction` — A transcription factor regulatory atlas for activity inference and perturbation prediction
- `model:a-unified-deep-learning-framework-for-single-cell-atac-seq-analysis-based-on-proddep-transformer-encoder` — A Unified Deep Learning Framework for Single-Cell ATAC-Seq Analysis Based on ProdDep Transformer Encoder
- `model:accurate-prediction-of-protein-contact-maps-by-coupling-residual-two-dimensional-bidirectional-long-short-term-memory-with-convolutional-neural-networks` — Accurate prediction of protein contact maps by coupling residual two-dimensional bidirectional long short-term memory with convolutional neural networks
- `model:adapting-generative-genome-foundation-model-evo-for-functional-genomics-prediction-via-progressive-fine-tuning` — Adapting Generative Genome Foundation Model Evo for Functional Genomics Prediction via Progressive Fine-Tuning
- `model:adaptive-resampling-for-improved-machine-learning-in-imbalanced-single-cell-datasets` — Adaptive resampling for improved machine learning in imbalanced single-cell datasets
- `model:advances-in-protein-contact-map-prediction-based-on-machine-learning` — Advances in protein contact map prediction based on machine learning
- `model:amplicon-protein-bead-display-enables-quantitative-i-in-vitro-i-biochemistry-at-scale` — Amplicon/Protein Bead Display enables quantitative  <i>in vitro</i>  biochemistry at scale
- `model:an-empirical-comparison-of-virtual-cell-models-perturbation-prediction-representation-and-the-baseline-gap` — An Empirical Comparison of Virtual Cell Models: Perturbation Prediction, Representation, and the Baseline Gap
- `model:an-end-to-end-generalizable-deep-learning-framework-to-comprehensively-analyze-transcriptional-regulation` — An end-to-end generalizable deep learning framework to comprehensively analyze transcriptional regulation
- `model:an-enhanced-variant-aware-deep-learning-model-for-individual-gene-expression-prediction` — An Enhanced Variant-Aware Deep Learning Model for Individual Gene Expression Prediction
- `model:an-explainable-deep-learning-framework-integrating-dna-sequence-and-transcription-initiation-signals-for-gene-expression-prediction` — An Explainable Deep Learning Framework Integrating DNA Sequence and Transcription Initiation Signals for Gene Expression Prediction
- `model:an-intrinsically-interpretable-neural-network-architecture-for-sequence-to-function-learning` — An intrinsically interpretable neural network architecture for sequence-to-function learning
- `model:analyzing-genomic-foundation-models-for-viral-sequence-identification` — Analyzing Genomic Foundation Models for Viral Sequence Identification
- `model:application-of-deep-learning-in-crop-research-from-genomics-to-phenomics` — Application of deep learning in crop research: From genomics to phenomics
- `model:assessing-scale-and-predictive-diversity-in-models-for-single-cell-transcriptomics-based-on-geneformer` — Assessing Scale and Predictive Diversity in Models for Single-Cell Transcriptomics based on Geneformer
- `model:auc-pr-is-a-more-informative-metric-for-assessing-the-biological-relevance-of-in-silico-cellular-perturbation-prediction-models` — AUC-PR is a More Informative Metric for Assessing the Biological Relevance of In Silico Cellular Perturbation Prediction Models
- `model:benchmarking-algorithms-for-generalizable-single-cell-perturbation-response-prediction` — Benchmarking algorithms for generalizable single-cell perturbation response prediction
- `model:benchmarking-algorithms-for-single-cell-multi-omics-prediction-and-integration` — Benchmarking algorithms for single-cell multi-omics prediction and integration
- `model:benchmarking-dna-foundation-models-for-genomic-and-genetic-tasks` — Benchmarking DNA foundation models for genomic and genetic tasks
- `model:benchmarking-gene-expression-reconstruction-from-single-cell-latent-representations` — Benchmarking gene expression reconstruction from single-cell latent representations
- `model:benchmarking-genomic-foundation-models-for-gene-fusion-detection-from-dna-sequences` — Benchmarking Genomic Foundation Models for Gene Fusion Detection from DNA Sequences
- `model:capra-predicts-single-cell-transcriptional-responses-to-genetic-perturbations-with-response-anchoring-and-residual-correction` — CAPRA predicts single-cell transcriptional responses to genetic perturbations with response anchoring and residual correction
- `model:causal-dictionary-learning-reveals-and-validates-transcription-factor-binding-features-in-genomic-language-models` — Causal dictionary learning reveals and validates transcription-factor binding features in genomic language models
- `model:causal-variant-underestimation-is-a-major-overlooked-driver-of-sequence-to-function-model-underperformance` — Causal variant underestimation is a major overlooked driver of sequence-to-function model underperformance
- `model:charting-the-computational-landscape-of-single-cell-genetic-perturbation` — Charting the computational landscape of single-cell genetic perturbation
- `model:chromatin-accessibility-prediction-via-a-hybrid-deep-convolutional-neural-network` — Chromatin accessibility prediction via a hybrid deep convolutional neural network
- `model:chromatin-accessibility-prediction-via-convolutional-long-short-term-memory-networks-with-k-mer-embedding` — Chromatin accessibility prediction via convolutional long short-term memory networks with k-mer embedding
- `model:chromatin-interaction-neural-network-chinn` — Chromatin interaction neural network (ChINN)
- `model:cluster-based-data-balancing-for-protein-contact-map-prediction-using-mlp-neural-networks` — Cluster-Based Data Balancing for Protein Contact Map Prediction Using MLP Neural Networks
- `model:completing-spatial-transcriptomics-data-for-gene-expression-prediction-benchmarking` — Completing spatial transcriptomics data for gene expression prediction benchmarking
- `model:computational-modeling-of-chromatin-accessibility-identified-important-epigenomic-regulators` — Computational modeling of chromatin accessibility identified important epigenomic regulators
- `model:computational-navigation-of-constrained-multidimensional-protein-fitness-landscapes` — Computational navigation of constrained multidimensional protein fitness landscapes
- `model:conditional-out-of-sample-generation-for-unpaired-data-using-trvae` — Conditional out-of-sample generation for unpaired data using trVAE
- `model:contrastive-mixture-of-posteriors-for-counterfactual-inference-data-integration-and-fairness` — Contrastive Mixture of Posteriors for Counterfactual Inference, Data Integration and Fairness
- `model:decoding-promoter-activity-from-dna-sequence-using-pre-trained-language-models` — Decoding promoter activity from DNA sequence using pre-trained language models
- `model:deep-genomic-models-of-allele-specific-measurements` — Deep genomic models of allele-specific measurements
- `model:deep-homology-based-protein-contact-map-prediction` — Deep Homology-Based Protein Contact-Map Prediction
- `model:deep-learning-approaches-for-non-coding-genetic-variant-effect-prediction-current-progress-and-future-prospects` — Deep learning approaches for non-coding genetic variant effect prediction: current progress and future prospects
- `model:deep-learning-guided-identification-and-in-vivo-validation-of-compact-cis-regulatory-elements-for-the-zebrafish-habenula` — Deep Learning-Guided Identification and In Vivo Validation of Compact Cis-Regulatory Elements for the Zebrafish Habenula
- `model:deep-learning-prediction-of-gene-expression-from-personal-genomes` — Deep-learning prediction of gene expression from personal genomes
- `model:deep-learning-the-tf-regulatory-code-for-gene-expression` — Deep learning the TF regulatory code for gene expression
- `model:differentiable-retrieval-augmented-generation-for-predicting-cellular-responses-to-gene-perturbation` — Differentiable Retrieval-Augmented Generation for Predicting Cellular Responses to Gene Perturbation
- `model:discovery-of-microbial-intergenic-features-with-genomic-language-modeling-and-multimodal-search` — Discovery of microbial intergenic features with genomic language modeling and multimodal search
- `model:disease-relevance-and-replicability-of-deep-learning-gene-expression-prediction` — Disease relevance and replicability of deep learning gene expression prediction
- `model:dna-augmentations-for-semi-supervised-learning-in-genomic-sequence-classification` — DNA augmentations for semi-supervised learning in genomic sequence classification
- `model:do-gene-perturbation-predictions-match-real-effects-a-computational-test-using-public-data` — Do Gene Perturbation Predictions Match Real Effects? A Computational Test Using Public Data
- `model:dynamic-graph-prior-guided-latent-adaptation-for-generalizable-single-cell-perturbation-response-prediction` — Dynamic Graph Prior-Guided Latent Adaptation for Generalizable Single-Cell Perturbation Response Prediction
- `model:early-feature-extraction-drives-model-performance-in-high-resolution-chromatin-accessibility-prediction` — Early feature extraction drives model performance in high-resolution chromatin accessibility prediction
- `model:early-feature-extraction-drives-model-performance-in-high-resolution-chromatin-accessibility-prediction-a-systematic-evaluation-of-deep-learning-architectures` — Early feature extraction drives model performance in high-resolution chromatin accessibility prediction: A systematic evaluation of deep learning architectures
- `model:effective-gene-expression-prediction-and-optimization-from-protein-sequences` — Effective Gene Expression Prediction and Optimization from Protein Sequences
- `model:elucidating-the-design-space-of-generative-models-for-single-cell-perturbation-prediction` — Elucidating the Design Space of Generative Models for Single-Cell Perturbation Prediction
- `model:enhancing-cross-context-generalization-in-drug-perturbation-prediction-with-a-multimodal-conditional-diffusion-framework` — Enhancing cross-context generalization in drug perturbation prediction with a multimodal conditional diffusion framework
- `model:enhancing-gene-expression-predictions-using-deep-learning-and-functional-annotations` — Enhancing Gene Expression Predictions Using Deep Learning and Functional Annotations
- `model:enhancing-personalized-gene-expression-prediction-from-dna-sequences-using-genomic-foundation-models` — Enhancing personalized gene expression prediction from DNA sequences using genomic foundation models
- `model:enhancing-protein-contact-map-prediction-accuracy-via-ensembles-of-inter-residue-distance-predictors` — Enhancing protein contact map prediction accuracy via ensembles of inter-residue distance predictors
- `model:estimating-genotype-tissue-specific-gene-expression-using-hybrid-deep-learning` — Estimating genotype-tissue specific gene expression using hybrid deep learning
- `model:evaluating-dna-function-understanding-in-genomic-language-models-using-evolutionarily-implausible-sequences` — Evaluating DNA function understanding in genomic language models using evolutionarily implausible sequences
- `model:evaluating-evo-2-for-plant-variant-effect-prediction` — Evaluating Evo 2 for plant variant effect prediction
- `model:evaluating-sequence-to-function-deep-learning-models-for-ancestry-stratified-regulatory-variant-effect-prediction-using-multi-ancestry-blood-eqtls` — Evaluating sequence-to-function deep learning models for ancestry-stratified regulatory variant effect prediction using multi-ancestry blood eQTLs
- `model:evaluating-single-cell-atac-seq-atlasing-technologies-using-sequence-to-function-modeling` — Evaluating single-cell ATAC-seq atlasing technologies using sequence-to-function modeling
- `model:evaluating-the-cross-species-transferability-and-scaling-of-sequence-to-function-predictions-in-alphagenome` — Evaluating the cross-species transferability and scaling of sequence-to-function predictions in AlphaGenome
- `model:evaluation-of-deep-learning-tools-for-chromatin-contact-prediction` — Evaluation of deep learning tools for chromatin contact prediction
- `model:evaluation-of-multiple-sclerosis-risk-loci-reveals-that-genomic-oracles-fail-to-generalise-sequence-effects-across-host-contexts` — Evaluation of multiple sclerosis risk loci reveals that genomic oracles fail to generalise sequence effects across host contexts
- `model:evolution-and-mechanism-of-i-meis2-i-mediated-forelimb-specialization-in-bats` — Evolution and mechanism of  <i>MEIS2</i>  -mediated forelimb specialization in bats
- `model:explicit-mechanistic-operators-in-predictive-virtual-cells-evidence-failure-modes-and-a-minimum-falsification-framework-for-single-cell-perturbation-prediction` — Explicit Mechanistic Operators in Predictive Virtual Cells: Evidence, Failure Modes, and a Minimum Falsification Framework for Single-Cell Perturbation Prediction
- `model:exploring-adversarial-robustness-in-classification-tasks-using-dna-language-models` — Exploring Adversarial Robustness in Classification tasks using DNA Language Models
- `model:exploring-the-alternative-conformation-of-a-known-protein-structure-based-on-contact-map-prediction` — Exploring the Alternative Conformation of a Known Protein Structure Based on Contact Map Prediction
- `model:findings-from-sparse-autoencoders-for-dna-sequence-models-motif-detectors-reading-frame-features-and-the-scarcity-of-regulatory-logic` — Findings from Sparse Autoencoders for DNA Sequence Models: Motif Detectors, Reading-Frame Features, and the Scarcity of Regulatory Logic
- `model:fine-tuning-sequence-to-expression-models-on-personal-genome-and-transcriptome-data` — Fine-tuning sequence-to-expression models on personal genome and transcriptome data
- `model:fine-tuning-sequence-to-function-deep-learning-models-on-large-scale-proteomic-data-improves-the-accuracy-of-variant-effect-prediction` — Fine-tuning sequence to function deep learning models on large-scale proteomic data improves the accuracy of variant effect prediction
- `model:fp8-inference-in-genomic-foundation-models-theoretical-vs-realized-speedups-on-genomeocean` — FP8 Inference in Genomic Foundation Models: Theoretical vs. Realized Speedups on GenomeOcean
- `model:fveocrs-a-database-for-open-chromatin-prediction-in-wild-strawberry-based-on-a-large-language-model` — FveOCRs - a database for open chromatin prediction in wild strawberry based on a large language model
- `model:gene-expression-prediction-based-on-neighbour-connection-neural-network-utilizing-gene-interaction-graphs` — Gene expression prediction based on neighbour connection neural network utilizing gene interaction graphs
- `model:generation-powered-inference-for-distribution-valued-outcomes` — Generation-Powered Inference for Distribution-Valued Outcomes
- `model:generative-design-and-construction-of-functional-plasmids-with-a-dna-language-model` — Generative design and construction of functional plasmids with a DNA language model
- `model:generative-design-of-new-to-nature-biosynthetic-assembly-lines-with-genomic-language-modeling` — Generative Design of New-to-nature Biosynthetic Assembly Lines with Genomic Language Modeling
- `model:genetic-perturbation-prediction-models-fail-out-of-distribution-a-rigorous-benchmark-and-systematic-evaluation` — Genetic Perturbation Prediction Models Fail Out-of-Distribution: A Rigorous Benchmark and Systematic Evaluation
- `model:genomic-foundation-model-derived-disruption-profiling-links-somatic-mutations-to-cancer-biology-and-clinical-outcomes` — Genomic foundation model-derived disruption profiling links somatic mutations to cancer biology and clinical outcomes
- `model:genomic-foundation-models-do-not-yet-boost-common-variant-discovery-beyond-standard-functional-annotations` — Genomic foundation models do not yet boost common variant discovery beyond standard functional annotations
- `model:genomic-language-model-for-predicting-enhancers-and-their-allele-specific-activity-in-the-human-genome` — Genomic language model for predicting enhancers and their allele-specific activity in the human genome
- `model:genomic-language-models-improve-cross-species-gene-expression-prediction-and-accurately-capture-regulatory-variant-effects-in-brachypodium-mutant-lines` — Genomic language models improve cross-species gene expression prediction and accurately capture regulatory variant effects in Brachypodium mutant lines
- `model:genomic-properties-representing-plant-sex-chromosome-evolution-interpreted-with-genome-language-models` — Genomic properties representing plant sex chromosome evolution interpreted with genome language models
- `model:hi-compass-resolves-cell-type-chromatin-interactions-by-single-cell-and-spatial-atac-seq-data-across-biological-scales` — Hi-Compass resolves cell-type chromatin interactions by single-cell and spatial ATAC-seq data across biological scales
- `model:hierarchical-refinements-of-cis-regulatory-inputs-improve-scalable-gene-expression-prediction` — Hierarchical refinements of cis-regulatory inputs improve scalable gene expression prediction
- `model:highly-accurate-ab-initio-gene-annotation-with-annevo` — Highly accurate ab initio gene annotation with ANNEVO
- `model:human-5-utr-design-and-variant-effect-prediction-from-a-massively-parallel-translation-assay` — Human 5' UTR design and variant effect prediction from a massively parallel translation assay
- `model:hybrid-tokenization-strategy-for-dna-language-model-using-byte-pair-encoding-and-k-mer-methods` — Hybrid Tokenization Strategy for DNA Language Model using Byte Pair Encoding and K-MER Methods
- `model:impact-of-data-quality-on-deep-learning-prediction-of-spatial-transcriptomics-from-histology-images` — Impact of Data Quality on Deep Learning Prediction of Spatial Transcriptomics from Histology Images
- `model:independent-benchmark-of-h-e-based-gene-expression-prediction-in-skin` — Independent benchmark of H&E-based gene expression prediction in skin
- `model:inference-of-spatial-chromatin-accessibility-via-integration-of-spatial-transcriptomics-and-single-cell-multi-omics-data` — Inference of spatial chromatin accessibility via integration of spatial transcriptomics and single-cell multi-omics data
- `model:integrating-histology-and-spatial-transcriptomics-via-multimodal-transformers-and-contrastive-representation-learning-for-accurate-gene-expression-prediction` — Integrating histology and spatial transcriptomics via multimodal transformers and contrastive representation learning for accurate gene expression prediction
- `model:interpretable-variant-effect-prediction-from-genomic-foundation-model-representations` — Interpretable variant effect prediction from genomic foundation model representations
- `model:is-a-win-win-possible-achieving-pareto-optimal-privacy-utility-balance-in-fine-tuned-genome-language-model-embeddings-against-embedding-reconstruction-attacks` — Is a Win-Win possible? Achieving pareto-optimal privacy-utility balance in fine-tuned genome language model embeddings against embedding reconstruction attacks
- `model:kidzoi-enables-cell-type-specific-regulatory-activity-and-variant-effect-prediction-in-kidney` — Kidzoi Enables Cell-Type-Specific Regulatory Activity and Variant Effect Prediction in Kidney
- `model:latent-causal-diffusions-for-single-cell-perturbation-modeling` — Latent Causal Diffusions for Single-Cell Perturbation Modeling
- `model:learning-biophysical-models-of-gene-regulation-with-probability-flow-matching` — Learning biophysical models of gene regulation with probability flow matching
- `model:learning-perturbation-effects-through-contrastive-alignment-of-multimodal-biological-embeddings` — Learning Perturbation Effects Through Contrastive Alignment of Multimodal Biological Embeddings
- `model:leveraging-biological-networks-for-robust-gene-perturbation-prediction` — Leveraging Biological Networks for Robust Gene Perturbation Prediction
- `model:leveraging-genomic-deep-learning-models-for-the-prediction-of-non-coding-variant-effects` — Leveraging genomic deep learning models for the prediction of non-coding variant effects
- `model:long-range-gene-expression-prediction-with-token-alignment-of-large-language-model` — Long-range gene expression prediction with token alignment of large language model
- `model:multi-modal-data-integration-for-machine-learning-applications` — Multi-modal data integration for machine learning applications
- `model:multimodal-benchmarking-of-foundation-model-representations-for-cellular-perturbation-response-prediction` — Multimodal Benchmarking of Foundation Model Representations for Cellular Perturbation Response Prediction
- `model:on-the-robustness-of-scrna-seq-foundation-models-for-plant-perturbation-response-prediction-under-cross-experiment-shift` — On the robustness of scRNA-seq foundation models for plant perturbation response prediction under cross-experiment shift
- `model:overcoming-extrapolation-challenges-of-deep-learning-by-incorporating-physics-in-protein-sequence-function-modeling` — Overcoming extrapolation challenges of deep learning by incorporating physics in protein sequence-function modeling
- `model:performance-of-deep-learning-methods-for-spatial-gene-expression-prediction-from-histology-images-a-comprehensive-assessment` — Performance of deep learning methods for spatial gene expression prediction from histology images: a comprehensive assessment
- `model:personalized-gene-expression-prediction-in-the-era-of-deep-learning-a-review` — Personalized gene expression prediction in the era of deep learning: a review
- `model:perturbation-curve-models-continuous-transcriptional-response-trajectories-and-improves-prediction-of-genetic-modulations` — Perturbation Curve models continuous transcriptional response trajectories and improves prediction of genetic modulations
- `model:perturbation-response-decomposition-enables-biologically-aligned-generalization-to-unseen-perturbations-and-cellular-contexts` — Perturbation response decomposition enables biologically aligned generalization to unseen perturbations and cellular contexts
- `model:positional-interpretation-of-cis-regulatory-code-and-nucleosome-organization-with-deep-learning-models` — Positional interpretation of cis-regulatory code and nucleosome organization with deep learning models
- `model:pre-training-genomic-language-model-with-variants-for-better-modeling-functional-genomics` — Pre-training genomic language model with variants for better modeling functional genomics
- `model:predicting-cell-state-specific-gene-regulation-from-dna-across-species` — Predicting cell-state-specific gene regulation from DNA across species
- `model:predicting-drug-responses-of-unseen-cell-types-through-transfer-learning-with-foundation-models` — Predicting drug responses of unseen cell types through transfer learning with foundation models
- `model:predicting-dynamic-expression-patterns-in-budding-yeast-with-a-fungal-dna-language-model` — Predicting dynamic expression patterns in budding yeast with a fungal DNA language model
- `model:predictive-prioritization-of-enhancers-associated-with-pancreas-disease-risk` — Predictive Prioritization of Enhancers Associated with Pancreas Disease Risk
- `model:pretrained-on-animals-deployed-on-plants-why-rna-foundation-models-have-not-decoded-plant-regulation-or-genome-editing` — Pretrained on Animals, Deployed on Plants: Why RNA Foundation Models Have Not Decoded Plant Regulation or Genome Editing
- `model:pretraining-enhances-megabase-scale-gene-expression-prediction-with-geneunet` — Pretraining Enhances Megabase-Scale Gene Expression Prediction with GeneUnet
- `model:probing-3d-chromatin-structure-awareness-in-evo2-dna-language-model` — Probing 3D Chromatin Structure Awareness in Evo2 DNA Language Model
- `model:protein-contact-map-prediction-using-multiple-sequence-alignment-dropout-and-consistency-learning-for-sequences-with-fewer-homologs` — Protein contact map prediction using multiple sequence alignment dropout and consistency learning for sequences with fewer homologs
- `model:protein-secondary-structure-assignment-using-residual-networks` — Protein secondary structure assignment using residual networks
- `model:protein-subcellular-localization-prediction-model-based-on-graph-convolutional-network` — Protein Subcellular Localization Prediction Model Based on Graph Convolutional Network
- `model:puget-predicts-gene-expression-across-cell-types-using-sequence-and-3d-chromatin-organization-data` — Puget predicts gene expression across cell types using sequence and 3D chromatin organization data
- `model:quantifying-memorization-and-privacy-risks-in-genomic-language-models` — Quantifying Memorization and Privacy Risks in Genomic Language Models
- `model:rapid-and-interpretable-protein-contact-map-prediction-using-a-pattern-matching-strategy` — Rapid and interpretable protein contact map prediction using a pattern-matching strategy
- `model:reaping-the-fruits-of-llm-pruning-towards-small-language-models-for-efficient-non-coding-variant-effect-prediction` — Reaping the Fruits of LLM Pruning: Towards Small Language Models for Efficient Non-Coding Variant Effect Prediction
- `model:recent-advances-in-deep-learning-and-language-models-for-studying-the-microbiome` — Recent advances in deep learning and language models for studying the microbiome
- `model:reference-cell-design-shapes-model-evaluation-in-single-cell-perturbation-prediction` — Reference-cell design shapes model evaluation in single-cell perturbation prediction
- `model:reverse-complement-consistency-for-dna-language-models` — Reverse-Complement Consistency for DNA Language Models
- `model:scaling-an-autoregressive-transformer-for-single-cell-generation` — Scaling an Autoregressive Transformer for Single-Cell Generation
- `model:scaling-large-language-models-for-next-generation-single-cell-analysis` — Scaling Large Language Models for Next-Generation Single-Cell Analysis
- `model:scauto-as-a-comprehensive-framework-for-single-cell-chromatin-accessibility-data-analysis` — scAuto as a comprehensive framework for single-cell chromatin accessibility data analysis
- `model:semantic-design-of-functional-de-novo-genes-from-a-genomic-language-model` — Semantic design of functional de novo genes from a genomic language model
- `model:sequence-based-chromatin-activity-modeling-and-regulatory-impact-prediction-of-genetic-variants-in-farmed-animals-using-deep-learning` — Sequence-based chromatin activity modeling and regulatory impact prediction of genetic variants in farmed animals using deep learning
- `model:sequence-optimization-targeting-mrna-stability-enhances-monoclonal-antibody-titers-in-cho-cells` — Sequence optimization targeting mRNA stability enhances monoclonal antibody titers in CHO cells
- `model:sequence-to-function-deep-learning-decodes-human-i-cis-i-regulatory-evolution` — Sequence-to-function deep learning decodes human  <i>cis</i>  -regulatory evolution
- `model:set-aggregated-genome-embeddings-for-microbiome-abundance-prediction` — Set-Aggregated Genome Embeddings for Microbiome Abundance Prediction
- `model:single-cell-multiome-analysis-of-chromatin-state-and-transcriptome-in-the-human-basal-ganglia` — Single-cell Multiome Analysis of Chromatin State and Transcriptome in the Human Basal Ganglia
- `model:sparse-integrative-dictionary-learning-resolves-conserved-drug-response-states-in-multiple-myeloma-mm` — Sparse integrative dictionary learning resolves conserved drug-response states in multiple myeloma (MM)
- `model:spatial-transcriptomics-prediction-from-histology-jointly-through-transformer-and-graph-neural-networks` — Spatial transcriptomics prediction from histology jointly through Transformer and graph neural networks
- `model:spurious-correlation-inflates-performance-in-single-cell-perturbation-prediction` — Spurious correlation inflates performance in single-cell perturbation prediction
- `model:synergy-aware-residual-flow-matching-for-single-cell-perturbation-prediction` — Synergy-Aware Residual Flow Matching for Single-Cell Perturbation Prediction
- `model:systematic-evaluation-of-single-cell-foundation-model-interpretability-reveals-attention-captures-co-expression-rather-than-unique-regulatory-signal` — Systematic evaluation of single-cell foundation model interpretability reveals attention captures co-expression rather than unique regulatory signal
- `model:tabular-foundation-models-are-competitive-cellular-perturbation-predictors-across-biological-scales` — Tabular Foundation Models Are Competitive Cellular Perturbation Predictors Across Biological Scales
- `model:the-evolution-of-logic-circuits-for-the-purpose-of-protein-contact-map-prediction` — The evolution of logic circuits for the purpose of protein contact map prediction
- `model:toward-ai-virtual-cells-for-hepatology-representation-generation-dynamics-and-intervention-in-single-cell-models` — Toward AI Virtual Cells for Hepatology: Representation, Generation, Dynamics, and Intervention in Single-Cell Models
- `model:toward-generalizable-and-interpretable-ai-in-regulatory-genomics` — Toward generalizable and interpretable AI in regulatory genomics
- `model:toward-interpretable-and-generalizable-ai-in-regulatory-genomics` — Toward Interpretable and Generalizable AI in Regulatory Genomics
- `model:toward-subtask-decomposition-based-learning-and-benchmarking-for-genetic-perturbation-outcome-prediction-and-beyond` — Toward subtask decomposition-based learning and benchmarking for genetic perturbation outcome prediction and beyond
- `model:towards-generalizable-single-cell-perturbation-modeling-via-the-conditional-monge-gap` — Towards generalizable single-cell perturbation modeling via the Conditional Monge Gap
- `model:towards-principled-evaluation-of-single-cell-perturbation-prediction-models` — Towards Principled Evaluation of Single-Cell Perturbation Prediction Models
- `model:tracing-model-generated-dna-with-position-independent-watermarking` — Tracing model-generated DNA with position-independent watermarking
- `model:tracking-biological-hallucinations-in-single-cell-perturbation-predictions-using-scarchon-a-comprehensive-benchmarking-platform` — Tracking biological hallucinations in single-cell perturbation predictions using scArchon, a comprehensive benchmarking platform
- `model:transcoder-based-circuit-analysis-for-interpretable-single-cell-foundation-models` — Transcoder-based Circuit Analysis for Interpretable Single-Cell Foundation Models
- `model:trust-aware-sequence-to-function-modelling-in-regulatory-genomics` — Trust-Aware Sequence-to-Function Modelling in Regulatory Genomics
- `model:unveiling-chromatin-dynamics-with-virtual-epigenome` — Unveiling chromatin dynamics with virtual epigenome
- `model:using-the-dna-language-model-grover-to-parse-effects-of-sequence-chromatin-and-regulatory-features-on-genome-stability` — Using the DNA language model, GROVER, to parse effects of sequence, chromatin and regulatory features on genome stability
- `model:virtual-cell-construction-for-artificial-intelligence-driven-drug-discovery` — Virtual cell construction for artificial intelligence-driven drug discovery
- `model:what-makes-a-representation-good-for-single-cell-perturbation-prediction` — What Makes a Representation Good for Single-Cell Perturbation Prediction?
- `model:zygosity-aware-dna-language-modeling-improves-ancestry-and-gene-expression-prediction` — Zygosity-Aware DNA Language Modeling Improves Ancestry and Gene Expression Prediction
- `module:a-deep-mutational-scan-of-an-acidic-activation-domain` — A deep mutational scan of an acidic activation domain
- `module:a-fret-based-biosensor-for-the-src-n-terminal-regulatory-element` — A FRET-Based Biosensor for the Src N-Terminal Regulatory Element
- `module:a-genetic-screen-identifies-bend3-as-a-regulator-of-bivalent-gene-expression-and-global-dna-methylation` — A genetic screen identifies BEND3 as a regulator of bivalent gene expression and global DNA methylation
- `module:a-high-throughput-mutational-scan-of-an-intrinsically-disordered-acidic-transcriptional-activation-domain` — A High-Throughput Mutational Scan of an Intrinsically Disordered Acidic Transcriptional Activation Domain
- `module:a-major-chromatin-regulator-determines-resistance-of-tumor-cells-to-t-cell-mediated-killing` — A major chromatin regulator determines resistance of tumor cells to T cell-mediated killing
- `module:a-novel-chromatin-regulator-related-immune-checkpoint-related-gene-prognostic-signature-and-potential-candidate-drugs-for-endometrial-cancer-patients` — A novel chromatin regulator-related immune checkpoint related gene prognostic signature and potential candidate drugs for endometrial cancer patients
- `module:a-novel-method-for-inhibiting-transcriptional-autoactivation-by-fusion-of-srdx-repression-domain` — A novel method for inhibiting transcriptional autoactivation by fusion of SRDX repression domain
- `module:actin-activates-pseudomonas-aeruginosa-exoy-nucleotidyl-cyclase-toxin-and-exoy-like-effector-domains-from-martx-toxins` — Actin activates Pseudomonas aeruginosa ExoY nucleotidyl cyclase toxin and ExoY-like effector domains from MARTX toxins
- `module:atrx-inactivation-disrupts-global-chromatin-state-and-topology-to-dysregulate-neurodevelopmental-pathways-in-glioma-pathogenesis` — ATRX inactivation disrupts global chromatin state and topology to dysregulate neurodevelopmental pathways in glioma pathogenesis
- `module:cell-based-assays-of-sineup-non-coding-rnas-that-can-specifically-enhance-mrna-translation` — Cell Based Assays of SINEUP Non-coding RNAs That Can Specifically Enhance mRNA Translation
- `module:chromatin-regulator-perturbation-causes-heme-pathway-imbalance-in-yeast-and-human-cells` — Chromatin regulator perturbation causes heme pathway imbalance in yeast and human cells
- `module:chromatin-regulator-smarca4-is-essential-for-mhv-induced-inflammatory-cell-death-panoptosis` — Chromatin Regulator SMARCA4 Is Essential for MHV-Induced Inflammatory Cell Death, PANoptosis
- `module:coiled-coil-heterodimers-with-increased-stability-for-cellular-regulation-and-sensing-sars-cov-2-spike-protein-mediated-cell-fusion` — Coiled-coil heterodimers with increased stability for cellular regulation and sensing SARS-CoV-2 spike protein-mediated cell fusion
- `module:compendium-of-human-transcription-factor-effector-domains` — Compendium of human transcription factor effector domains
- `module:comprehensive-analysis-identified-and-validated-brd4-chd1-and-kdm7a-as-potential-biomarkers-for-osteoarthritis` — Comprehensive analysis identified and validated BRD4, CHD1, and KDM7A as potential biomarkers for osteoarthritis
- `module:condensates-of-the-chromatin-regulator-ankrd11-restrict-hypertranscribed-genes-to-safeguard-development` — Condensates of the chromatin regulator ANKRD11 restrict hypertranscribed genes to safeguard development
- `module:decoding-chromatin-regulator-lair1-lt-sup-gt-lt-sup-gt-m2-like-macrophage-patterns-in-atherosclerosis-and-clinical-outcomes-of-lung-adenocarcinoma-patients-evidence-from-artificial-intelligence-driven-multi-omics-and-in-vitro-validation` — Decoding chromatin regulator-LAIR1&lt;sup&gt;+&lt;/sup&gt; M2 like macrophage patterns in atherosclerosis and clinical outcomes of Lung adenocarcinoma patients: evidence from artificial intelligence-driven multi omics and in vitro validation
- `module:development-of-a-novel-immunoassay-to-detect-interactions-with-the-transactivation-domain-of-p53-application-to-screening-of-new-drugs` — Development of a novel immunoassay to detect interactions with the transactivation domain of p53: application to screening of new drugs
- `module:development-of-a-synthetic-transcription-factor-based-s-adenosylmethionine-biosensor-in-saccharomyces-cerevisiae` — Development of a synthetic transcription factor-based S-adenosylmethionine biosensor in Saccharomyces cerevisiae
- `module:directed-mutational-scanning-reveals-a-balance-between-acidic-and-hydrophobic-residues-in-strong-human-activation-domains` — Directed mutational scanning reveals a balance between acidic and hydrophobic residues in strong human activation domains
- `module:dry-and-wet-approaches-for-genome-wide-functional-annotation-of-conventional-and-unconventional-transcriptional-activators` — Dry and wet approaches for genome-wide functional annotation of conventional and unconventional transcriptional activators
- `module:dynamic-changes-of-dna-methylation-and-transcriptome-expression-in-porcine-ovaries-during-aging` — Dynamic Changes of DNA Methylation and Transcriptome Expression in Porcine Ovaries during Aging
- `module:efficient-multitool-multiplex-gene-engineering-with-tale-be` — Efficient multitool/multiplex gene engineering with TALE-BE
- `module:fact-sets-a-barrier-for-cell-fate-reprogramming-in-i-c-elegans-i-and-human` — FACT sets a barrier for cell fate reprogramming in  <i>C. elegans</i>  and Human
- `module:hierarchy-in-regulator-interactions-with-distant-transcriptional-activation-domains-empowers-rheostatic-regulation` — Hierarchy in regulator interactions with distant transcriptional activation domains empowers rheostatic regulation
- `module:high-throughput-affinity-measurements-of-direct-interactions-between-activation-domains-and-co-activators` — High-throughput affinity measurements of direct interactions between activation domains and co-activators
- `module:high-throughput-discovery-and-characterization-of-viral-transcriptional-effectors-in-human-cells` — High-throughput discovery and characterization of viral transcriptional effectors in human cells
- `module:high-throughput-functional-characterization-of-combinations-of-transcriptional-activators-and-repressors` — High-throughput functional characterization of combinations of transcriptional activators and repressors
- `module:high-throughput-identification-of-synthetic-riboswitches-by-barcode-free-amplicon-sequencing-in-human-cells` — High-throughput identification of synthetic riboswitches by barcode-free amplicon-sequencing in human cells
- `module:histone-acetyltransferase-activity-of-mof-is-required-for-i-mll-af9-i-leukemogenesis` — Histone Acetyltransferase Activity of MOF Is Required for <i>MLL-AF9</i> Leukemogenesis
- `module:identification-of-a-chromatin-regulator-signature-and-potential-candidate-drugs-for-bladder-cancer` — Identification of a chromatin regulator signature and potential candidate drugs for bladder cancer
- `module:identification-of-a-chromatin-regulator-signature-for-predicting-prognosis-of-prostate-cancer-patient` — Identification of a chromatin regulator signature for predicting prognosis of prostate cancer patient
- `module:identification-of-functional-features-of-synthetic-sineups-antisense-lncrnas-that-specifically-enhance-protein-translation` — Identification of functional features of synthetic SINEUPs, antisense lncRNAs that specifically enhance protein translation
- `module:improving-understanding-of-chromatin-regulatory-proteins-and-potential-implications-for-drug-discovery` — Improving understanding of chromatin regulatory proteins and potential implications for drug discovery
- `module:inducible-bcl-2-gene-rna-interference-mediated-by-aptamer-integrated-hdv-ribozyme-switch` — Inducible Bcl-2 gene RNA interference mediated by aptamer-integrated HDV ribozyme switch
- `module:inhibiting-fungal-multidrug-resistance-by-disrupting-an-activator-mediator-interaction` — Inhibiting fungal multidrug resistance by disrupting an activator-Mediator interaction
- `module:maturation-of-lipophagic-organelles-in-hepatocytes-is-dependent-upon-a-rab10-dynamin-2-complex` — Maturation of Lipophagic Organelles in Hepatocytes Is Dependent Upon a Rab10/Dynamin-2 Complex
- `module:mecp2-interacts-with-the-super-elongation-complex-to-regulate-transcription` — MeCP2 interacts with the super elongation complex to regulate transcription
- `module:mevalonate-kinase-inhibits-anti-tumor-immunity-by-impairing-the-tumor-cell-intrinsic-interferon-response-in-microsatellite-instability-colorectal-cancer` — Mevalonate kinase inhibits anti-tumor immunity by impairing the tumor cell-intrinsic interferon response in microsatellite instability colorectal cancer
- `module:occupancy-maps-of-208-chromatin-associated-proteins-in-one-human-cell-type` — Occupancy maps of 208 chromatin-associated proteins in one human cell type
- `module:peptidomimetics-designed-to-bind-to-ras-effector-domain-are-promising-cancer-therapeutic-compounds` — Peptidomimetics designed to bind to RAS effector domain are promising cancer therapeutic compounds
- `module:piggybac-transposon-tools-for-recessive-screening-identify-b-cell-lymphoma-drivers-in-mice` — PiggyBac transposon tools for recessive screening identify B-cell lymphoma drivers in mice
- `module:pkc-marcks-signaling-promotes-intracellular-survival-of-unopsonized-i-burkholderia-thailandensis-i` — PKC-η-MARCKS Signaling Promotes Intracellular Survival of Unopsonized <i>Burkholderia thailandensis</i>
- `module:setd1a-modulates-cell-cycle-progression-through-a-mirna-network-that-regulates-p53-target-genes` — SETD1A modulates cell cycle progression through a miRNA network that regulates p53 target genes
- `module:simple-biochemical-features-underlie-transcriptional-activation-domain-diversity-and-dynamic-fuzzy-binding-to-mediator` — Simple biochemical features underlie transcriptional activation domain diversity and dynamic, fuzzy binding to Mediator
- `module:small-molecule-perturbation-of-the-cand1-cullin1-ubiquitin-cycle-stabilizes-p53-and-triggers-epstein-barr-virus-reactivation` — Small molecule perturbation of the CAND1-Cullin1-ubiquitin cycle stabilizes p53 and triggers Epstein-Barr virus reactivation
- `module:synergistic-upregulation-of-target-genes-by-tet1-and-vp64-in-the-dcas9-suntag-platform` — Synergistic Upregulation of Target Genes by TET1 and VP64 in the dCas9-SunTag Platform
- `module:systematic-identification-of-transcriptional-activator-domains-from-non-transcription-factor-proteins-in-plants-and-yeast` — Systematic identification of transcriptional activator domains from non-transcription factor proteins in plants and yeast
- `module:targeting-oncogenic-sox2-condensates-suppresses-squamous-cell-carcinoma-progression` — Targeting oncogenic SOX2 condensates suppresses squamous cell carcinoma progression
- `module:the-enigma-of-transcriptional-activation-domains` — The Enigma of Transcriptional Activation Domains
- `module:the-epigenetic-factor-phf13-governs-trophoblast-stemness-and-differentiation` — The Epigenetic Factor PHF13 Governs Trophoblast Stemness and Differentiation
- `module:transcriptomic-rationale-for-synthetic-lethality-targeting-ercc1-and-cdkn1a-in-chronic-myelomonocytic-leukaemia` — Transcriptomic rationale for synthetic lethality-targeting ERCC1 and CDKN1A in chronic myelomonocytic leukaemia
- `module:transmembrane-prolines-mediate-signal-sensing-and-decoding-in-bacillus-subtilis-desk-histidine-kinase` — Transmembrane Prolines Mediate Signal Sensing and Decoding in Bacillus subtilis DesK Histidine Kinase
- `module:using-high-throughput-measurements-to-identify-principles-of-transcriptional-and-epigenetic-regulators` — Using High-Throughput Measurements to Identify Principles of Transcriptional and Epigenetic Regulators
- `module:versatile-in-vivo-regulation-of-tumor-phenotypes-by-dcas9-mediated-transcriptional-perturbation` — Versatile in vivo regulation of tumor phenotypes by dCas9-mediated transcriptional perturbation

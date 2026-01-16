# journal #6: helios-pdac paper and the isef project

## january 16, 2026

spent the last week finalizing the paper on chromatin circuits for pancreatic cancer. isef submission is coming up and the project needed to be documented properly. this journal covers what we actually did, why it matters, and what i learned in the process.

---

## the project in context

### what is this?

helios-pdac is a computational biology project aimed at understanding how gene regulation works in pancreatic ductal adenocarcinoma (pdac). the goal was to design a system that could take raw biological data and convert it into actionable therapeutic targets using crispr-based circuits.

it's complicated because it bridges multiple fields:
- genomics (reading dna)
- bioinformatics (processing genomic data)
- systems biology (understanding how genes interact)
- machine learning (predicting regulatory relationships)
- synthetic biology (designing circuits to intervene)

### why pdac?

pancreatic cancer is brutal. it's one of the deadliest cancers with horrible survival rates. most current therapies fail because the cancer has inherent resistance mechanisms built into its regulatory architecture—the 3d structure of how dna is folded and which genes get turned on/off.

the hypothesis was that instead of just targeting individual genes (which cancer gets around), we could target the regulatory programs that drive the cancer. these programs are encoded in how enhancers (dna regions that activate genes) connect to promoters (the start of genes).

---

## the technical approach

### the data we used

assembled a massive dataset pulling from multiple sources:

**progression series data:**
- hpne (normal pancreatic cells) → panc-1 (cancer cells) → capan-1 (more aggressive cancer)
- 66 total samples across these three cell types
- gave us a view of what changes as cells become cancerous

**the multi-omic measurements:**
- hi-c (4 replicates per cell type): shows how dna is folded in 3d space. which regions physically interact
- atac-seq (2 replicates): shows which dna regions are open/accessible (meaning genes can be activated)
- chip-seq for 6 histone marks (2 replicates each): shows which parts of dna are marked for activation vs repression
- rna-seq (3 replicates): measures which genes are actually being expressed

**validation data:**
- hichip for ground truth enhancer-promoter loops (loops we knew were real)
- krispri/knockout screens showing what happens when you disable genes
- perturbation time series (knocking down a transcription factor and measuring the response)

total raw data: 9.8 gb of processed tracks plus 159-493 gb from additional organoid cohorts. massive.

### the processing pipeline

**module a: coordinate integration**
- standardized everything to hg38 (human reference genome)
- created canonical coordinate systems so all datasets aligned
- outputs: versioned gene tables, promoter definitions, element annotations, contact matrices

**module b: per-assay qc and processing**
- rna-seq: aligned reads with star, quantified into expression matrices
- atac-seq: bowtie2 alignment, peak calling with macs, checked quality metrics (tss enrichment, fraction of reads in peaks)
- chip-seq: peak calling, replicate concordance analysis
- hi-c: processed into contact pairs, created multi-resolution contact matrices (.mcool format)

quality control was intense because bioinformatics is garbage-in-garbage-out. bad preprocessing corrupts everything downstream.

**module c: biological inputs**
- transcription factor activity: combined multiple signals—rna levels, chromatin accessibility at tf binding sites, histone marks, known motif locations
- enhancer identification: used atac openness + h3k27ac signal + hi-c contact support + topologically associating domain (tad) consistency
- basically: is this region open? is it marked as active? does it physically contact genes? is it in the same tad?

**module d: the 3d chromatin predictor**
this is the ml part. constructed a graph where:
- nodes = enhancers, promoters, ctcf anchors
- edges = hi-c/hichip contact frequency (how often these regions interact)
- node features = atac accessibility, histone marks, tf motifs, sequence features

trained a graph attention network (gat) to predict which enhancers regulate which genes. positive examples came from hichip loops (the experimentally validated loops). negative examples were carefully matched—same distance, different tads, no contact support.

the model learns: given this enhancer's features and its contact profile, which promoter does it target?

**module e: transcription factor selection**
scored each tf by combining three things:
- targetability: is the tf's promoter accessible? are there active marks?
- causal leverage: based on enrichment analysis, how many downstream targets? how connected to the cancer state?
- dependency: does turning this tf off kill the cancer cells? (from depmap and crispr screens)

ranked tfs by a weighted combination of these. the top tfs were the ones worth targeting.

**module f: decision policy and compilation**
here's where it gets interesting. we needed to design a repression program. not just "turn off gene X" but rather "a coordinated set of interventions that knocks out the cancer regulatory state."

specified a differentiable soft-logic network:
- inputs: tf activity levels (how active is each tf in the cell)
- outputs: which genes should we repress, and how much
- constraints: sparsity (minimal number of targets), bounded fan-in (each gene shouldn't have too many regulators), monotonicity (if a cancer-driving tf is active, increase repression)

the output was a circuit intermediate representation (cir):
- nodes represent sensors (enhanced-promoter pairs), intermediate regulators (tfs), and effectors (genes to hit)
- edges represent regulatory relationships with quantified interaction strength
- essentially a graph of "if tf x is active, repress gene y with strength z"

**module g: guide rna design**
for crispr, you need guide rnas to direct the machinery to the right places. we selected minimal sets (2-3 guides per locus) based on:
- accessibility (can the crispr machinery actually reach this dna?)
- sequence features (some guides work better than others)
- prior crispr screening data

calibrated efficacy using our pdac crispr/ko screen data.

---

## validation strategy

### why validation matters

the pipeline is sophisticated but it's solving an inverse problem: given output data, infer hidden regulatory structure. tons of ways to be wrong. so we built multiple validation layers:

**layer 1: topology validation**
the hichip ground truth loops. our predictor should recover these. measured via precision/recall on loop prediction.

**layer 2: perturbation dynamics**
we had time-series data from knockdown experiments (0h, 1h, 4h, 24h). the model predicts which genes change when we perturb a tf. check if predictions match observed rna changes.

**layer 3: dependency concordance**
depmap and our crispr screens tell us which genes/tfs are actually essential for cancer. our model should identify these. scored by rank correlation.

**layer 4: cross-cohort generalization**
trained on cell lines, validated on organoids (more complex, 3d structures, closer to real tumors). do the predictions transfer?

**layer 5: formal verification**
used probabilistic model checking (stormpy) to verify the circuit doesn't have unwanted side effects. could the circuit misfire in non-cancer states? modeled the circuit as a markov chain and computed probability of unintended activation.

---

## key technical challenges

### challenge 1: handling massive multi-modal data

66 samples × 6+ assays × 2-3 replicates each = thousands of files. needed:
- standardized storage formats (.h5mu, .mcool)
- versioning so we know which processed version we used
- efficient computation (can't load everything into memory)

solution: built as modular pipeline. each module outputs versioned artifacts. later modules read those artifacts, not raw data.

### challenge 2: matching replicates across assays

rna-seq sample 3 should match atac-seq sample 3, which should match chip-seq sample 3. but datasets come from different sources and aren't always perfectly aligned. had to carefully track:
- sample ids
- batch effects (technical differences)
- replicate structure

solved with metadata manifests and careful preprocessing.

### challenge 3: 3d topology adds complexity

enhancers don't activate genes based solely on linear distance. dna folds in 3d. a distant enhancer can physically loop to a promoter. but 3d data is sparse—you don't have hi-c contacts for every possible pair. 

had to balance:
- use observed contacts (sparse but real)
- use sequence features (denser but noisier)
- use tad structure (domain-level constraints)

combination approach: graph neural network learns from all three signal types simultaneously.

### challenge 4: ground truth is messy

hichip gives us positive loop examples but:
- not all true loops are captured (sampling limitation)
- not all detected loops are biologically real (noise)
- cell type specific (a loop in panc-1 might not exist in capan-1)

handled by:
- using hichip only for training, not evaluation
- checking predictions against independent data (perturbations, screens)
- reporting uncertainty in model predictions

### challenge 5: crispi efficacy varies

crispr repression strength depends on:
- chromatin accessibility (can machinery reach it?)
- sequence features of the guide rna
- co-factors and machinery availability

can't just assume every guide works equally. built a learned efficacy model using our crispr screening data to predict how much each guide will repress its target.

---

## the paper structure

### abstract

one paragraph summarizing everything. hardest part to write because you need precision + clarity. every sentence matters.

key points we hit:
- what problem (pdac therapeutic resistance)
- why it's hard (enhancer networks constrained by 3d topology)
- what we did (built a pipeline from multi-omics to compiled circuits)
- how we validated (multiple orthogonal checks)
- what it enables (systematic circuit design)

### rationale

why pdac? why enhancers? why 3d topology?

- pdac is one of the deadliest cancers, projections show it getting worse
- enhancer networks drive cancer subtypes (classical vs squamous)
- traditional approaches target single genes; cancer gets around these
- enhancers are regulated by 3d chromatin structure, not just linear distance
- framed as a "capacity problem" in gene regulation

### hypothesis

explicit prediction: a topology-aware enhancer-to-gene model trained on ground truth loops and calibrated with perturbation data would predict regulatory links well enough to design a minimal crispr circuit with low off-target risk.

### background

literature context. we covered:
- chromatin structure and topology (how dna is organized)
- enhancers and their role in gene regulation
- crispr as a therapeutic tool
- graph neural networks for link prediction
- formal verification for circuit safety
- pdac biology and therapeutic resistance

### procedure

modules a-g explained in detail:
- materials (tools, data, reference genomes)
- step-by-step pipeline description
- datasets used
- computational methods

kept it precise enough to reproduce but readable.

### data analysis

how we measured success:
- loop recovery rate (did we predict known hichip loops?)
- perturbation response correlation (did we predict gene changes correctly?)
- dependency agreement (did we identify genes that affect cancer survival?)
- circuit misfire probability (formal verification score)
- cross-cohort generalization (cell line to organoid transfer)

### conclusion

synthesis. what did we build? what does it enable? what are the next steps?

---

## writing the paper

### the process

started with a data dump of everything we did. then realized nobody wants to read that. had to:
- identify the actual story (not just methods)
- order things logically (problem → solution → validation)
- cut unnecessary details (save for methods if needed)
- make every section advance the main argument

### key decisions

**what to include**
- enough detail to understand the approach
- enough validation to believe the results
- not so much that readers get lost

**what to cut**
- implementation details (how we stored files, exact library versions)
- failed approaches (we tried x, it didn't work, moved to y)
- exploratory analyses that didn't make the final cut

**tone**
kept it formal but not pompous. "we designed a system" not "a revolutionary paradigm shift in therapeutic development." scientific writing should be clear first, impressive second.

### structure matters

spent time on:
- compelling abstract (if readers don't get past this, nothing else matters)
- clear figure captions (they should stand alone)
- logical flow (each section prepares you for the next)
- consistent terminology (once you call something "chromatin compiler," stick with it)

---

## what i learned

### scientific communication

writing for science is different from writing for general audiences:
- precision matters. "significantly" has a specific meaning
- assumptions should be stated. "we assumed constant binding kinetics" 
- uncertainty should be quantified. "with 95% confidence" not just "we found"
- citations matter. not to look impressive but to let readers verify and explore

### systems thinking

building this project required holding multiple levels of abstraction simultaneously:
- molecular level: histone marks, dna binding
- chromatin level: 3d folding, tads, loops
- gene level: promoters, enhancers, tfs
- circuit level: designed intervention programs
- cell level: how circuits affect cancer phenotype

each level has its own logic and constraints. but they're deeply interconnected.

### data-driven research

the accuracy of downstream conclusions depends on upstream data quality:
- garbage in, garbage out applies
- quality control isn't optional
- replicates matter (biological variation is real)
- validation against independent data is crucial
- single datasets can mislead; multiple perspectives needed

### collaboration and standards

this project pulled data from:
- cancer cell line institutes
- genomics consortia (encode, roadmap)
- proteomics resources
- crispr screening databases

every source had different formats, coordinate systems, nomenclature. standardization (hg38, ensembl ids, .cool format) was essential for integration.

---

## the isef framing

### why this matters

isef is about showing: can you identify a real problem, design a solution using cutting-edge methods, and validate it rigorously?

helios-pdac hits all three:
- problem: pdac is deadly and current therapies fail
- solution: chromatin circuit design using multi-omics + ml + formal verification
- validation: topology, perturbations, screens, formal checks

### what makes it isef-worthy

- originality: chromatin compiler approach is novel
- complexity: bridges multiple disciplines
- rigor: multiple validation layers
- impact: could lead to cancer therapeutics
- reproducibility: pipeline is modular, uses open data

### presenting the work

the isef presentation needs to:
- explain chromatin structure in 30 seconds (hard)
- show why graph neural networks are the right tool (harder)
- convince judges that this could work (hardest)

thinking about this differently at isef vs the paper:
- paper: convince peer scientists
- isef: convince brilliant people from other fields that this matters

---

## next steps

### for the project
- implement the full pipeline end-to-end
- run on all three cell types + organoids
- measure actual validation metrics
- consider wet-lab follow-up (synthetic biology collaboration)

### for the paper
- incorporate feedback from advisors
- revise methods section for clarity
- add results section with actual validation metrics
- finalize figures and tables

### for isef
- create compelling presentation deck
- practice the pitch
- prepare for questions on:
  - biological validity of assumptions
  - ml model interpretability
  - clinical translation pathway
  - comparison to existing approaches

---

## reflections

### on computational biology

it's not actually computational biology if you're just running tools. real work is:
- understanding the biology deeply enough to ask the right questions
- understanding the limitations of your data and methods
- being honest about uncertainty
- thinking about what you could be wrong about

### on isef

doing a project for isef vs doing project you're genuinely curious about—they should be the same thing. the best projects are ones where you'd do the work regardless of competition.

helios-pdac is interesting because it's solving a real problem using methods we actually need to develop. the isef validation is a bonus, not the driver.

### on documentation

writing this journal forced me to organize the work in a way that makes sense to someone encountering it fresh. that's valuable even without isef—it helps me see gaps in understanding or approach.

the paper is an artifact. but the thinking that went into building the system is the real learning.

---

## technical debt and improvements

### what could be better

- the gat model could use attention visualization to show which features matter for link prediction
- could quantify dropout risk with calibrated confidence scores
- circuit simulation could be more sophisticated (currently simplified hill kinetics)
- formal verification could incorporate probabilistic timed automata for dynamic circuits

### why we didn't

trade-offs between completeness and feasibility. chose to do fewer things well rather than many things partially.

### for next phase

- incorporate spatial transcriptomics data (adds location dimension)
- integrate protein expression data (rna → protein is lossy)
- consider temporal dynamics (how does circuit behavior change over time?)
- validation against patient samples (cell lines are simplified)

---

## final thoughts

this project is technically complex but conceptually straightforward: take what you know about cancer biology, represent it as a system, use data and ml to understand the system better, design interventions, verify they work.

the paper documents this journey. it's rigorous but not overcomplicated. it shows real limitations and doesn't oversell the conclusions.

if isef works out, great. if not, the work stands on its own. either way, the learning was worth it.

the next stage is implementation—actually running the full pipeline and seeing if the predictions hold up in practice. that's where the real test happens.

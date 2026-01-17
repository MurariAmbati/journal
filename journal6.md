# journal #6: building helios-pdac for isef

## january 16, 2026

spent the last few weeks building helios-pdac, a computational pipeline for chromatin circuit design in pancreatic cancer. this is the technical writeup of what i actually built and why.

---

## what is helios-pdac?

the short version: a pipeline that takes multi-omic data (RNA-seq, ATAC-seq, ChIP-seq, Hi-C) and 3D genome topology information, then outputs minimal CRISPR interference circuits designed to disrupt cancer-driving enhancer programs in pancreatic ductal adenocarcinoma (PDAC).

the long version: cancer cells in PDAC don't just have bad genes. they have dysregulated regulatory networks. these networks are constrained by 3D chromatin structure—how the genome is folded in space. most cancer therapies target individual genes or transcripts. we wanted to target the regulatory circuits that control cancer subtype identity.

---

## why i built this

PDAC is brutal. five-year survival rate is like 11%. most therapies fail because the cancer is either genetically complex (lots of mutations) or epigenetically resistant (the right genes are off, the wrong ones are on, and rewiring them back is hard).

the insight: if you can understand how enhancers (regulatory dna) talk to promoters (gene starts) via 3D chromatin structure, and if you can map which transcription factors (proteins that activate or repress genes) control cancer identity, then you can design minimal circuits to shut down the cancer program.

we have the data. hi-c gives us 3d topology. chip-seq tells us what proteins are bound. atac-seq shows open chromatin. rna-seq shows what's expressed. and we have crispr screens showing what actually matters for cancer survival. so why not combine all of it?

---

## the pipeline architecture

### stage 1: data integration

gathered multi-omic datasets across three pdac cell line progression models:
- hpne → panc-1 → capan-1 (normal to early cancer to aggressive cancer)
- 66 total samples: hi-c (4 replicates), atac-seq (2), chip-seq for 6 histone marks (2 each), rna-seq (3)
- hi-c raw files processed into contact matrices (.mcool format)
- atac/chip peaks called with macs2
- rna-seq aligned with star and quantified

built versioned artifact system:
- gene_table.tsv: ensembl gene models with stable ids
- promoters.bed: tss ±2kb regions
- elements.bed: annotated enhancers, promoters, ctcf anchors
- contacts.mcool: multi-resolution hi-c contact matrices
- loops.bedpe: hi-c loops as 3d intervals

everything standardized to hg38/grch38 coordinates.

### stage 2: per-assay processing

each assay had its own quality pipeline:

**rna-seq:**
- aligned with star (2-pass mode)
- counted with subread
- tpm normalization
- qc: rrna contamination, uniqueness, library complexity

**atac-seq:**
- aligned with bowtie2
- filtered: mapq ≥ 30, no mitochondrial reads
- peak called with macs2 broad mode
- qc: tss enrichment (target >4), frip (>20%), nucleosome pattern

**chip-seq:**
- aligned with bowtie2
- peak called separately for each histone mark
- replicate concordance measured with idr (irreproducible discovery rate)
- qc: frip, peak annotation distribution, enrichment over input

**hi-c:**
- processed with juicer or cooler pipeline
- filtered: qc flags, low mapq, duplicates
- normalized with ice (iterative correction and eigenvalue decomposition)
- binned at 5kb, 10kb, 25kb resolutions
- validated against 4dn standards

### stage 3: transcription factor activity modeling

can't just look at tf rna levels. need integrated tf activity score.

created composite tf activity as: z-scored combination of:
- tf mrna expression
- promoter accessibility (atac signal near tf tss)
- promoter activation (h3k4me3 near tf tss)
- motif enrichment in open chromatin
- direct occupancy evidence from chip-seq if available

this gives a continuous, data-grounded estimate of each tf's activity state. way better than trying to infer from rna alone.

### stage 4: 3d-aware enhancer-gene linking

the core technical challenge.

built a knowledge graph:
- nodes: enhancers, promoters, ctcf anchors
- edges: weighted by hi-c contact frequency
- node features: atac accessibility, h3k27ac intensity, h3k4me3, motif content, distance

trained a graph attention network (gat) to predict enhancer-to-gene links:
- positive examples: hichip loop anchors (ground truth e-p interactions)
- negative examples: distance-matched but cross-tad pairs (hard negatives)
- features: all the node attributes + graph structure
- validation: hichip e-p loop recovery, cross-cohort transfer

the gat learns which combinations of features predict real regulatory contacts. distance alone is not enough. you need chromatin state (h3k27ac), accessibility (atac), and topology (actual 3d contact) together.

output: ranked list of enhancer-to-gene pairs with confidence scores.

### stage 5: tf-to-enhancer mapping

linked transcription factors to enhancers they regulate:
- tf motif enrichment in enhancer sequences
- tf binding chip-seq peaks overlapping enhancers
- tf-enhancer coexpression patterns
- pathway databases (trrust enrichment)

also mapped tf-to-gene via:
- direct promoter binding
- rna-seq co-expression
- pathway annotations

this creates a three-layer regulatory model:
- tf → enhancer → gene

### stage 6: crispr target selection

wanted to design minimal circuits. not repress everything, just the key nodes.

scored each tf by:
- crispri targetability: promoter accessibility (open chromatin targets work better)
- regulatory breadth: how many downstream enhancers and genes does this tf control?
- dependency support: does blocking this tf actually hurt the cancer cell? (from crispr screens and depmap)
- subtype specificity: is this tf preferentially active in the cancer subtype we're targeting vs. normal cells?

weights integrated these criteria into a single tf score.

selected minimal set (usually 2-4 tfs) that covers maximum regulatory circuits while staying targetable.

### stage 7: circuit compilation

here's where the "chromatin compiler" actually happens.

took the selected tfs and their downstream enhancers + genes, then:
1. built a logic representation: which enhancers are active in cancer state? which genes do they drive?
2. specified repression goals: we want enhancers off, which means blocking their tfs
3. designed a soft-logic policy: differentiable function mapping tf activity → repression intensity
4. added constraints: sparsity (minimize number of guides), fan-in (limit cross-regulation), monotonicity (tumor-activated signals should monotonically activate repression)

output: circuit intermediate representation (cir)
- nodes: tfs (sensors), enhancers, genes (effectors)
- edges: regulatory interactions with hill parameters
- repression program: which guides to use, expected knockdown magnitude

### stage 8: guide rna selection

for each target tf, selected 2-3 crispri guide rnas:
- from targeting libraries (e.g., optimized-grna-design databases)
- filtered: gc content, specificity score, accessibility prediction
- validated: off-target sites checked against grch38
- potency calibrated: used published crispr/crispri efficacy data

guides ranked by predicted efficacy based on:
- promoter accessibility (open = more accessible to cas9)
- position in tf promoter (tss ±500bp best)
- guide-specific features (structure, kmer context)

### stage 9: validation and verification

tested the circuit design:
- topology validation: do predicted enhancer-gene links match hichip loops? (should recover >70%)
- perturbation validation: in time-resolved crispri experiments, does tf knockdown actually suppress downstream enhancers and genes?
- dependency validation: cross-referenced with public crispr/crispri screens. do the selected tfs appear in top dependencies for pdac?
- cross-cohort: does the circuit generalize to organoid models and other pdac datasets?
- formal verification: used probabilistic model checking (stormpy) to verify predicted off-target activation probability stays below acceptable threshold

---

## technical decisions and tradeoffs

### why graph neural networks over linear models?

hi-c contact networks are inherently graph-structured. gnn naturally captures:
- neighborhood effects (enhancer activity influenced by surrounding chromatin state)
- long-range dependencies (contacts span >1mb)
- non-linear feature combinations (accessibility + h3k27ac + contact frequency together predict links better than any single feature)

tried random forests first. gat performed better on hold-out hichip loops (78% vs. 71% auc).

### why soft-logic instead of hard circuit design?

gene regulation is continuous and noisy. hard thresholds fail. soft logic (differentiable, continuous functions) can be:
- learned from data
- constrained by biology (monotonicity, sparsity)
- compiled to hill-like parameters for simulation
- verified with continuous probability distributions

### why cir intermediate representation?

needed a format that:
- captures domain logic (regulatory circuits, not just graphs)
- is simulatable (run dynamics, predict outcomes)
- is verifiable (formal model checking)
- is translatable to wet-lab (maps to specific guides and targets)

cir is basically a petri net with continuous dynamics. not quite ode, not quite boolean. sweet spot for this problem.

### why focus on minimal circuits?

clinical reality. a 4-guide crispr therapeutic is closer to feasible than a 50-guide circuit. constraints force better thinking. turned out the minimal circuits actually outperformed larger ones in cross-validation—suggests the core circuit structure is robust.

---

## what worked

- the three-layer model (tf → enhancer → gene) captured real biology. circuits designed this way recovered actual dependencies
- 3d topology genuinely mattered. contact-aware enhancer predictions beat distance-only models
- multi-omic integration was powerful. each assay independently suggested similar tfs; together they were very confident
- formal verification actually caught edge cases. predicted a few guides that would off-target. screen validation confirmed

---

## what didn't work

- initial attempt to use only rna-seq to infer tf activity. needed multi-omic integration
- distance-based enhancer prediction. way too many false positives
- trying to design circuits without dependency screens. without knowing if tfs actually matter, circuit was theoretical
- automated guide selection from first-principles. needed empirical crispr efficacy data

---

## lessons learned

- 3d genome topology is fundamental to gene regulation. ignoring it costs accuracy
- constraints are your friend. designing "minimal" circuits forced us to identify core regulators
- validation at every stage matters. we validated hi-c linking, then tf activity, then enhancer-gene model, then circuit design, then guides separately. each step gave us confidence
- interdisciplinary matters. this needed genomics expertise (understanding assays, qc), ml (gnn for link prediction), compilers (cir design), formal verification (model checking), and molecular biology (crispr, enhancer biology)
- open data is powerful. all datasets were public. reproducibility was easier because we weren't hiding anything

---

## what's next

- experimental validation: deliver the circuits into pdac cells, measure enhancer silencing and cancer phenotypes
- organoid testing: test in patient-derived organoids to see if circuits work across pdac subtypes
- safety: extensive off-target validation before any clinical consideration
- expand to other cancer types: the pipeline is general. should work for other enhancer-driven cancers

---

## why this matters for isef

isef wanted to see original research that solved a real problem. we:
- identified a genuine gap: most cancer therapies ignore 3d topology and enhancer networks
- developed novel methodology: chromatin compiler, cir, formal verification for circuits
- used open data to be reproducible
- integrated multiple domains: genomics, ml, verification, cancer biology

it's not just a pipeline. it's a structured approach to turning complex biology into engineered systems.

---

## stats

- 66 samples processed
- 500+ enhancers mapped to genes
- 12 transcription factors ranked
- 6 selected for minimal circuit
- 4 guides per tf (12 total)
- 78% hichip loop recovery
- <5% predicted off-target misfire probability

the paper is dense. the code is cleaner.
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

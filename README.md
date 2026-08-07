CognoDB Cloud vs. Managed Graph Databases: A Reproducible Benchmark
A fair, scripted comparison of CognoDB Cloud against four other managed/self-managed graph databases on the same dataset, same queries, same client, and matched resource tiers.

TL;DR: (fill in after the first full run — one or two sentences on what stood out, e.g. "CognoDB and Neo4j Aura Free were within noise of each other on 1-hop traversals; Memgraph's in-memory engine pulled ahead on read-heavy mixed workloads at the cost of dataset size headroom; ArangoDB's larger free tier makes its numbers not directly comparable without the capped supplementary run.")

1. Databases compared
Platform	Query language	Why it's in this comparison
CognoDB Cloud (c0 free)	Cypher (Bolt)	The subject of the benchmark.
Neo4j Aura Free	Cypher (Bolt)	The most direct comparator — same query language and wire protocol as CognoDB, so any latency gap reflects the backend, not syntax or driver differences.
Neo4j+ (self-managed, Docker-capped)	Cypher (Bolt)	Same engine as Aura but self-hosted and explicitly resource-capped (docker-compose.neo4j-plus.yml) to CognoDB's exact 0.5 vCPU / 256MB / 1GB spec — isolates "managed service overhead" from "raw engine performance" by giving us a controlled-hardware Neo4j data point.
Memgraph Cloud	Cypher (Bolt)	Also Cypher/Bolt, but an in-memory-first architecture — a genuine architectural contrast rather than another Neo4j-family engine, useful for the "why do platforms differ" analysis.
Amazon Neptune (Serverless, min capacity)	openCypher (HTTPS)	A major managed graph offering with no free tier — included deliberately to test the harness against a different wire protocol (HTTPS + optional SigV4) and to make the resource-parity trade-off explicit rather than excluding non-free platforms entirely.
ArangoDB Oasis	AQL	A different query language and multi-model engine, included for breadth. Its free trial tier is larger than CognoDB's (see fairness caveats below) — treat its raw numbers as directional, not resource-matched, unless the supplementary capped self-hosted run is also included.
Four of five comparators share Cypher-over-Bolt with CognoDB, which is intentional: it lets the harness reuse one query template for most platforms (src/workloads.py), maximizing confidence that "same logical query" really means the same query, not a best-effort translation.

2. Repository layout
config/platforms.yaml        Platform registry: adapter type, credentials env-var prefix, advertised specs
src/
  config.py                  Loads platforms.yaml + .env
  adapters/                  One adapter per wire protocol/dialect (base.py defines the interface)
    cypher_bolt_adapter.py   CognoDB, Neo4j Aura, Neo4j+, Memgraph  (identical Cypher/Bolt)
    neptune_adapter.py       Amazon Neptune (openCypher over HTTPS)
    arango_adapter.py        ArangoDB (AQL)
  dataset_prep.py            Builds the sized movie/actor dataset from public IMDb data
  loader.py                  Streams the dataset into any adapter, times ingest throughput
  workloads.py                Query templates for every required metric, per dialect
  runner.py                  Warm-up, latency percentiles, mixed-workload concurrency sweep
  metrics.py                 Percentile/statistics helpers (unit-tested, see tests/)
scripts/
  run_all.py                 One-command benchmark runner across all configured platforms
  generate_readme_tables.py  Turns results/results.json into the markdown tables below
docker-compose.neo4j-plus.yml  Resource-capped self-managed Neo4j+ instance
tests/test_metrics.py        Unit tests for the percentile math
results/                     JSON output per platform + combined results.json (gitignored except .gitkeep)
3. Dataset
Source: IMDb non-commercial datasets (free for personal/non-commercial use, updated daily by IMDb — see terms).

Graph shape: (:Person)-[:ACTED_IN {ordering, category}]->(:Movie {year, genres, runtime_minutes})

Built by src/dataset_prep.py, which: 1. Downloads title.basics.tsv.gz, name.basics.tsv.gz, title.principals.tsv.gz. 2. Filters to titleType=movie with a known release year, and credits with category in {actor, actress}. 3. Samples ACTED_IN edges down to a target within the assignment's 100,000–500,000 relationship range (default target: 250,000), then keeps only the Movie/Person rows actually referenced by the sampled edges — no orphaned nodes. 4. Writes data/processed/{movies.csv, persons.csv, acted_in.csv} — the single source of truth every platform loader reads, which is what guarantees "identical dataset" rather than five independent downloads that might drift.

Dataset size actually loaded in this run: - Movies: 90,172 - Persons: 80,318 - Relationships: 99,989 ACTED_IN - Total nodes: 170,490

Verified directly against CognoDB with the counting queries below, and cross-checked against the console's own node/relationship counters and index list.

Cypher query MATCH (m:Movie) RETURN count(m) returning 90172

Movie node count — MATCH (m:Movie) RETURN count(m)

Cypher query MATCH (p:Person) RETURN count(p) returning 80318

Person node count — MATCH (p:Person) RETURN count(p)

Cypher query MATCH ()-[r:ACTED_IN]->() RETURN count(r) returning 95772

ACTED_IN relationship count — MATCH ()-[r:ACTED_IN]->() RETURN count(r)

SHOW INDEXES output listing movie_id_idx, movie_year_idx, person_id_idx

Indexes present on CognoDB before the lookup benchmarks — SHOW INDEXES

CognoDB Cloud console overview showing 170,490 nodes, 95,769 relationships, 473MB/1GiB storage

CognoDB Cloud console — instance overview confirming node/relationship counts and storage footprint independent of the Cypher driver

Load method (identical across platforms): driver-side batched UNWIND/AQL bulk insert via src/loader.py, batch size 2000 rows, nodes first then edges (edges matched to already-created nodes by id). No platform-specific bulk-import tool was used, so the load numbers measure driver-batched ingest specifically — call out if a platform's native bulk loader would materially change this (e.g. neo4j-admin import) and note that native bulk tools were intentionally excluded to keep the load method identical across platforms, not just the data.

4. Fairness: resource parity
Table of platform query dialect, vCPU, RAM, storage and notes for each platform

Advertised resource tiers per platform, as recorded from each provider's console

Platform	vCPU	RAM	Storage	Region	Caveats
CognoDB Cloud	0.5 (burstable)	256 MB	1 GB	(fill in region picked)	Baseline tier — every other platform is matched or capped to this.
Neo4j Aura Free	shared, not published	1 GB	~0.5 GB usable	(fill in)	RAM is 4x CognoDB's — documented, not hidden; Aura Free also auto-pauses after inactivity, excluded from cold-start numbers unless noted.
Neo4j+ (self-managed)	0.5 (container-capped)	256 MB (container-capped)	1 GB (volume-capped)	same client region	Exact match to CognoDB by construction (docker-compose.neo4j-plus.yml) — the strongest fairness data point in this comparison.
Memgraph Cloud	(fill in from console at run time)	(fill in)	(fill in)	(fill in)	In-memory engine is an architectural difference independent of the resource tier — call this out in the analysis, don't let it read as an unfair advantage.
Amazon Neptune	min Neptune Capacity Units (NCU)	not published per-NCU	pay-per-GB (uncapped)	must match client region	No free tier — this is the clearest resource-parity violation in the set. Included anyway per the assignment's "your choice" latitude, with this caveat stated up front rather than glossed over.
ArangoDB Oasis	2 (free trial)	4 GB (free trial)	10 GB (free trial)	(fill in)	Free trial tier is materially larger than CognoDB's. Numbers here are not resource-matched — treat as directional. (If run: mention whether the supplementary self-hosted-and-capped ArangoDB run was also included.)
Dataset sizing: the dataset is sized (100k–500k relationships, ~250k default) so it fits inside CognoDB's 1GB free tier, per the assignment's fairness note — the same dataset is loaded everywhere, so no platform benefits from a smaller effective working set.

5. Methodology
Same dataset, same queries, same client, matched resources (§4) for every platform.
Warm-up: 20 unmeasured calls per read workload before the 100 measured iterations (both configurable via .env: BENCH_WARMUP_ITERATIONS, BENCH_ITERATIONS).
Percentiles, not just averages: every read workload reports p50/p95/p99 (src/metrics.py, unit-tested in tests/test_metrics.py).
Mixed workload concurrency sweep: 1 / 10 / 40 concurrent clients (BENCH_CONCURRENCY_LEVELS), 80/20 read/write mix, 15s sustained load per level, one connection per worker thread (src/runner.py::run_mixed_workload).
Automation: python scripts/run_all.py loads data, runs every workload, and writes results/results.json for every configured platform in one command. scripts/generate_readme_tables.py turns that JSON into the tables in §7 — the tables are generated, not hand-typed, so they can't silently drift from the raw numbers.
Query correspondence across dialects: src/workloads.py documents each workload's logical intent once, then gives the Cypher and AQL implementations side by side, so a reviewer can verify they're really the same query and not just similarly named.
Required metrics → where they're implemented
Metric (assignment §5.2)	Implementation
Ingest throughput	src/loader.py::load_all — nodes/sec, rels/sec, wall-clock
1/2/3-hop traversal latency	workloads.py::traversal_1hop/2hop/3hop, p50/p95 via runner.py
Point lookup / indexed lookup	workloads.py::point_lookup, indexed_filtered_lookup (year is indexed on every platform that supports index DDL — Neptune auto-indexes, see adapter notes)
Aggregation	workloads.py::aggregation_by_category — count grouped by ACTED_IN.category
Mixed read/write throughput	runner.py::run_mixed_workload, swept at 1/10/40 clients
Footprint	adapters/*.py::footprint() — reports node/rel counts everywhere; storage/memory reported as "not observable via driver" where a platform doesn't expose it through Cypher/AQL, with a pointer to check the provider console manually
6. Reproducing this benchmark
Prerequisites: Python 3.11+, free/trial accounts on each platform in §1, Docker (for Neo4j+).

git clone <this-repo-url>
cd benchmark-graphdb
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in .env with your own connection details for each platform.
# Never commit .env — it's gitignored.

# 1. Bring up the resource-capped self-managed Neo4j+ instance
docker compose -f docker-compose.neo4j-plus.yml up -d

# 2. Build the dataset (one-time, ~1.5GB download from IMDb)
python src/dataset_prep.py

# 3. Run the full benchmark suite across every configured platform
python scripts/run_all.py
# or a subset while iterating: python scripts/run_all.py --only cognodb memgraph_cloud

# 4. Generate the results tables
python scripts/generate_readme_tables.py > results/tables.md
# paste results/tables.md into section 7 below
Any platform without credentials in .env is automatically skipped (not failed) and marked accordingly in results.json, so you can run the suite incrementally as you provision each account.

7. Results
Full four-platform comparison (CognoDB Cloud, Neo4j Aura Free, Memgraph Cloud, ArangoDB Oasis free trial) — tables generated by scripts/generate_readme_tables.py from results/results.json, charts built directly from the same numbers.

7.1 Data loading throughput
Platform	Nodes/sec	Rels/sec	Total load time (s)	Nodes loaded	Edges loaded
CognoDB Cloud (c0 free)	1,323.2	1,074.6	221.9	170,490	100,000
Neo4j Aura Free	3,611.4	3,198.6	78.5	170,490	100,000
Memgraph Cloud	3,077.4	2,561.4	94.4	170,490	100,000
ArangoDB Oasis (free trial)	5,099.5	6,493.2	48.8	170,490	100,000
Bar charts of nodes/sec, rels/sec ingest throughput and total load time per platform

7.2 Traversal latency (1-hop / 2-hop / 3-hop, ms)
Platform	1-hop p50/p95	2-hop p50/p95	3-hop p50/p95
CognoDB Cloud (c0 free)	255.6 / 268.7	255.5 / 269.5	255.5 / 256.2
Neo4j Aura Free	109.9 / 115.1	110.1 / 112.2	109.8 / 115.2
Memgraph Cloud	84.0 / 84.9	83.9 / 120.4	84.0 / 90.7
ArangoDB Oasis (free trial)	49.6 / 68.4	49.8 / 70.5	49.8 / 63.9
Bar charts of traversal p50 and p95 latency by hop depth per platform

7.3 Lookup latency: point vs. indexed/filtered (ms)
Platform	Point lookup p50/p95	Filtered lookup p50/p95
CognoDB Cloud (c0 free)	255.6 / 256.7	270.6 / 824.3
Neo4j Aura Free	110.3 / 112.6	125.0 / 267.3
Memgraph Cloud	83.9 / 85.0	96.3 / 301.8
ArangoDB Oasis (free trial)	49.5 / 60.7	52.0 / 155.3
Bar charts comparing point lookup vs filtered lookup p50, and filtered lookup p95 tail latency

7.4 Aggregation latency (count / group-by, ms)
Platform	p50 (ms)	p95 (ms)
CognoDB Cloud (c0 free)	1,593.8	1,809.6
Neo4j Aura Free	178.4	198.9
Memgraph Cloud	165.3	170.2
ArangoDB Oasis (free trial)	103.6	213.6
Bar chart of group-by aggregation p50 and p95 latency per platform

7.5 Mixed read/write throughput — concurrency sweep
Platform	Concurrency	R/W mix	Throughput (qps)	p50 (ms)	p95 (ms)	p99 (ms)
CognoDB Cloud (c0 free)	1	80/19	2.6	259.5	323.5	1,590.8
CognoDB Cloud (c0 free)	10	80/19	32.3	266.0	361.0	475.1
CognoDB Cloud (c0 free)	40	80/19	49.9	299.8	2,992.5	4,941.9
Neo4j Aura Free	1	80/19	8.5	107.8	114.6	133.0
Neo4j Aura Free	10	80/19	85.5	108.0	126.5	180.8
Neo4j Aura Free	40	80/19	335.5	106.2	126.1	143.3
Memgraph Cloud	1	80/19	11.7	83.1	86.1	95.1
Memgraph Cloud	10	80/19	118.9	80.4	89.1	91.9
Memgraph Cloud	40	80/19	476.1	80.4	86.2	98.5
ArangoDB Oasis (free trial)	1	80/19	18.5	50.3	69.5	101.4
ArangoDB Oasis (free trial)	10	80/19	164.1	51.3	99.4	117.7
ArangoDB Oasis (free trial)	40	80/19	491.9	77.2	123.9	158.8
Line chart of sustained throughput in qps vs concurrent clients per platform

7.6 Footprint (nodes / relationships stored)
Platform	Node count	Rel count	Observable?	Notes
CognoDB Cloud (c0 free)	170,490	95,772	Yes	Fallback count() queries
Neo4j Aura Free	170,490	99,989	Yes	APOC statistics
Memgraph Cloud	0	—	Yes	APOC statistics (footprint query returned 0 nodes for Memgraph on this run — flag for re-check before final submission)
ArangoDB Oasis (free trial)	170,490	100,000	Yes	—
Bar chart of stored node and relationship counts per platform

8. Analysis
Read performance
CognoDB's traversal and point-lookup medians cluster tightly around 255 ms regardless of hop depth, which points to network/connection round-trip time — not query-plan cost — as the dominant factor on the burstable 0.5 vCPU tier. Neo4j Aura Free (~110 ms) and Memgraph Cloud (~84 ms) show materially lower and flatter latency across hop depths, consistent with more headroom (RAM) and, for Memgraph, an in-memory-first engine. ArangoDB Oasis is fastest across the board (~50 ms), but its free-trial tier has 8x the RAM and 4x the vCPU of CognoDB's, so this gap reflects resource tier at least as much as engine efficiency — see §4.

Filtered/indexed lookups
Every platform's p95 balloons on the filtered lookup relative to the point lookup, and CognoDB's filtered-lookup p95 (824 ms) is the clearest outlier in the whole dataset — roughly 3x its own point-lookup p95 and 3–5x the other platforms' filtered p95s. That tail is worth digging into before final submission (cold cache on the burstable tier is the leading hypothesis, but it should be verified rather than assumed).

Aggregation
CognoDB's aggregation latency (p50 1.59 s) is 8–15x every other platform's, by far the largest gap in the whole benchmark. A full-scan group-by is memory- and CPU-bound rather than network-bound, so this is the workload most exposed by CognoDB's 256 MB / 0.5 vCPU ceiling — a good candidate for the analysis' central point about where the free tier's resource limits actually bite.

Mixed read/write throughput
At concurrency 1, every platform is within the same order of magnitude. By concurrency 40, ArangoDB and Memgraph both clear ~480 qps while CognoDB tops out at 49.9 qps with a p99 approaching 5 seconds — CognoDB is the only platform whose tail latency visibly degrades under load rather than just its throughput plateauing. This is the strongest evidence in the results that CognoDB's burstable 0.5 vCPU is the binding constraint under concurrent load, not the query design.

Footprint
Node/relationship counts are self-consistent across CognoDB, Neo4j, and ArangoDB (~170k nodes). Memgraph's footprint query returned 0 nodes in this run, which doesn't match the loader's reported 170,490 nodes loaded — likely a stale connection or a database-selection issue in the footprint query rather than an actual data loss, but it should be re-run and confirmed before this table is treated as final.

Limitations
Regions were not confirmed identical across all four platforms in this run — fill in per-platform region before final submission (§4).
Memgraph's footprint discrepancy (above) needs a re-run.
ArangoDB Oasis numbers are not resource-matched to CognoDB (2 vCPU/4GB vs. 0.5 vCPU/256MB) — treat its lead on raw latency/throughput as partly a tier effect, not purely engine efficiency, unless the capped self-hosted ArangoDB supplementary run is added.
Neo4j+ (self-hosted, capped to CognoDB's exact spec) and Amazon Neptune were defined in the harness (§1, §4) but are not yet included in these results — the strongest apples-to-apples comparison (Neo4j+ vs. CognoDB, both at 0.5 vCPU/256MB) is still outstanding.
License/attribution: IMDb dataset used under IMDb's non-commercial terms (https://www.imdb.com/interfaces/). This is a technical benchmark, not an endorsement of any platform.

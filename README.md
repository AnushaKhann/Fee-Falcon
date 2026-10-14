# FreightTiger — Freight Cost Anomaly Detection

A data-driven freight cost anomaly detection system that identifies unusual
changes in transportation costs and uses contextual notes to determine whether
those changes have a supported explanation.


## 1. Problem Statement

Freight transportation costs can change because of disruptions, temporary
demand fluctuations, fuel price increases, or other operational factors.

The objective is to build a reproducible pipeline that:

- Calculates weekly freight cost per tonne-kilometre for each route.
- Compares each route's cost with its historical behaviour.
- Compares costs with similar routes during the same week.
- Identifies unusual cost increases.
- Retrieves relevant operational notes.
- Validates whether a note supports the anomaly.
- Produces a structured CSV containing anomaly flags and explanations.

A detected anomaly is not automatically considered justified. An explanation
must be supported by a relevant contextual note.

## 2. Solution Overview

The pipeline consists of the following stages:

1. Load shipment records and contextual notes.
2. Aggregate shipment-level data into weekly route-level costs.
3. Calculate historical and peer baselines.
4. Detect potential anomalies.
5. Retrieve potentially relevant contextual notes.
6. Validate note applicability and timing.
7. Generate explanations and export the results.

### Architecture

```text
Shipment Records ──> Data Loading ──> Weekly Aggregation
                                           |
                                           v
                                    Baseline Calculation
                                           |
                                           v
                                    Anomaly Detection
                                           |
                                           v
Context Notes ──> Embedding Index ──> Note Retrieval
                                           |
                                           v
                                   Evidence Validation
                                           |
                                           v
                                   Explanation Generation
                                           |
                                           v
                                      Results CSV
```

## 3. Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Programming language | Python | Implements the data pipeline |
| Data processing | pandas | Loads, transforms, and aggregates shipment data |
| Testing | pytest | Tests individual components and pipeline behaviour |
| Embeddings | Sentence Transformers | Converts contextual notes into vector representations |
| Embedding model | all-MiniLM-L6-v2 | Supports semantic retrieval of contextual notes |
| Vector database | ChromaDB | Stores and retrieves embedded context notes |
| Output | CSV | Provides structured anomaly results |

The embedding model runs locally. The current implementation does not require
a hosted LLM API for anomaly detection or explanation generation.

## 4. Weekly Cost Calculation

Shipment records are grouped by origin, destination, route type, and week.

Weeks run from Monday through Sunday. The `week_of` field represents the
Monday starting the week.

For each shipment:

`tonne_km = quantity_tonnes × distance_km`

The weekly route-level cost is calculated as:

`cost_per_tonne_km = total_freight_cost / total_tonne_km`

The calculation uses the ratio of total freight cost to total
tonne-kilometres rather than a simple average of individual shipment ratios.

This produces a weighted cost measure for each route-week combination.

## 5. Baseline Calculation

The system compares each weekly route cost against two baselines.

### 5.1 Historical Baseline

The historical baseline is the mean cost per tonne-kilometre across the
preceding eight weekly observations for the same route.

The current observation is excluded from its own baseline.

If fewer than eight previous observations are available, all available
prior observations are used. The first observation for a route has no
historical baseline.

### 5.2 Similar-Route Baseline

The peer baseline is the mean cost per tonne-kilometre of other routes
with the same route type during the same week.

The current route is excluded from the peer calculation.

If no other route of the same type is available, the peer baseline is
unavailable.

### 5.3 Percentage Deviation

For either baseline:

`percentage_deviation = ((current_cost / baseline_cost) - 1) × 100`

A positive percentage indicates that the current cost is higher than
the corresponding baseline.

## 6. Anomaly Detection

The current implementation uses these initial thresholds:

- Historical deviation: 20%
- Similar-route deviation: 20%

An observation becomes an anomaly candidate when either percentage
deviation reaches or exceeds its corresponding threshold.

**Threshold assumption:** The case study does not prescribe an exact
numerical threshold. The 20% thresholds are engineering choices for the
initial implementation, not values supplied by FreightTiger.

The thresholds should be evaluated against labeled examples and
business requirements before production use.

## 7. Context Retrieval and Evidence Validation

Contextual notes are indexed using embeddings and stored in ChromaDB.

For each anomaly candidate, the system retrieves potentially relevant notes
using a query based on the route and relevant week.

Semantic similarity is used to identify candidate notes. It does not, by
itself, establish that a note explains an anomaly.

The evidence-validation stage checks whether a retrieved note is applicable
to the route and relevant time period.

The current implementation includes explicit validation rules for selected
notes, including the Chennai–Bangalore flooding disruption, the
Ahmedabad–Mumbai festival surcharge, and the nationwide diesel-price increase.

A note is accepted only when the implemented rules support its applicability.
A note that merely resembles the query, concerns another route, describes
stable conditions, or falls outside its supported time period must not be
treated as sufficient evidence.

### Output Classifications

| Flag | Meaning |
|---|---|
| `No` | No anomaly was detected using the configured thresholds. |
| `Yes` | An anomaly was detected, but no sufficiently supported explanation was accepted. |
| `No (justified)` | An anomaly candidate has a validated contextual explanation. |

The `matched_note_id` field identifies the supporting note for a justified
anomaly. It remains empty when no note is accepted.

## 8. Output Format

The pipeline writes its results to:

`outputs/results.csv`

The CSV contains the following columns in the required order:

| Column | Description |
|---|---|
| `route` | Origin-destination route |
| `week_of` | Monday starting the observation week |
| `cost_per_tonne_km` | Weekly freight cost per tonne-kilometre |
| `vs_own_history` | Comparison against the route's historical baseline |
| `vs_similar_routes` | Comparison against the same-week peer baseline |
| `flagged` | Anomaly classification |
| `matched_note_id` | ID of the validated supporting note, if any |
| `reason` | Explanation of the classification |

Each row represents one route-week observation.

## 9. Setup and Execution

### Prerequisites

- Python 3.12
- Git
- Sufficient disk space for Python dependencies and the local embedding model

### Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
python3 -m pip install -r requirements.txt
```

### Run the Pipeline

From the project root:

```bash
python3 main.py
```

The pipeline processes the input files, retrieves contextual notes, validates
evidence, and writes the results to `outputs/results.csv`.

The first execution may download the embedding model if it is not already
available locally.

### Run Tests

```bash
python3 -m pytest -v
```

## 10. Validation and Reproducibility

The current dataset contains:

- 2,940 shipment records
- 10 contextual notes
- 728 weekly route observations

The current pipeline run produced:

| Classification | Count |
|---|---:|
| `No` | 708 |
| `Yes` | 17 |
| `No (justified)` | 3 |
| **Total** | **728** |

Output validation confirmed the required column order, expected row count,
valid dates and numeric costs, permitted flag values, and consistency
between justified flags and matched note IDs.

Three consecutive runs using unchanged inputs produced byte-identical CSV
outputs in the local reproducibility check.

Reproducibility should be rechecked whenever the code, configuration,
dependencies, model, or input data changes.

## 11. Model and Cost Considerations

The project uses the local
`sentence-transformers/all-MiniLM-L6-v2` embedding model for semantic retrieval.

The current pipeline does not call a hosted LLM API.

| Metric | Current implementation |
|---|---|
| Hosted LLM API calls | 0 |
| Hosted LLM input tokens | 0 |
| Hosted LLM output tokens | 0 |
| Hosted LLM API cost | $0.00 |
| Embedding inference | Local computation |

Zero hosted LLM API cost does not mean computation is free. Local embedding
inference still uses hardware resources, and a production cost assessment
would include runtime, memory, storage, and deployment infrastructure.

## 12. Limitations

- The 20% anomaly thresholds are initial engineering assumptions.
- The thresholds have not been established through a formal optimization study.
- Evidence validation currently uses explicit rules for selected notes.
- Semantic similarity retrieves candidate notes but does not prove causation.
- The system requires further evaluation against labeled data before
  production use.
- Local embedding inference avoids hosted API charges but still consumes
  computational resources.

## 13. Future Improvements

- Evaluate thresholds using labeled historical examples.
- Measure precision, recall, and false-positive rates.
- Generalize temporal and route-specific evidence validation.
- Add explicit confidence and evidence-quality reporting.
- Expand retrieval evaluation using relevant and irrelevant note examples.
- Pin dependency versions for reproducible environment setup.
- Add structured logging and pipeline performance measurements.
- Add end-to-end tests for expected anomaly and non-anomaly cases.
MRB Long-Term CBA Module
========================

**MultiRiskBox -- Long-Term Planning & Risk Mitigation Analysis**

* * * * *

1\. Overview
------------

This module implements the **Long-Term Cost--Benefit Analysis (CBA)** component of the **MultiRiskBox (MRB)** platform, following the methodology defined in the approved proposal.

It supports **long-term strategic planning** and **risk-mitigation prioritization** for exposed infrastructures, using:

-   Hazard characteristics from MRB (Degree, Frequency, Intensity)

-   Infrastructure importance levels (Excel-based expert table)

-   Transparent, explainable ranking logic

-   Outputs designed for **matrix-based visualization**, as required by the proposal

The module is **self-contained**, **Docker-ready**, and communicates with MRB only via structured input/output folders.

* * * * *

2\. Conceptual Structure
------------------------

The long-term analysis is divided into **two phases**:

### Phase 1 --- *New Planification*

> *"What exists, what is missing, and how important is each element in the long term?"*

Outputs:

-   Hazard assessment per zone

-   A **ranking matrix** (zones × infrastructure types)

-   Identification of **missing high-value elements** ("gaps")

### Phase 2 --- *Risk Mitigation Measures*

> *"Given what exists, where should mitigation efforts be prioritized first?"*

Outputs:

-   Ranked mitigation list with **diminishing returns**

-   Aggregated summaries for visualization and decision-making

* * * * *

3\. Inputs (from MRB)
---------------------

All inputs are read from the `input/` directory.

### 3.1 `hazard_zones.json`

Hazard indicators per zone, already mapped to integer scales (1--5) by MRB.

`{
  "zones": [
    { "zone_id": "Zone_Yellow", "HD": 5, "F": 5, "I": 5 },
    { "zone_id": "Zone_Orange", "HD": 4, "F": 4, "I": 4 }
  ]
}`

Where:

-   **HD** = Hazard Degree

-   **F** = Frequency

-   **I** = Intensity

* * * * *

### 3.2 `exposure_by_zone.json`

Counts of exposed infrastructure elements per zone and per type.

`{
  "counts": [
    {
      "zone_id": "Zone_Yellow",
      "counts_by_type": {
        "hospitals_health_center": 2,
        "roads": 5,
        "shelters": 1
      }
    }
  ]
}`

> ⚠️ MRB provides **counts only** (no population, no asset IDs).

* * * * *

### 3.3 `config.json` (optional)

Controls thresholds and behavioral flags.

`{
  "phase1_gap_value_threshold": 4,
  "phase1_only_nonlow_hazard": true,
  "alpha_min": 0.55,
  "alpha_max": 0.92,
  "phase2_top_n": 50
}`

* * * * *

4\. Core Formulas and Logic
---------------------------

### 4.1 Hazard Index (per zone)

HazardIndex=round(HD+F+I3)\text{HazardIndex} = \text{round}\left(\frac{HD + F + I}{3}\right)HazardIndex=round(3HD+F+I​)

Mapped to hazard classes:

| HazardIndex | Hazard Class |
| --- | --- |
| 1--2 | Low |
| 3 | Medium |
| 4--5 | High |

* * * * *

### 4.2 Value Index (per infrastructure type)

Each infrastructure type is assigned a **Value Index (1--5)** based on expert knowledge (Excel table).

-   Phase 1 and Phase 2 may use **different tables**

-   Tables are **hardcoded** to ensure reproducibility

* * * * *

### 4.3 Priority Matrix (approved proposal logic)

This matrix maps **Hazard Class × Value Index → Priority**:

| Hazard ↓ / Value → | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- |
| Low hazard | Low | Low | Medium | Medium | High |
| Medium hazard | Low | Medium | Medium-High | High | Very High |
| High hazard | Medium | Medium-High | High | Very High | Very High |

This mapping is used in **both phases**.

* * * * *

5\. Phase 1 --- New Planification
-------------------------------

### 5.1 What Phase 1 computes

For **every zone × infrastructure type**:

-   HazardIndex and hazard class (from MRB)

-   ValueIndex (from Excel table)

-   Priority label and numeric rank

-   Observed count

-   Whether the element is **missing** (gap)

No population or planning standards are used.

* * * * *

### 5.2 Phase 1 Final Output (MAIN)

#### `phase1_matrix.json`

This file is the **official proposal-approved ranking matrix**.

**Structure:**

-   Rows = zones

-   Columns = infrastructure types

-   Cells contain:

    -   `value_index`

    -   `priority_label`

    -   `priority_rank` (1--5)

    -   `count`

    -   `is_gap`

This matrix is directly visualizable as:

-   Table

-   Heatmap

-   Gap map

* * * * *

### 5.3 Gap definition

Gap={1if ValueIndex≥threshold∧count=00otherwise\text{Gap} = \begin{cases} 1 & \text{if } \text{ValueIndex} \ge \text{threshold} \land \text{count} = 0 \\ 0 & \text{otherwise} \end{cases}Gap={10​if ValueIndex≥threshold∧count=0otherwise​

* * * * *

6\. Phase 2 --- Risk Mitigation Measures
--------------------------------------

Phase 2 prioritizes **existing exposed elements**, accounting for **diminishing returns** when many similar elements exist.

* * * * *

### 6.1 Synthetic assets

Because MRB provides only counts, the module generates **synthetic IDs** internally:

`Zone_Yellow:roads:1
Zone_Yellow:roads:2
...`

This allows per-element ranking while remaining consistent with counts.

* * * * *

### 6.2 Base score

Each element receives a base score derived from:

-   Priority class

-   HazardIndex

-   ValueIndex

Used only for ordering (no physical units).

* * * * *

### 6.3 Diminishing returns (key concept)

To avoid over-prioritizing repeated element types:

α(V)=αmin+V-14(αmax-αmin)\alpha(V) = \alpha_{min} + \frac{V - 1}{4}(\alpha_{max} - \alpha_{min})α(V)=αmin​+4V-1​(αmax​-αmin​) weight(k)=α(V)k\text{weight}(k) = \alpha(V)^kweight(k)=α(V)k final_score=base_score×weight(k)\text{final\_score} = \text{base\_score} \times \text{weight}(k)final_score=base_score×weight(k)

Where:

-   VVV = Value Index

-   kkk = number of already-selected elements of the same type

This ensures **diversification of mitigation priorities**.

* * * * *

7\. Phase 2 Outputs
-------------------

### 7.1 `phase2_risk_mitigation.json` (MAIN)

A ranked list of mitigation priorities, including:

-   Element type

-   Zone

-   Priority label

-   Final score

-   Diminishing-returns diagnostics (α, weight, repetition count)

* * * * *

### 7.2 `phase2_type_summary.json`

Aggregated, **non-technical friendly** summary:

-   Total contribution per type

-   Average and maximum scores

-   Zones involved

Ideal for dashboards and bar charts.

* * * * *

### 7.3 `phase2_matrix.json` (optional but powerful)

A **zone × type matrix** showing:

-   Number of assets

-   Sum of final scores

-   Maximum final score

Allows Phase-2 results to be visualized similarly to Phase-1.

* * * * *

8\. Output Files Summary (Frontend Contract)
--------------------------------------------

| File | Purpose |
| --- | --- |
| `phase1_matrix.json` | **Main Phase-1 ranking matrix (proposal output)** |
| `phase2_risk_mitigation.json` | **Main Phase-2 ranked list** |
| `phase2_type_summary.json` | Executive / chart-ready summary |
| `phase2_matrix.json` | Optional Phase-2 matrix |
| `phase1_new_planification.json` | Detailed traceability |
| `summary.json` | KPIs & run metadata |

* * * * *

9\. Running the Module
----------------------

### Install (once)

`pip install -e .`

### Run with MRB-style folders

`python -m mrb_longterm.cli --input input --output output`

* * * * *

10\. Tests
----------

Run all tests (unit + E2E):

`pytest`

* * * * *

11\. Demo
---------

Run the demo scenario:

`python demo/demo_run.py`

Outputs appear in:

`demo/demo_outputs/`

* * * * *

12\. Design Principles
----------------------

-   ✔ Fully explainable (no black boxes)

-   ✔ Proposal-faithful

-   ✔ Frontend-ready outputs

-   ✔ Counts-only compatible

-   ✔ Docker-friendly

-   ✔ Scientifically defensible

* * * * *

13\. Final Statement
--------------------

> This module **implements the approved long-term ranking matrix and mitigation logic exactly as described in the proposal**, producing both machine-readable and visualization-ready outputs suitable for the MultiRiskBox platform.
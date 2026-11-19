# Wild Shield Karnataka — System Architecture

> All diagrams rendered as Mermaid. GitHub, GitLab, and Mermaid Live (mermaid.live) will render these automatically.

---

## 1. High-Level System Architecture

```mermaid
graph TD
    User["👤 User / Forest Official"] -->|Browser| Dashboard

    subgraph Frontend["🖥️ Streamlit Dashboard"]
        Dashboard["app.py — Entry Point"]
        P1["📊 Main Dashboard"]
        P2["🗺️ Risk Assessment Map"]
        P3["📢 Safety Advisories"]
        P4["📋 Incident History"]
        P5["⚙️ Agent Console"]
    end

    Dashboard --> P1
    Dashboard --> P2
    Dashboard --> P3
    Dashboard --> P4
    Dashboard --> P5

    subgraph Orchestrator["🔄 Orchestrator Layer"]
        Orch["orchestrator.py"]
    end

    P2 -->|Trigger analysis| Orch
    P3 -->|Trigger advisories| Orch
    P5 -->|Run full pipeline| Orch

    subgraph Agent1["🤖 Agent 1 — Risk Assessment"]
        A1["agent1_risk.py"]
        LLM1["IBM Granite LLM\nWatsonx.ai\nAPI Key 1\nTemp: 0.2"]
    end

    subgraph Agent2["🤖 Agent 2 — Safety Advisor"]
        A2["agent2_safety.py"]
        LLM2["IBM Granite 4.2-8B\nReplicate API\nAPI Key 2\nTemp: 0.7"]
    end

    Orch -->|"Historical incidents"| A1
    A1 --> LLM1
    LLM1 -->|"RiskAssessmentResult"| A1
    A1 -->|"Structured JSON"| A2
    A2 --> LLM2
    LLM2 -->|"Kannada + English advisories"| A2

    subgraph DB["🗄️ MySQL Database"]
        T1["villages"]
        T2["wildlife_incidents"]
        T3["risk_assessments"]
        T4["safety_advisories"]
        T5["forest_boundaries"]
    end

    A1 -->|"Save results"| T3
    A2 -->|"Save advisories"| T4
    Dashboard -->|"Read data"| DB

    subgraph Data["📂 Data Layer"]
        CSV["sample_incidents.csv\n(45 rows, 11 villages)"]
        Seeds["seed_data.py"]
    end

    CSV --> Seeds --> DB
```

---

## 2. Agent Communication Workflow

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Streamlit Dashboard
    participant O as Orchestrator
    participant A1 as Agent 1 (Risk Assessment)
    participant L1 as IBM Granite LLM 1
    participant A2 as Agent 2 (Safety Advisor)
    participant L2 as IBM Granite 4.2-8B
    participant DB as MySQL Database

    U->>UI: Select village / trigger analysis
    UI->>O: run_pipeline(village_id)
    O->>DB: Fetch historical incidents for village
    DB-->>O: Incident records

    O->>A1: assess_risk(incidents, village_data)
    A1->>A1: Calculate risk score (0-100)
    A1->>A1: Identify hotspots (rule-based)
    A1->>L1: Generate narrative explanation
    L1-->>A1: Risk narrative (Granite LLM 1)
    A1-->>O: RiskAssessmentResult {score, classification, hotspots, explanation}

    O->>DB: Save risk assessment
    O->>A1: Progress callback (50%)

    O->>A2: generate_advisory(RiskAssessmentResult)
    A2->>L2: Generate English advisory prompt
    L2-->>A2: English advisory text
    A2->>L2: Generate Kannada advisory prompt
    L2-->>A2: Kannada advisory text
    A2->>A2: Validate advisory (no real-time claims)
    A2-->>O: SafetyAdvisoryResult {english, kannada, precautions}

    O->>DB: Save advisory
    O->>UI: Progress callback (100%)
    O-->>UI: PipelineResult {assessment, advisory}
    UI-->>U: Display maps, risk cards, advisory panels
```

---

## 3. Database Schema

```mermaid
erDiagram
    villages {
        INT id PK
        VARCHAR name
        VARCHAR district
        DECIMAL latitude
        DECIMAL longitude
        INT population
        DECIMAL distance_to_forest_km
        TIMESTAMP created_at
    }

    wildlife_incidents {
        INT id PK
        INT village_id FK
        VARCHAR species
        VARCHAR incident_type
        TEXT description
        DECIMAL latitude
        DECIMAL longitude
        DATETIME incident_date
        VARCHAR severity
        BOOLEAN is_synthetic
        TIMESTAMP created_at
    }

    risk_assessments {
        INT id PK
        INT village_id FK
        FLOAT risk_score
        VARCHAR risk_classification
        TEXT hotspots_json
        TEXT explanation
        TEXT species_summary_json
        TIMESTAMP assessed_at
    }

    safety_advisories {
        INT id PK
        INT village_id FK
        INT risk_assessment_id FK
        TEXT english_advisory
        TEXT kannada_advisory
        TEXT precautions_json
        VARCHAR priority
        TIMESTAMP generated_at
    }

    forest_boundaries {
        INT id PK
        VARCHAR name
        VARCHAR region
        TEXT boundary_geojson
        TIMESTAMP created_at
    }

    villages ||--o{ wildlife_incidents : "has"
    villages ||--o{ risk_assessments : "has"
    villages ||--o{ safety_advisories : "has"
    risk_assessments ||--o{ safety_advisories : "produces"
```

---

## 4. Technology Stack Overview

```mermaid
mindmap
  root((Wild Shield Karnataka))
    Frontend
      Streamlit 1.28+
      Folium Maps
      Plotly Charts
      Custom CSS
    AI Agents
      Agent 1 Risk Assessment
        IBM Watsonx.ai
        Granite LLM 1
        Temperature 0.2
      Agent 2 Safety Advisor
        Replicate API
        Granite 4.2-8B
        Temperature 0.7
    Backend
      Python 3.11+
      Orchestrator
      Pandas
      python-dotenv
    Database
      MySQL 8.0+
      5 Tables
      Connection Pool
    IBM Platform
      IBM Bob Dev Tool
      IBM Cloud
      IBM Watsonx.ai
      IBM SkillsBuild
    Deployment
      Streamlit Cloud
      GitHub
      Env Secrets
```

---

## 5. Risk Scoring Logic

```mermaid
flowchart TD
    Start([Village Selected]) --> FetchData[Fetch Historical Incidents]
    FetchData --> CalcFreq[Calculate Incident Frequency\nper 90-day window]
    CalcFreq --> CalcProx[Assess Forest Proximity\ndistance_to_forest_km]
    CalcProx --> CalcSpec[Species Severity Weight\nElephant=10, Leopard=9,\nTiger=10, Wild Boar=6]
    CalcSpec --> CalcRecency[Recency Weight\nLast 30d = 1.5x\nLast 90d = 1.2x]
    CalcRecency --> CalcSev[Injury/Death Penalty\n+15 points per fatality]
    CalcSev --> SumScore[Sum Weighted Score\n0–100 range]
    SumScore --> Classify{Classify}
    Classify -->|score < 35| LOW[🟢 LOW RISK\nGeneral awareness advisories]
    Classify -->|35 ≤ score < 65| MEDIUM[🟡 MEDIUM RISK\nIncreased caution messages]
    Classify -->|score ≥ 65| HIGH[🔴 HIGH RISK\nUrgent advisory + contact officials]
    LOW --> A2([Pass to Agent 2])
    MEDIUM --> A2
    HIGH --> A2
```

---

## 6. Data Flow Summary

```mermaid
flowchart LR
    CSV["📄 sample_incidents.csv\n45 synthetic incidents\n11 Karnataka villages"] -->|seed_data.py| MySQL

    MySQL -->|"SQL query"| A1["Agent 1\nRisk Assessment"]
    A1 -->|"RiskAssessmentResult\nJSON payload"| A2["Agent 2\nSafety Advisor"]

    A1 -->|"risk_assessments table"| MySQL
    A2 -->|"safety_advisories table"| MySQL

    A1 -->|"Map markers\nRisk cards"| Dashboard["Streamlit Dashboard"]
    A2 -->|"Kannada advisory\nEnglish advisory\nPrecautions"| Dashboard

    Dashboard -->|"Folium map\nPlotly charts\nKPI cards"| Browser["👤 User Browser"]
```

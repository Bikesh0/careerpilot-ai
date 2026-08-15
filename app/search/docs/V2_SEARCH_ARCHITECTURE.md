# CareerPilot AI

## Technical Project Documentation, Architecture, Development Procedure, and Interview Guide

**Project:** CareerPilot AI
**Branch:** `v2-development`
**Current V2 milestone:** Unified Search Service
**Latest commit:** `84cf16e — Add V2 search service`

---

# 1. Project Overview

CareerPilot AI is a job discovery and matching application designed to help a candidate find relevant employment opportunities from multiple job sources.

The project combines:

* job-source aggregation
* data normalization
* duplicate detection
* candidate/job matching
* relevance scoring
* job ranking
* web application integration

The original V1 application established the basic application and job-search foundation. V2 is being developed as a more modular and extensible search architecture.

The central architectural idea of V2 is:

> **Collect jobs from multiple sources, convert them into one common representation, remove duplicates, evaluate their relevance to a candidate, and rank them before presenting them to the application.**

---

# 2. Problem Statement

A job-search application that collects information from multiple websites faces several engineering problems.

Different sources can expose job information in different formats. A job from one source may contain fields or naming conventions that differ from another source.

Without a common representation, downstream functionality such as matching and ranking becomes tightly coupled to individual sources.

The system also needs to answer two different questions:

1. **Is this job relevant to the candidate?**
2. **Which relevant jobs should be shown first?**

These concerns should not be mixed together.

The V2 architecture was therefore designed around separate layers for:

* source collection
* normalization
* deduplication
* matching
* ranking
* service orchestration

This separation makes the system easier to test, understand, extend, and maintain.

---

# 3. Project Objectives

The V2 search architecture has the following objectives.

## Primary objectives

1. Support multiple job sources through a common interface.
2. Convert source-specific job data into a canonical representation.
3. Remove duplicate jobs.
4. Match jobs against candidate preferences and skills.
5. Produce an interpretable relevance score.
6. Rank jobs according to that score.
7. Provide one unified search entry point.
8. Keep the architecture extensible for future improvements.
9. Validate each architectural layer independently.
10. Integrate the V2 architecture into the existing application without unnecessarily breaking V1 functionality.

## Secondary objectives

The architecture should also make future functionality possible, including:

* semantic job matching
* improved skill extraction
* seniority matching
* persistent job storage
* richer candidate profiles
* ranking evaluation
* machine-learning or LLM-assisted matching

---

# 4. High-Level Architecture

The V2 search pipeline can be represented as follows:

```text
                    JOB SOURCES
                         │
          ┌──────────────┼──────────────┐
          │              │              │
      Duunitori        Jobly      Työmarkkinatori
          │              │              │
          └──────────────┼──────────────┘
                         │
                  Work in Finland
                         │
                         ▼
                 SOURCE REGISTRY
                         │
                         ▼
                   SOURCE RUNNER
                         │
                         ▼
                  NORMALIZATION
                         │
                         ▼
                   CanonicalJob
                         │
                         ▼
                    DEDUPLICATION
                         │
                         ▼
                    MATCHING
                         │
             ┌───────────┼───────────┐
             │           │           │
           Title       Skills     Location
             │           │           │
             └───────────┼───────────┘
                         │
                         ▼
                     RANKING
                         │
                         ▼
                  V2SearchService
                         │
                         ▼
                  APPLICATION / UI
```

The key principle is separation of concerns.

Each layer has one primary responsibility.

---

# 5. Technology Stack

| Area                    | Technology                      |
| ----------------------- | ------------------------------- |
| Programming language    | Python                          |
| HTTP requests           | `requests`                      |
| HTML parsing            | BeautifulSoup                   |
| Data modelling          | Python `dataclasses`            |
| Web application         | Existing Python web application |
| Testing                 | Python smoke/integration tests  |
| Version control         | Git                             |
| Development environment | Windows / PowerShell            |
| Architecture            | Layered modular architecture    |

---

# 6. Why Python?

Python was used because it is well suited to this type of application.

The project requires:

* HTTP requests
* HTML parsing
* text processing
* data transformation
* scoring
* web application integration

Python provides mature libraries for all of these areas.

It also allows the search architecture to remain relatively concise and readable.

For this project, readability and development speed were important because the system is being developed incrementally.

---

# 7. Source Layer

The first part of the V2 architecture deals with external job sources.

The current source implementations are:

* Duunitori
* Jobly
* Työmarkkinatori
* Work in Finland

The source implementations are located under:

```text
app/search/sources/
```

The V2 architecture does not want the rest of the system to know how each website works internally.

Instead, sources expose a common search operation.

Conceptually:

```python
source.search()
```

returns jobs that can subsequently be normalized.

---

# 8. Source Foundation

The source foundation was repaired first.

Git checkpoint:

```text
2b915c4 — Repair V2 job source foundation
```

The source classes were verified for:

* class definitions
* search URLs
* search methods
* page retrieval
* HTTP dependencies
* parsing dependencies

The environment was also checked for:

```text
requests
beautifulsoup4
```

Both dependencies were successfully available.

The source module compiled successfully and all four source classes imported successfully.

This was deliberately made the first checkpoint because later V2 layers depend on reliable source objects.

---

# 9. Canonical Job Model

The next architectural problem was data consistency.

Different sources should not force the matching and ranking layers to understand different data formats.

V2 therefore introduced a canonical job representation:

```text
CanonicalJob
```

The canonical representation contains fields such as:

* title
* company
* location
* URL
* source
* description
* external ID
* employment type
* remote status
* salary information
* posting date
* skills
* tags
* discovery timestamp

The canonical model becomes the contract between ingestion and the rest of the search system.

Git checkpoint:

```text
5efa652 — Add V2 canonical job ingestion layer
```

---

# 10. Why Use a Canonical Job Model?

Without canonicalization, downstream components would need logic such as:

```text
If source == Duunitori:
    use field A

If source == Jobly:
    use field B

If source == Work in Finland:
    use field C
```

That approach creates tight coupling.

Instead:

```text
Source-specific data
        ↓
Normalization
        ↓
CanonicalJob
        ↓
Matching / Ranking
```

The matching layer therefore only needs to understand `CanonicalJob`.

### Alternative considered

Another approach would have been to make the matching system understand every source format directly.

### Why that approach was rejected

It would make the matching system:

* harder to maintain
* harder to test
* harder to extend
* dependent on source-specific implementation details

The canonical model adds one transformation step but significantly simplifies the rest of the architecture.

---

# 11. Normalization

Normalization converts existing job objects into the canonical V2 representation.

The normalizer is responsible for creating consistent job data before matching and ranking.

A smoke test was performed using a V1 job object.

The resulting canonical object contained the expected fields and successfully passed the normalization test.

This demonstrated that V1-style job data can enter the V2 pipeline through a controlled conversion step.

---

# 12. Deduplication

Multiple sources can potentially describe the same job.

For example:

```text
Source A
Security Engineer
Acme
Helsinki
https://example.com/job/1

Source B
Security Engineer
Acme
Helsinki
https://example.com/job/1
```

Showing both records would produce duplicate results.

V2 therefore includes a deduplication layer.

Git checkpoint:

```text
5efa652 — Add V2 canonical job ingestion layer
```

A smoke test used two identical jobs:

```text
Input:  2 jobs
Output: 1 unique job
```

The deduplication test passed.

---

# 13. Source Registry

After canonical ingestion, V2 introduced a source registry.

Git checkpoint:

```text
e67d234 — Add V2 job source registry and orchestration
```

The registry contains source definitions for:

```text
Duunitori
Jobly
Työmarkkinatori
Work in Finland
```

Instead of the orchestration layer manually knowing how to construct every source, the registry provides a central definition.

Conceptually:

```text
SOURCE_REGISTRY
       │
       ├── DuunitoriSource
       ├── JoblySource
       ├── TyomarkkinatoriSource
       └── WorkInFinlandSource
```

---

# 14. Why a Registry?

A registry makes the architecture easier to extend.

If another job source needs to be added later, the intended process becomes:

```text
Create source implementation
        ↓
Register source
        ↓
Runner automatically includes it
```

Instead of rewriting the entire search pipeline.

### Alternative

Hardcode every source directly inside the search service.

### Why not?

That creates unnecessary coupling between the orchestration logic and individual source implementations.

The registry therefore improves extensibility and separation of concerns.

---

# 15. Source Runner

The `SourceRunner` coordinates source execution.

Its responsibilities include:

1. Create or receive source objects.
2. Execute each source.
3. Collect raw jobs.
4. Normalize each job.
5. Handle source-level errors.
6. Continue processing other sources if one source fails.
7. Deduplicate the combined result.

This creates a controlled ingestion boundary.

Conceptually:

```text
Source 1 ─┐
Source 2 ─┤
Source 3 ─┼──> SourceRunner
Source 4 ─┘        │
                   ▼
              normalize
                   │
                   ▼
               deduplicate
```

---

# 16. Error Isolation

An important property of the runner is that one source failure should not necessarily terminate the entire search.

For example:

```text
Duunitori       → success
Jobly           → success
Työmarkkinatori → error
Work in Finland → success
```

The intended behavior is to retain the successful results rather than discard the entire search.

This is important for real-world web scraping because external websites can be temporarily unavailable or change their structure.

---

# 17. Matching Layer

Once jobs are normalized and deduplicated, V2 evaluates how well they match a candidate profile.

Git checkpoint:

```text
09ef64a — Add V2 job matching foundation
```

The matching layer currently evaluates:

* job title
* candidate skills
* location

The result is represented by:

```text
MatchResult
```

A match result contains:

* overall score
* reasons
* matched skills
* missing skills
* title score
* skill score
* location score
* seniority score

---

# 18. Why Separate Matching From Ranking?

Matching and ranking solve different problems.

### Matching

Answers:

> How well does this individual job fit the candidate?

### Ranking

Answers:

> In what order should the matching jobs be presented?

Keeping these concerns separate allows the matching logic and ranking logic to evolve independently.

For example, the matching engine could later become semantic without requiring the entire search service to be rewritten.

---

# 19. Current Matching Algorithm

The current deterministic scoring model is:

```text
Title       = 35%
Skills      = 45%
Location    = 20%
```

The total score is calculated as:

```text
score =
    title_score × 0.35
  + skill_score × 0.45
  + location_score × 0.20
```

The score is normalized to a 0–100 scale.

This is intentionally simple and explainable.

---

# 20. Why Deterministic Matching Instead of an LLM?

An LLM could potentially be used to determine semantic similarity between a candidate and a job.

However, introducing an LLM at this stage would add:

* API dependency
* cost
* latency
* less deterministic behavior
* additional debugging complexity
* evaluation complexity

The current deterministic system has several advantages:

* predictable
* reproducible
* explainable
* easy to test
* inexpensive
* easy to debug

This does not mean LLM-based matching is rejected permanently.

The architecture deliberately leaves room for a future semantic matching component.

The current strategy is:

> **Build a reliable deterministic foundation first, then introduce AI where it provides measurable value.**

---

# 21. Explainability

The matcher does not only produce a number.

It also produces reasons such as:

```text
Target job title matched
Matched 3 profile skills
Target location matched
1 profile skill not found
```

This is important because a candidate should be able to understand why a job received a particular score.

Explainability is especially useful for debugging and future UI development.

---

# 22. Matching Validation

A mock job was tested against:

```text
Python
AWS
Linux
Cybersecurity
```

The job description contained:

```text
Python
AWS
Linux
cloud security
```

The result was:

```text
Score: 88.75

Matched:
- Python
- AWS
- Linux

Missing:
- Cybersecurity
```

The title and location both matched.

The matching smoke test passed.

---

# 23. Ranking Layer

After matching was implemented, V2 introduced a dedicated ranking layer.

Git checkpoint:

```text
7689535 — Add V2 job ranking layer
```

The ranker:

1. receives jobs
2. evaluates each job using the matcher
3. creates ranked job objects
4. sorts them by score
5. optionally applies a result limit

The result therefore becomes:

```text
Jobs
  ↓
Match each job
  ↓
Calculate scores
  ↓
Sort descending
  ↓
Top results
```

---

# 24. Ranking Validation

Three mock jobs were evaluated.

The resulting order was:

```text
1. Security Engineer      100.0
2. Cloud Engineer          57.5
3. IT Support Specialist   20.0
```

The test verified that the Security Engineer position appeared first and that its score exceeded the other results.

The ranking layer passed validation.

---

# 25. Unified V2 Search Service

The next step was to create a single service that combines the architecture.

Git checkpoint:

```text
84cf16e — Add V2 search service
```

The service is:

```text
V2SearchService
```

Its purpose is to provide one entry point for the complete search process.

Conceptually:

```text
V2SearchService.search()
          │
          ▼
     SourceRunner
          │
          ▼
    Normalization
          │
          ▼
     Deduplication
          │
          ▼
        Ranking
          │
          ▼
     Ranked results
```

This means callers do not need to know the internal details of the search pipeline.

---

# 26. V2 Search Service Validation

The unified service was tested using three mock jobs.

Results:

```text
RESULT COUNT: 3

1. Security Engineer | Company B | score=100.0
2. Cloud Engineer | Company C | score=57.5
3. IT Support Specialist | Company A | score=20.0
```

The test confirmed:

```text
V2 SEARCH SERVICE OK
FULL V2 SEARCH STACK OK
```

---

# 27. Development Procedure

The V2 architecture was developed incrementally rather than being written as one large change.

The procedure was:

### Step 1 — Stabilize source foundation

Verify source classes, HTTP access, parsing dependencies, compilation, and imports.

### Step 2 — Introduce canonical data

Create `CanonicalJob`, normalization, and deduplication.

### Step 3 — Introduce source management

Create the registry and runner.

### Step 4 — Introduce matching

Create match signals and deterministic scoring.

### Step 5 — Introduce ranking

Convert match scores into ordered results.

### Step 6 — Create unified service

Expose the complete pipeline through `V2SearchService`.

### Step 7 — Validate each layer

Run compilation, import tests, smoke tests, and mock integration tests.

### Step 8 — Create Git checkpoint

Commit each architectural milestone independently.

### Step 9 — Integrate with application

The next development phase is connecting V2 to the existing application while protecting existing V1 behavior.

---

# 28. Git Development History

The V2 development history currently provides a clear architectural progression.

```text
84cf16e  Add V2 search service
    │
7689535  Add V2 job ranking layer
    │
09ef64a  Add V2 job matching foundation
    │
e67d234  Add V2 job source registry and orchestration
    │
5efa652  Add V2 canonical job ingestion layer
    │
2b915c4  Repair V2 job source foundation
    │
ab022e2  Release CareerPilot AI V1
```

This history provides useful development checkpoints and makes it possible to inspect each architectural stage independently.

---

# 29. Testing Strategy

Testing has been incremental.

Each layer was first compiled and imported before being connected to the next layer.

Validation has included:

* Python compilation
* module imports
* source registration
* deduplication smoke tests
* normalization smoke tests
* matching smoke tests
* ranking smoke tests
* unified service tests

The principle was:

> **Validate each layer before building the next layer on top of it.**

This reduces the number of possible causes when a later integration test fails.

---

# 30. Debugging Example

During the orchestration testing stage, the first mock test attempted to define a Python class and method inside a single `python -c` command.

Python rejected the command with a syntax error because the compound class/function definition could not be expressed in that attempted one-line structure.

Instead, the test was rewritten as a PowerShell here-string:

```powershell
@'
Python test code
'@ | python
```

The corrected test produced:

```text
MOCK INPUT: 2
CANONICAL OUTPUT: 1
ORCHESTRATION OK
```

This demonstrates an important development principle:

> Test failures should be isolated to determine whether the problem is in the application code, test code, or development environment.

---

# 31. Design Principles

The V2 architecture follows several software engineering principles.

## Separation of concerns

Each layer has a specific responsibility.

## Modularity

Components can be tested independently.

## Extensibility

New sources can be added through the source registry.

## Encapsulation

The search service hides internal pipeline details from callers.

## Explainability

Matching produces both scores and reasons.

## Fault isolation

Individual source failures do not have to terminate the entire ingestion process.

## Incremental development

Each major architectural improvement has its own Git checkpoint.

---

# 32. Why Not Build Everything Into One Search Function?

A single function could technically:

```text
scrape → normalize → match → rank → return
```

However, that would create a large amount of coupling.

Changing one concern could affect unrelated functionality.

For example, changing HTML parsing could accidentally affect ranking logic.

The layered architecture avoids this.

Instead:

```text
Sources
   ↓
Ingestion
   ↓
Matching
   ↓
Ranking
   ↓
Service
```

Each component has a defined responsibility.

---

# 33. Why Not Use a Database First?

A database can be useful for persistent job storage, historical analysis, and tracking jobs over time.

However, persistence was not required to establish the core search architecture.

The first priority was to make the data pipeline correct:

```text
collect
→ normalize
→ deduplicate
→ match
→ rank
```

Persistence can be introduced once the domain model and pipeline behavior are stable.

This reduces the risk of building database infrastructure around an unstable data model.

---

# 34. Why Not Introduce Machine Learning Immediately?

Machine learning or LLM-based ranking can be valuable, but it requires evaluation.

Without a reliable baseline, it becomes difficult to determine whether a sophisticated model actually improves results.

The deterministic matcher provides a baseline against which future semantic approaches can be measured.

Therefore the development strategy is:

```text
Reliable baseline
       ↓
Evaluation
       ↓
Semantic matching
       ↓
Compare results
       ↓
Keep improvements that demonstrate value
```

---

# 35. Current Limitations

The current V2 foundation is intentionally incomplete in several areas.

## Matching

Matching is primarily lexical rather than semantic.

For example, two skills that are conceptually related but use different terminology may not match.

## Seniority

The `seniority_score` field exists in the result model but is not yet actively calculated.

## Skill extraction

The current system relies on available job/profile skill information and text matching rather than a sophisticated skill ontology.

## External websites

Job-source implementations depend on external website structures that may change.

## Evaluation

The current tests validate functionality, but a larger labelled dataset is required to evaluate ranking quality systematically.

## Application integration

The V2 search service currently exists as a search architecture and has not yet been fully integrated into the production application path.

---

# 36. Future Development

The next major phase is application integration.

Potential future improvements include:

### Application integration

Connect `V2SearchService` to the existing web application through a controlled adapter.

### Persistent storage

Store normalized jobs for:

* history
* tracking
* deduplication across runs
* analytics

### Better skill extraction

Develop a richer skill normalization system.

For example:

```text
AWS
Amazon Web Services
AWS Cloud
```

could potentially map to a common skill concept.

### Seniority matching

Introduce:

```text
Intern
Junior
Mid
Senior
Lead
Manager
```

and compare job requirements with candidate preferences.

### Semantic matching

Introduce embeddings or LLM-assisted analysis after the deterministic baseline has been evaluated.

### Ranking evaluation

Create a labelled dataset and measure:

* precision
* recall
* ranking quality
* user satisfaction
* relevance at top-K results

---

# 37. Interview Explanation — Short Version

A concise explanation of the project is:

> CareerPilot AI is a job discovery and matching system. I developed a V2 search architecture to make the original search functionality more modular and extensible.
>
> I separated the system into source ingestion, normalization, deduplication, matching, ranking, and service layers. Multiple job sources are registered through a common registry and executed by a source runner. Their results are converted into a canonical job model so that downstream components do not need to understand source-specific formats.
>
> I then built a deterministic matching engine using job title, skills, and location, followed by a ranking layer that orders jobs according to their relevance score. Finally, I created a `V2SearchService` that provides a single entry point to the complete pipeline.
>
> I deliberately started with deterministic and explainable matching instead of immediately using an LLM. This provides a predictable baseline that is easy to test and evaluate, while keeping the architecture open for semantic matching later.
>
> I developed the system incrementally and committed each architectural milestone separately in Git. Each layer was validated with compilation, import, smoke, and mock integration tests.

---

# 38. Interview Question: What Did You Personally Build?

A strong answer is:

> I worked on the redesign of the job-search subsystem. I implemented the canonical job model and normalization layer, source registry and orchestration, deduplication, candidate/job matching, relevance scoring, ranking, and the unified V2 search service. I also validated each layer independently and used Git checkpoints throughout the development process.

---

# 39. Interview Question: Why Did You Choose This Architecture?

> I wanted to separate source-specific concerns from the rest of the application. Job websites change independently, so I didn't want the matching or ranking logic to depend on how a particular website structures its data. The canonical model creates a stable internal contract, while the registry and runner make the ingestion layer extensible.

---

# 40. Interview Question: Why Not Just Scrape Everything and Send It to an LLM?

> That would make the system harder to control and evaluate. I wanted a deterministic baseline first. Explicit matching signals give me predictable and explainable results. Once that baseline is measured, I can introduce semantic or LLM-based matching and determine whether it actually improves relevance.

---

# 41. Interview Question: What Was the Hardest Part?

> The main architectural challenge was separating responsibilities that were previously closer together. Instead of treating job search as one operation, I decomposed it into ingestion, normalization, deduplication, matching, ranking, and orchestration. That required defining clear interfaces between each layer.

A secondary practical challenge was dealing with test execution from PowerShell. One early mock test failed because of Python syntax used inside a one-line command. I changed the test execution approach to a PowerShell here-string and verified the orchestration successfully.

---

# 42. Interview Question: How Did You Test It?

> I tested incrementally. Each module was first compiled and imported. Then I created focused smoke tests for normalization, deduplication, matching, and ranking. Finally, I tested the unified search service with mock jobs and verified the complete pipeline and ranking order.

---

# 43. Interview Question: What Would You Improve Next?

> I would first integrate the V2 service into the existing application without breaking V1. After that I would improve skill normalization, add seniority matching, introduce persistent storage, and create a labelled evaluation dataset. Only after establishing that baseline would I evaluate semantic or LLM-based matching.

---

# 44. Final Technical Summary

The current V2 search architecture is:

```text
                 ┌─────────────────────┐
                 │     Job Sources     │
                 │                     │
                 │ Duunitori           │
                 │ Jobly               │
                 │ Työmarkkinatori     │
                 │ Work in Finland     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Source Registry   │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    Source Runner    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    Normalization    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    CanonicalJob     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    Deduplication    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │      Matching       │
                 │                     │
                 │ Title    35%        │
                 │ Skills   45%        │
                 │ Location 20%        │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │      Ranking        │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  V2SearchService    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Application / UI  │
                 └─────────────────────┘
```

The key architectural achievement is that the system has moved from a collection of source-specific search operations toward a **structured, layered job-search pipeline**.

---

# 45. Conclusion

CareerPilot AI V2 establishes a stronger foundation for intelligent job discovery.

The main improvement is not simply adding more features. It is establishing a cleaner architecture in which each part of the system has a clearly defined responsibility.

The system now has a complete V2 search pipeline:

```text
Source
→ Normalize
→ Canonicalize
→ Deduplicate
→ Match
→ Rank
→ Search Service
```

The deterministic foundation provides a transparent baseline that can be tested and evaluated.

The architecture is also designed for future evolution. Semantic matching, machine learning, richer candidate profiles, persistent storage, and more advanced ranking can be added without fundamentally replacing the ingestion architecture.

The next major milestone is therefore not another isolated search component, but **integration of the V2 search service into the existing CareerPilot AI application**.

The project demonstrates an incremental software-engineering approach:

> **Stabilize → modularize → normalize → match → rank → integrate → evaluate → improve.**

That is the central development story of CareerPilot AI V2.

# TalentLens AI
### Intelligent Candidate Ranking System

> Rank candidates the way a great recruiter would — 
> not by matching keywords, but by understanding 
> who truly fits the role.

---

## What is TalentLens AI?

TalentLens AI is an intelligent hiring system that 
ranks 1,00,000 candidates in under 90 seconds.

Instead of keyword matching, it understands:
- Career narrative and depth
- Skill proficiency levels
- Domain and industry fit
- Behavioral signals
- Availability and response signals

---

## Results

- 1,00,000 candidates scored
- Top 100 shortlisted
- Submission validated successfully

---

## Top 3 Candidates Found

| Rank | Candidate ID | Score | Title |
|------|-------------|-------|-------|
| 1 | CAND_0018499 | 99.01% | Senior ML Engineer |
| 2 | CAND_0079387 | 98.86% | AI Engineer |
| 3 | CAND_0002025 | 98.31% | Senior AI Engineer |

---

## How TalentLens AI Scores Candidates

| Dimension | Weight | What it checks |
|-----------|--------|----------------|
| Skills Match | 28% | Embeddings, Vector DB, NLP |
| Title Fit | 22% | AI/ML role or not |
| Career Quality | 18% | Product company vs consulting |
| Availability | 12% | Notice period, response rate |
| Experience | 10% | 5-9 years band |
| Education | 5% | IIT/NIT tier |
| GitHub Activity | 5% | Coding presence |

---

## Why Not Keyword Matching?

Normal keyword filter:
- Sees Python = match
- Cannot check skill depth
- Ignores GitHub, notice period
- Treats TCS same as Google

TalentLens AI:
- Understands actual skill depth
- Checks production ML experience
- Uses behavioral signals
- Separates product vs consulting companies

---

## How to Run

Install dependencies:
pip install requests scikit-learn pandas numpy

Run the ranking system:
python src/ranker.py

Validate submission:
python data/validate_submission.py output/submission.csv

---

## Project Structure
📁 TalentLens-AI
  │
  ├── 📁 src
  │     └── 📄 ranker.py
  │
  ├── 📁 data
  │     ├── 📄 candidates.jsonl
  │     └── 📄 validate_submission.py
  │
  ├── 📁 output
  │     └── 📄 submission.csv
  │
  └── 📄 README.md

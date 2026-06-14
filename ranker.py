

import json
import csv

INPUT_FILE  = "data/candidates.jsonl"
OUTPUT_FILE = "output/submission.csv"
EXCEL_FILE  = "output/results_excel.csv"

WEIGHTS = {
    "skills":       0.28,
    "title":        0.22,
    "career":       0.18,
    "availability": 0.12,
    "experience":   0.10,
    "education":    0.05,
    "github":       0.05,
}

SYNONYMS = {
    "machine learning": [
        "ml", "xgboost", "lightgbm", "scikit-learn",
        "sklearn", "catboost", "random forest"
    ],
    "python": ["python3", "py"],
    "nlp": [
        "natural language processing", "text mining",
        "transformers", "bert", "gpt"
    ],
    "embeddings": [
        "vector embeddings", "word2vec",
        "sentence transformers", "dense retrieval",
        "semantic search"
    ],
    "vector database": [
        "faiss", "pinecone", "weaviate", "qdrant",
        "milvus", "vector search", "vector store"
    ],
    "llms": [
        "large language model", "gpt-4",
        "llama", "mistral", "gemini", "claude"
    ],
    "retrieval": [
        "information retrieval", "dense retrieval",
        "sparse retrieval", "hybrid search", "bm25"
    ],
    "ranking": [
        "learning to rank", "reranking", "ltr",
        "ndcg", "mrr", "recommendation"
    ],
    "mlops": [
        "mlflow", "kubeflow", "airflow",
        "model deployment", "model serving"
    ],
}

GOOD_TITLES = [
    "ai engineer", "ml engineer",
    "machine learning engineer",
    "applied scientist", "applied ml",
    "research engineer", "senior ai engineer",
    "senior ml engineer", "data scientist",
    "senior data scientist", "nlp engineer",
    "search engineer", "ranking engineer",
    "recommendation engineer",
]

BAD_TITLES = [
    "marketing manager", "hr manager",
    "accountant", "sales executive",
    "operations manager", "civil engineer",
    "mechanical engineer", "graphic designer",
    "content writer", "customer support",
]

CONSULTING_FIRMS = [
    "tcs", "infosys", "wipro", "accenture",
    "cognizant", "capgemini", "hcl",
    "tech mahindra", "mphasis", "hexaware"
]

# ── Functions ─────────────────────────────────────────

def normalize(skill_name):
    skill_lower = skill_name.lower().strip()
    for standard, aliases in SYNONYMS.items():
        if skill_lower == standard or skill_lower in aliases:
            return standard
    return skill_lower

def score_skills(candidate):
    required = [
        "embeddings", "vector database", "retrieval",
        "ranking", "machine learning", "python", "nlp"
    ]
    bonus_skills = ["llms", "mlops", "spark", "fastapi"]

    total = 0
    max_possible = len(required) * 3.0

    cand_skills = {}
    for skill in candidate.get("skills", []):
        name = normalize(skill.get("name", ""))
        proficiency = skill.get("proficiency", "beginner")
        endorsements = min(skill.get("endorsements", 0), 50)
        duration = min(skill.get("duration_months", 0), 60)

        prof_score = {
            "beginner":     0.3,
            "intermediate": 0.6,
            "advanced":     0.85,
            "expert":       1.0
        }.get(proficiency, 0.3)

        cand_skills[name] = {
            "prof":    prof_score,
            "endorse": endorsements,
            "months":  duration
        }

    for req in required:
        if req in cand_skills:
            info = cand_skills[req]
            base = info["prof"] * 2.0
            endorse_bonus = (info["endorse"] / 50) * 0.5
            duration_bonus = (info["months"] / 60) * 0.5
            total += base + endorse_bonus + duration_bonus

    for bonus in bonus_skills:
        if bonus in cand_skills:
            total += 0.3

    assessments = candidate.get(
        "redrob_signals", {}
    ).get("skill_assessment_scores", {})

    for skill_name, score in assessments.items():
        name = normalize(skill_name)
        if name in [normalize(r) for r in required]:
            total += (score / 100) * 0.5

    return max(0.0, min(1.0, total / max_possible))

def score_title(candidate):
    current = candidate.get(
        "profile", {}
    ).get("current_title", "").lower()

    score = 0.0

    for good in GOOD_TITLES:
        if good in current:
            score = 1.0
            break

    for bad in BAD_TITLES:
        if bad in current:
            return 0.0

    for job in candidate.get("career_history", [])[:3]:
        title = job.get("title", "").lower()
        for good in GOOD_TITLES:
            if good in title:
                score = max(score, 0.5)
                break

    return score

def score_career(candidate):
    career = candidate.get("career_history", [])
    if not career:
        return 0.2

    total_months = 0
    product_months = 0
    ml_jobs = 0

    for job in career:
        months = job.get("duration_months", 0)
        company = job.get("company", "").lower()
        description = job.get("description", "").lower()
        total_months += months

        is_consulting = any(
            firm in company
            for firm in CONSULTING_FIRMS
        )
        if not is_consulting:
            product_months += months

        ml_words = [
            "model", "deployed", "production",
            "embedding", "ranking", "recommendation",
            "retrieval", "pipeline", "inference", "training"
        ]
        ml_count = sum(
            1 for w in ml_words if w in description
        )
        if ml_count >= 3:
            ml_jobs += 1

    if total_months > 0:
        product_ratio = product_months / total_months
    else:
        product_ratio = 0

    ml_ratio = ml_jobs / max(len(career), 1)
    final = (product_ratio * 0.6) + (ml_ratio * 0.4)
    return round(final, 3)

def score_experience(candidate):
    years = candidate.get(
        "profile", {}
    ).get("years_of_experience", 0)

    if 5 <= years <= 9:
        return 1.0
    elif years < 5:
        gap = 5 - years
        return max(0.1, 1.0 - gap * 0.18)
    else:
        gap = years - 9
        return max(0.5, 1.0 - gap * 0.06)

def score_availability(candidate):
    signals = candidate.get("redrob_signals", {})
    score = 0.0

    if signals.get("open_to_work_flag", False):
        score += 0.35

    notice = signals.get("notice_period_days", 90)
    if notice <= 15:
        score += 0.30
    elif notice <= 30:
        score += 0.20
    elif notice <= 60:
        score += 0.10

    response = signals.get("recruiter_response_rate", 0)
    score += response * 0.20

    last_active = signals.get("last_active_date", "")
    if last_active:
        try:
            from datetime import date
            last = date.fromisoformat(last_active)
            today = date(2026, 6, 13)
            days_ago = (today - last).days
            if days_ago <= 7:
                score += 0.15
            elif days_ago <= 30:
                score += 0.08
            elif days_ago > 60:
                score -= 0.10
        except:
            pass

    return max(0.0, min(1.0, score))

def score_education(candidate):
    score = 0.3
    for edu in candidate.get("education", []):
        tier = edu.get("tier", "unknown")
        field = edu.get("field_of_study", "").lower()
        degree = edu.get("degree", "").lower()

        tier_score = {
            "tier_1": 1.0,
            "tier_2": 0.75,
            "tier_3": 0.50,
            "tier_4": 0.25,
        }.get(tier, 0.3)

        field_bonus = 0
        if any(f in field for f in [
            "computer", "ai", "machine learning",
            "data", "information"
        ]):
            field_bonus = 0.2

        degree_bonus = 0
        if "ph" in degree:
            degree_bonus = 0.3
        elif "master" in degree or "m.tech" in degree:
            degree_bonus = 0.1

        edu_score = tier_score + field_bonus + degree_bonus
        score = max(score, edu_score)

    return min(1.0, score)

def score_github(candidate):
    gh = candidate.get(
        "redrob_signals", {}
    ).get("github_activity_score", -1)
    if gh < 0:
        return 0.2
    return gh / 100

def get_penalty(candidate):
    penalty = 0.0
    title = candidate.get(
        "profile", {}
    ).get("current_title", "").lower()

    for bad in BAD_TITLES:
        if bad in title:
            penalty += 0.50
            break

    career = candidate.get("career_history", [])
    if career:
        consulting_count = sum(
            1 for job in career
            if any(
                firm in job.get("company", "").lower()
                for firm in CONSULTING_FIRMS
            )
        )
        if consulting_count == len(career):
            penalty += 0.20

    return penalty

# ── Main Function ─────────────────────────────────────

def rank_one_lakh():
    print("=" * 50)
    print("  TalentLens AI")
    print("  Processing 1,00,000 candidates...")
    print("=" * 50)

    all_results = []
    count = 0

    with open(INPUT_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                candidate = json.loads(line)

                # Scores
                s_skills = score_skills(candidate)
                s_title  = score_title(candidate)
                s_career = score_career(candidate)
                s_avail  = score_availability(candidate)
                s_exp    = score_experience(candidate)
                s_edu    = score_education(candidate)
                s_github = score_github(candidate)

                # Weighted sum
                raw = (
                    s_skills * WEIGHTS["skills"]       +
                    s_title  * WEIGHTS["title"]        +
                    s_career * WEIGHTS["career"]       +
                    s_avail  * WEIGHTS["availability"] +
                    s_exp    * WEIGHTS["experience"]   +
                    s_edu    * WEIGHTS["education"]    +
                    s_github * WEIGHTS["github"]
                )

                # Penalty
                penalty = get_penalty(candidate)
                final = raw * (1 - penalty)

                # Match label
                if final >= 0.85:
                    label = "Strong Match"
                elif final >= 0.70:
                    label = "Good Match"
                elif final >= 0.50:
                    label = "Partial Match"
                else:
                    label = "Weak Match"

                # Current title
                curr_title = candidate.get(
                    "profile", {}
                ).get("current_title", "")

                # Experience
                exp_years = candidate.get(
                    "profile", {}
                ).get("years_of_experience", 0)

                all_results.append({
                    "candidate_id": candidate["candidate_id"],
                    "score":        round(final, 4),
                    "title":        curr_title,
                    "exp_years":    exp_years,
                    "s_skills":     round(s_skills, 2),
                    "s_title":      round(s_title, 2),
                    "s_career":     round(s_career, 2),
                    "s_avail":      round(s_avail, 2),
                    "s_exp":        round(s_exp, 2),
                    "s_edu":        round(s_edu, 2),
                    "s_github":     round(s_github, 2),
                    "label":        label,
                })

                count += 1
                if count % 10000 == 0:
                    print(f"  Processed {count:,}...")

            except Exception:
                continue

    print(f"\n  Total: {count:,} candidates scored")
    print("  Sorting...")

    # Sort
    all_results.sort(
        key=lambda x: (-x["score"], x["candidate_id"])
    )

    # Top 100
    top100 = all_results[:100]

    
    for i in range(1, len(top100)):
        if top100[i]["score"] >= top100[i-1]["score"]:
            top100[i]["score"] = round(
                top100[i-1]["score"] - 0.0001, 4
            )

    # ── File 1: submission.csv (for validation) ──
    print("  Saving submission.csv...")
    with open(OUTPUT_FILE, "w",
              newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

       
        writer.writerow([
            "candidate_id",
            "rank",
            "score",
            "reasoning",
        ])

        for rank, r in enumerate(top100, 1):
            reasoning = (
                f"{r['title']} | "
                f"{r['exp_years']}y exp | "
                f"skills={r['s_skills']} | "
                f"title={r['s_title']} | "
                f"avail={r['s_avail']} | "
                f"{r['label']}"
            )
            writer.writerow([
                r["candidate_id"],
                rank,
                r["score"],
                reasoning,
            ])

    # ── File 2: results_excel.csv  ──
    print("  Saving results_excel.csv...")
    with open(EXCEL_FILE, "w",
              newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        
        writer.writerow([
            "Rank",
            "Candidate ID",
            "Final Score",
            "Match Label",
            "Current Title",
            "Experience (Years)",
            "Skills Score",
            "Title Score",
            "Career Score",
            "Availability Score",
            "Experience Score",
            "Education Score",
            "GitHub Score",
        ])

        for rank, r in enumerate(top100, 1):
            writer.writerow([
                rank,
                r["candidate_id"],
                f"{r['score']*100:.1f}%",
                r["label"],
                r["title"],
                r["exp_years"],
                f"{r['s_skills']*100:.0f}%",
                f"{r['s_title']*100:.0f}%",
                f"{r['s_career']*100:.0f}%",
                f"{r['s_avail']*100:.0f}%",
                f"{r['s_exp']*100:.0f}%",
                f"{r['s_edu']*100:.0f}%",
                f"{r['s_github']*100:.0f}%",
            ])

    print("\n" + "=" * 50)
    print("  TalentLens AI — DONE!")
    print(f"  Validator: output/submission.csv")
    print(f"  Excel:     output/results_excel.csv")
    print("=" * 50)

    # Top 10 preview
    print("\nTop 10:")
    print("─" * 50)
    for i, r in enumerate(top100[:10], 1):
        print(f"#{i:2d} {r['candidate_id']} "
              f"[{r['score']}] {r['label']}")
        print(f"     {r['title']} | "
              f"{r['exp_years']}y exp")
        print()


if __name__ == "__main__":
    rank_one_lakh()
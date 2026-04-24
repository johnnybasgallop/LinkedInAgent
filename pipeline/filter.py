"""
Stage 3 — LLM Filter
Sends job descriptions + resume variants to Claude Haiku.
Returns only jobs that are a strong match (score >= 7/10),
along with which resume to use and a one-line reason.
"""

import json
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

_MODEL    = "claude-sonnet-4-6"
_MIN_SCORE = 6

_SYSTEM_PROMPT = """\
You are a strict, realistic technical recruiter. You must evaluate job fit based ONLY on \
what is explicitly written in the candidate's resume. Do not infer, assume, or extrapolate \
any skills or experience not directly stated.

## Candidate profile (from resume)
- Total experience: ~4 years across 2 jobs
- Job 1: Software/Fullstack Engineer at Axalt (UK) — May 2022 to Sep 2024
- Job 2: Software/Backend Engineer at Bluefin Automations (LA) — Oct 2024 to Feb 2026
- Confirmed languages/frameworks: Python (FastAPI, Django), Node.js/Express, \
Next.js, React, TypeScript, JavaScript
- Confirmed data/infra: PostgreSQL, Redis, MySQL, MongoDB, Docker, AWS, \
AWS Lambda, Celery, Apache Airflow, CI/CD pipelines, Git
- Confirmed concepts: REST APIs, microservices, event-driven architecture, \
role-based access control, Stripe integration, data pipelines
- NOT on any resume: Go, Rust, Java, C#, Kotlin, Swift, React Native, \
Flutter, mobile development, Kubernetes, Terraform, ML/AI frameworks

## Seniority rules — apply these strictly, no exceptions
- Staff / Principal / Lead / Head of / Director / VP / Manager \
→ MAX score 3. These require 7-10+ YOE. A 4 YOE candidate is not credible.
- Senior Engineer (any flavour) \
→ MAX score 7. Only award 7 if the tech stack is a near-exact match. \
Score 5-6 if it is a partial match or requires tech not on the resume.
- Everything else (Software Engineer, SWE II, Mid-level, Associate, Junior) \
→ Score freely (1-10) based purely on tech stack and requirements match.

Be selective. A score of 7 should mean "genuinely competitive applicant", \
not "could possibly apply".
"""

_USER_PROMPT_TEMPLATE = """\
Evaluate the {num_jobs} job postings below against the candidate's {num_resumes} resume \
variants. The candidate has ~4 years of experience. Score each job 1-10 following the \
seniority rules and tech stack constraints in the system prompt.

## My Resume Variants

{resumes_block}

## Job Postings

{jobs_block}

## Instructions

Respond with a JSON array only — no markdown, no explanation outside the JSON.
Score every job — include ALL {num_jobs} jobs in your response, regardless of score.
Each element should follow this schema exactly:
{{
  "id": "<job id string>",
  "score": <integer 1-10>,
  "best_resume": "<resume filename stem>",
  "reason": "<one concise sentence explaining the match or mismatch>"
}}
"""


def _build_resumes_block(resumes: dict[str, str]) -> str:
    blocks = []
    for name, text in resumes.items():
        blocks.append(f"### {name}\n{text}")
    return "\n\n".join(blocks)


def _build_jobs_block(jobs: list[dict]) -> str:
    blocks = []
    for i, job in enumerate(jobs, 1):
        blocks.append(
            f"### Job {i} (id: {job['id']})\n"
            f"**{job['title']}** @ {job['company']}\n"
            f"{job['location']} | {job['posted']}\n"
            f"{job['url']}\n\n"
            f"{job.get('description', 'No description available.')}"
        )
    return "\n\n---\n\n".join(blocks)


def _parse_response(raw: str) -> list[dict]:
    """Extract the JSON array from the model response."""
    raw = raw.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def filter_jobs(jobs: list[dict], resumes: dict[str, str]) -> list[dict]:
    """
    Run all jobs through Claude Haiku and return ALL jobs with scores attached.
    Caller is responsible for filtering by score threshold.
    Each returned job dict is enriched with: score, best_resume, reason.
    """
    if not jobs:
        return []

    api_key = os.environ.get("CLAUDE_CODE_API_KEY")
    if not api_key:
        raise EnvironmentError("CLAUDE_CODE_API_KEY not set in environment / .env")

    client = anthropic.Anthropic(api_key=api_key)

    prompt = _USER_PROMPT_TEMPLATE.format(
        num_resumes=len(resumes),
        num_jobs=len(jobs),
        resumes_block=_build_resumes_block(resumes),
        jobs_block=_build_jobs_block(jobs),
    )

    print(f"\n[Stage 3] Sending {len(jobs)} jobs to Claude ({_MODEL}) for filtering...")

    message = client.messages.create(
        model=_MODEL,
        max_tokens=8192,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text
    scores = _parse_response(raw)

    # Enrich every job dict with Claude's scoring data
    score_index = {s["id"]: s for s in scores}
    scored = []
    for job in jobs:
        if job["id"] in score_index:
            job.update({
                "score":       score_index[job["id"]]["score"],
                "best_resume": score_index[job["id"]]["best_resume"],
                "reason":      score_index[job["id"]]["reason"],
            })
            scored.append(job)

    print(f"[Stage 3] {sum(1 for j in scored if j['score'] >= _MIN_SCORE)}/{len(scored)} jobs scored >= {_MIN_SCORE}.")

    scored.sort(key=lambda j: j["score"], reverse=True)
    return scored

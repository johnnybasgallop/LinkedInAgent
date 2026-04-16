import json
import subprocess
from datetime import datetime


def _greeting(count: int) -> str:
    now = datetime.now()
    date_str = now.strftime("%A, %B %-d")
    time_str = now.strftime("%H:%M")
    noun = "match" if count == 1 else "matches"
    return (
        f"*Hello Sir*\n\n"
        f"I've found *{count}* fresh {noun} for you today.\n"
        f"_{date_str}  ·  {time_str}_\n"
        f"━━━━━━━━━━━━━━━"
    )


def _format_job(job: dict) -> str:
    score   = job["score"]
    title   = job["title"]
    company = job["company"]
    loc     = job.get("location", "") or ""
    posted  = job.get("posted", "") or ""
    resume  = job["best_resume"]
    reason  = job["reason"]
    url     = job["url"]

    lines = [
        f"*[{score}/10]*  *{title}*",
        f"_{company}_",
    ]
    meta = "  ·  ".join(p for p in (loc, posted) if p)
    if meta:
        lines.append(meta)
    lines.append("")
    lines.append(f"*Best resume*  ```{resume}```")
    lines.append("")
    lines.append(f"_{reason}_")
    lines.append("")
    lines.append(url)
    return "\n".join(lines)


def send_messages(phone_number: str, jobs: list[dict]):
    if not jobs:
        print("[WhatsApp] no jobs to send, skipping.")
        return

    messages = [_greeting(len(jobs))] + [_format_job(j) for j in jobs]

    try:
        result = subprocess.run(
            ["node", "pipeline/messaging/send_whatsapp.js", phone_number],
            input=json.dumps(messages),
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    send_messages(
        phone_number="+447592515298",
        jobs=[
            {
                "score": 9,
                "title": "Senior Backend Engineer",
                "company": "Acme Corp",
                "location": "Remote (US)",
                "posted": "2 days ago",
                "best_resume": "fullstack",
                "reason": "Python/FastAPI/Postgres stack is a near-exact match.",
                "url": "https://linkedin.com/jobs/view/123",
            },
        ],
    )

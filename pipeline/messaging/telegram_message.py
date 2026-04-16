import html
import os
from datetime import datetime

import telebot
from dotenv import load_dotenv
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv()


def _greeting(count: int) -> str:
    now = datetime.now()
    date_str = now.strftime("%A, %B %-d")
    time_str = now.strftime("%H:%M")
    noun = "match" if count == 1 else "matches"
    return (
        f"<b><u>Hello Sir</u></b>\n\n"
        f"I've found <b>{count}</b> fresh {noun} for you today.\n"
        f"<blockquote><i>{date_str}  ·  {time_str}</i></blockquote>\n"
        f"━━━━━━━━━━━━━━━"
    )


def _format_job(job: dict) -> str:
    score   = job["score"]
    title   = html.escape(job["title"])
    company = html.escape(job["company"])
    loc     = html.escape(job.get("location", "") or "")
    posted  = html.escape(job.get("posted", "") or "")
    resume  = html.escape(job["best_resume"])
    reason  = html.escape(job["reason"])

    lines = [
        f"<code>{score}/10</code>  <b>{title}</b>",
        f"<i>{company}</i>",
    ]
    meta = "  ·  ".join(p for p in (loc, posted) if p)
    if meta:
        lines.append(meta)
    lines.append("")
    lines.append(f"<b>Best resume</b>  <code>{resume}</code>")
    lines.append("")
    lines.append(f"<blockquote><i>{reason}</i></blockquote>")
    return "\n".join(lines)


def _job_markup(job: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("View job", url=job["url"]))
    return kb


def send_messages(chat_id: str, jobs: list[dict]):
    if not jobs:
        print("[Telegram] no jobs to send, skipping.")
        return

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN not set in environment / .env")

    bot = telebot.TeleBot(token)

    try:
        bot.send_message(chat_id, _greeting(len(jobs)), parse_mode="HTML")
        print("[Telegram] sent greeting")
    except Exception as e:
        print(f"[Telegram] failed to send greeting: {e}")

    for i, job in enumerate(jobs, 1):
        try:
            bot.send_message(
                chat_id,
                _format_job(job),
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=_job_markup(job),
            )
            print(f"[Telegram] sent {i}/{len(jobs)}")
        except Exception as e:
            print(f"[Telegram] failed to send {i}: {e}")


if __name__ == "__main__":
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not chat_id:
        raise EnvironmentError("TELEGRAM_CHAT_ID not set in environment / .env")
    send_messages(
        chat_id=chat_id,
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

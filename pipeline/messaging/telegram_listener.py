"""
Long-running Telegram bot listener — catches callback-button presses from
notification messages (currently just the "Applied" button).

Run with:  ./venv/bin/python -m pipeline.messaging.telegram_listener
"""

import os

import telebot
from dotenv import load_dotenv

from pipeline.applications.notion_sync import create_application
from pipeline.cache import load_cache

load_dotenv()


def _handle_applied(job_id: str) -> str:
    cache = load_cache()
    job = cache.get(job_id)
    if not job:
        print(f"[Applied] job_id={job_id} — not found in cache")
        return "Job not found in cache"

    print("-" * 60)
    print(f"[Applied] {job.get('title')} @ {job.get('company')}")
    print(f"  id:       {job_id}")
    print(f"  score:    {job.get('score')}/10")
    print(f"  resume:   {job.get('best_resume')}")
    print(f"  location: {job.get('location')}")
    print(f"  posted:   {job.get('posted')}")
    print(f"  reason:   {job.get('reason')}")
    print(f"  url:      {job.get('url')}")
    print("-" * 60)

    if create_application(job):
        title = job.get("title") or "position"
        msg = f"Applied to {title}"
        return msg if len(msg) <= 200 else msg[:197] + "..."
    return "Failed to sync with Notion"


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN not set in environment / .env")

    bot = telebot.TeleBot(token)

    @bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("applied:"))
    def on_applied(call):
        job_id = call.data.split(":", 1)[1]
        toast = _handle_applied(job_id)
        bot.answer_callback_query(call.id, toast)

    print("[Telegram listener] polling for callbacks… (Ctrl+C to stop)")
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()

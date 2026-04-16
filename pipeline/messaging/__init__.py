"""
Messaging dispatcher — routes matched-job notifications to the platform
configured by MESSAGING_PLATFORM in config.py.
"""

from config import MESSAGING_PLATFORM, TELEGRAM_CHAT_ID, WHATSAPP_PHONE


def send_messages(jobs: list[dict]):
    if not jobs:
        print("[Messaging] no jobs to send, skipping.")
        return

    if MESSAGING_PLATFORM == "telegram":
        from .telegram_message import send_messages as _send

        if not TELEGRAM_CHAT_ID:
            raise EnvironmentError("TELEGRAM_CHAT_ID not set in environment / .env")
        _send(TELEGRAM_CHAT_ID, jobs)

    elif MESSAGING_PLATFORM == "whatsapp":
        from .whatsapp_message import send_messages as _send

        _send(WHATSAPP_PHONE, jobs)

    else:
        raise ValueError(
            f"Unknown MESSAGING_PLATFORM: {MESSAGING_PLATFORM!r}. "
            f"Expected 'telegram' or 'whatsapp'."
        )

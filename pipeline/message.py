import json
import subprocess


def send_messages(phone_number: str, messages: list[str]):
    if not messages:
        print("[WhatsApp] no messages to send, skipping.")
        return

    try:
        result = subprocess.run(
            ["node", "pipeline/send_whatsapp.js", phone_number],
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
        messages=[
            "This is automated message 1 - lol",
            "This is automated message 2 - lol",
        ],
    )

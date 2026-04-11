import subprocess

def send_message(phone_number: str, message: str):
    try:
        result = subprocess.run(
            ["node", "pipeline/send_whatsapp.js", phone_number, message],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)

    except Exception as e:
        print(e)

if __name__ == "__main__":
    send_message(phone_number="+447592515298", message="testing yo yo yo")

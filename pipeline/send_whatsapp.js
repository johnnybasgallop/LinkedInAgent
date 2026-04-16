const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");

const number = process.argv[2];

let stdinBuf = "";
process.stdin.on("data", (chunk) => {
  stdinBuf += chunk;
});
process.stdin.on("end", () => {
  let messages;
  try {
    messages = JSON.parse(stdinBuf);
  } catch (err) {
    console.error("failed to parse messages JSON from stdin:", err.message);
    process.exit(1);
  }
  if (!Array.isArray(messages) || messages.length === 0) {
    console.log("no messages to send");
    process.exit(0);
  }
  start(messages);
});

function start(messages) {
  const client = new Client({
    authStrategy: new LocalAuth({ dataPath: ".wwebjs_auth" }),
  });

  client.on("qr", (qr) => {
    qrcode.generate(qr, { small: true });
  });

  client.once("ready", async () => {
    console.log("client is ready");
    const chatId = `${number.replace("+", "")}@c.us`;

    for (let i = 0; i < messages.length; i++) {
      try {
        await client.sendMessage(chatId, messages[i]);
        console.log(`message ${i + 1}/${messages.length} sent`);
      } catch (err) {
        console.error(`failed to send message ${i + 1}:`, err.message);
      }
    }

    setTimeout(async () => {
      await client.destroy();
    }, 5000);
  });

  client.initialize();
}

const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");

const number = process.argv[2];
const message = process.argv[3];

const client = new Client({
  authStrategy: new LocalAuth({ dataPath: ".wwebjs_auth" }),
});

client.on("qr", (qr) => {
  qrcode.generate(qr, { small: true });
});

client.once("ready", async () => {
  console.log("client is ready");
  try {
    const me = client.info.wid._serialized;
    await client.sendMessage(me, "testing things out");
    console.log("message sent");
  } catch (err) {
    console.error("failed to send message:", err.message);
  } finally {
    setTimeout(async () => {
      await client.destroy();
    }, 5000);
  }
});

client.initialize();

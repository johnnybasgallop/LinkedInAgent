const { Client } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");

const number = process.argv[2];
const message = process.argv[3];

console.log(number);
console.log(message);

const client = new Client();

client.once("ready", () => {
  console.log("client is ready");
});

client.on("qr", (qr) => {
  qrcode.generate(qr, { small: true });
});

console.log("ready to go");
client.initialize();

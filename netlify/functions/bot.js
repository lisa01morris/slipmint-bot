exports.handler = async (event) => {
  const TOKEN = process.env.BOT_TOKEN;
  const { message } = JSON.parse(event.body);
  
  if (!message || !message.text) {
    return { statusCode: 200, body: 'OK' };
  }
  
  const chatId = message.chat.id;
  const text = message.text;
  let reply = '';
  
  if (text === '/start') {
    reply = `🛡️ *SlipMint Risk Calculator*

*Commands:*
/risk — Calculate lot size
/rules — $60 framework
/help — How to use

*Educational only. Not financial advice.*`;
  }
  else if (text === '/help') {
    reply = `📚 *How to Use*

Send 3 numbers:
risk stop_distance pip_value

*Example:*
20 3.00 0.10

Result: 6 lots`;
  }
  else if (text === '/rules') {
    reply = `🛡️ *$60 FRAMEWORK*

• $60 daily budget
• $20 risk per trade
• 3 trades max
• 1:2 minimum RR
• 30min cooldown after loss`;
  }
  else if (text === '/risk') {
    reply = `💰 Send your numbers:

20 3.00 0.10

Format: risk stop pip_value`;
  }
  else if (text.trim().split(/\s+/).length === 3) {
    const parts = text.trim().split(/\s+/);
    const risk = parseFloat(parts[0]);
    const stop = parseFloat(parts[1]);
    const pip = parseFloat(parts[2]);
    const lots = risk / (stop * pip);
    const lotsR = Math.floor(lots);
    const actual = lotsR * stop * pip;
    
    reply = `🧮 *RESULT*

Risk: $${risk}
Stop: $${stop}
Pip: $${pip}

Lot Size: ${lots.toFixed(2)}
→ Use: *${lotsR} lots*

Actual Risk: $${actual.toFixed(2)}
${actual <= 20 ? '✅ Within $20' : '⚠️ Over $20'}

Target: $${(stop * 2).toFixed(2)} (1:2 RR)

*Educational only.*`;
  }
  else {
    reply = `Type /start for commands.`;
  }
  
  await fetch(`https://api.telegram.org/bot${TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      chat_id: chatId, 
      text: reply, 
      parse_mode: 'Markdown' 
    })
  });
  
  return { statusCode: 200, body: 'OK' };
};

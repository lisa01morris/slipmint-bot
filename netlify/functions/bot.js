exports.handler = async (event) => {
  const TOKEN = process.env.TELEGRAM_BOT_TOKEN;

  if (!event.body) {
    return { statusCode: 200, body: 'OK' };
  }

  let update;
  try {
    update = JSON.parse(event.body);
  } catch {
    return { statusCode: 200, body: 'OK' };
  }

  // Handle inline button presses (callback_query)
  if (update.callback_query) {
    const cq = update.callback_query;
    const chatId = cq.message.chat.id;
    const data = cq.data;

    // Dismiss the loading spinner on the button
    await tgPost(TOKEN, 'answerCallbackQuery', { callback_query_id: cq.id });

    if (data === 'calc_risk') {
      await sendMessage(TOKEN, chatId,
        `💰 *Calculate Risk*\n\nSend 3 numbers:\n\n\`risk stop_distance pip_value\`\n\n*Example:* \`20 3.00 0.10\`\n→ Lot size: 6 lots\n\n_Educational only. Not financial advice._`
      );
    } else if (data === 'show_rules') {
      await sendMessage(TOKEN, chatId,
        `🛡️ *$60 Framework*\n\n• $60 daily budget\n• $20 risk per trade\n• 3 trades max\n• 1:2 minimum RR\n• 30min cooldown after loss`
      );
    } else if (data === 'show_journal') {
      await sendMessage(TOKEN, chatId,
        `📊 *Trade Journal*\n\nUse /journal to see the trade log template.\n\n_Full journal storage is coming in the next update._`
      );
    }

    return { statusCode: 200, body: 'OK' };
  }

  // Handle regular text messages
  const message = update.message;
  if (!message || !message.text) {
    return { statusCode: 200, body: 'OK' };
  }

  const chatId = message.chat.id;
  // Strip bot username suffix (e.g. /start@SlipMintBot)
  const text = message.text.trim().replace(/@\w+$/, '');

  if (text === '/start') {
    await sendMessage(
      TOKEN,
      chatId,
      `🛡️ *SlipMint Risk Calculator*\n\nYour XAUUSD gold trading companion.\n\nChoose an option below:`,
      {
        inline_keyboard: [
          [
            { text: '🧮 Calculate Risk', callback_data: 'calc_risk' },
            { text: '📋 View Rules', callback_data: 'show_rules' }
          ],
          [
            { text: '📊 My Journal', callback_data: 'show_journal' }
          ]
        ]
      }
    );
    return { statusCode: 200, body: 'OK' };
  }

  if (text === '/help') {
    await sendMessage(TOKEN, chatId,
      `📚 *How to Use*\n\nSend 3 numbers in one message:\n\`risk stop_distance pip_value\`\n\n*Example:*\n\`20 3.00 0.10\`\n\n→ Result: 6 lots\n\n*Commands:*\n/risk — Calculate lot size\n/rules — $60 framework\n/journal — Trade log template\n/streak — Consistency tracker\n/help — This message`
    );
    return { statusCode: 200, body: 'OK' };
  }

  if (text === '/rules') {
    await sendMessage(TOKEN, chatId,
      `🛡️ *$60 Framework*\n\n• $60 daily budget\n• $20 risk per trade\n• 3 trades max\n• 1:2 minimum RR\n• 30min cooldown after loss`
    );
    return { statusCode: 200, body: 'OK' };
  }

  if (text === '/risk') {
    await sendMessage(TOKEN, chatId,
      `💰 *Calculate Lot Size*\n\nSend 3 numbers:\n\n\`risk stop_distance pip_value\`\n\n*Example:*\n\`20 3.00 0.10\`\n→ Result: 6 lots`
    );
    return { statusCode: 200, body: 'OK' };
  }

  if (text === '/journal') {
    await sendMessage(TOKEN, chatId,
      `📓 *Trade Journal Template*\n\nLog your next trade like this:\n\n• *Pair:* XAUUSD\n• *Direction:* BUY / SELL\n• *Entry:* _price_\n• *Stop Loss:* _price_\n• *Take Profit:* _price_\n• *Lot Size:* _x lots_\n• *Result:* WIN / LOSS / BE\n• *Notes:* _what you observed_\n\n_Persistent journal storage is coming in the next update — your logs will survive redeploys._`
    );
    return { statusCode: 200, body: 'OK' };
  }

  if (text === '/streak') {
    await sendMessage(TOKEN, chatId,
      `🔥 *Consistency Streak Tracker*\n\nStick to the $60 framework every day to earn:\n\n🥉 *Bronze* — 5 consecutive days\n🥈 *Silver* — 15 consecutive days\n🥇 *Gold* — 30 consecutive days\n\n_Streak tracking with persistent storage is coming in the next update._`
    );
    return { statusCode: 200, body: 'OK' };
  }

  // Risk calculation: three numbers on one line
  const parts = text.split(/\s+/);
  if (parts.length === 3 && parts.every(p => !isNaN(parseFloat(p)))) {
    const risk = parseFloat(parts[0]);
    const stop = parseFloat(parts[1]);
    const pip = parseFloat(parts[2]);

    if (stop === 0 || pip === 0) {
      await sendMessage(TOKEN, chatId, `⚠️ Stop distance and pip value cannot be zero.`);
      return { statusCode: 200, body: 'OK' };
    }

    const lots = risk / (stop * pip);
    const lotsRounded = Math.floor(lots);
    const actualRisk = lotsRounded * stop * pip;

    await sendMessage(TOKEN, chatId,
      `🧮 *Result*\n\nRisk: $${risk}\nStop: ${stop} pts\nPip value: $${pip}\n\nExact lots: ${lots.toFixed(2)}\n→ Use: *${lotsRounded} lots*\n\nActual risk: $${actualRisk.toFixed(2)}\n${actualRisk <= 20 ? '✅ Within $20 limit' : '⚠️ Exceeds $20 limit'}\n\nTarget profit (1:2 RR): $${(actualRisk * 2).toFixed(2)}\n\n_Educational only. Not financial advice._`
    );
    return { statusCode: 200, body: 'OK' };
  }

  // Default fallback
  await sendMessage(TOKEN, chatId,
    `Type /start to see the menu, or send /help for all commands.`
  );
  return { statusCode: 200, body: 'OK' };
};

async function tgPost(token, method, payload) {
  const res = await fetch(`https://api.telegram.org/bot${token}/${method}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

async function sendMessage(token, chatId, text, replyMarkup = null) {
  const payload = {
    chat_id: chatId,
    text,
    parse_mode: 'Markdown'
  };
  if (replyMarkup) {
    payload.reply_markup = replyMarkup;
  }
  return tgPost(token, 'sendMessage', payload);
}

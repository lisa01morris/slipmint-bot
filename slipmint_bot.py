
"""
SlipMint Risk Calculator Bot for Telegram
Built for XAUUSD traders using the $60/day framework
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token (get from @BotFather)
TOKEN = "YOUR_BOT_TOKEN_HERE"

# States for conversation
RISK, STOP_DISTANCE, PIP_VALUE, CONFIRM = range(4)

# ========== COMMAND HANDLERS ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    welcome_text = """
🛡️ *Welcome to SlipMint Risk Calculator*

I help you calculate position sizes for your $60/day framework.

*Available commands:*
/risk — Calculate lot size for your trade
/rules — Show the $60 framework rules
/journal — Log today's trades
/streak — Check your consistency streak
/help — How to use this bot

*Remember:*
• $60 daily budget
• $20 risk per trade
• 3 trades max
• 1:2 minimum risk/reward

*Educational purposes only. Not financial advice.*
    """

    keyboard = [
        [InlineKeyboardButton("🧮 Calculate Risk", callback_data='calc_risk')],
        [InlineKeyboardButton("📋 View Rules", callback_data='show_rules')],
        [InlineKeyboardButton("📊 My Journal", callback_data='show_journal')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help message"""
    help_text = """
📚 *How to Use SlipMint Calculator*

*1. Calculate Position Size:*
Type: /risk
Then enter:
• Your risk amount (max $20)
• Stop loss distance in USD (e.g., 3.00)
• Pip value per lot (e.g., 0.10 for micro lots)

*Example:*
Risk: $20
Stop: $3.00
Pip value: $0.10
Result: 6.6 micro lots → Round down to 6

*2. Log Your Trades:*
Type: /journal
Track your daily trades and lessons.

*3. Check Your Streak:*
Type: /streak
See how many days you've followed your rules.

*Need help?* Ask in the SlipMint community.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the $60 framework rules"""
    rules_text = """
🛡️ *THE $60 FRAMEWORK*

*Daily Budget:* $60 hard ceiling

*Per Trade:*
• Risk: $20 maximum
• Reward: $40 minimum (1:2 RR)
• Stop loss: Always set before entry

*Trade Limit:* 3 trades per day

*Time Window:* 12:00–16:00 GMT only

*Cooldown:* 30 minutes after ANY loss

*News Blackout:* No trades 15 min before/after CPI, NFP, FOMC

*Breakeven:* Move stop to entry at +0.5%

*Choppy Filter:* Skip ranging markets

*Position Sizing:*
Lot Size = $20 ÷ (Stop Distance × Pip Value)

*Educational purposes only.*
    """
    await update.message.reply_text(rules_text, parse_mode='Markdown')

# ========== RISK CALCULATOR CONVERSATION ==========

async def risk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start risk calculation"""
    await update.message.reply_text(
        "🧮 *Risk Calculator*\n\n"
        "How much are you risking on this trade? (Max $20)",
        parse_mode='Markdown'
    )
    return RISK

async def risk_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get risk amount"""
    try:
        risk = float(update.message.text)
        if risk > 20:
            await update.message.reply_text(
                "⚠️ *Warning:* Your risk exceeds $20 framework limit.\n"
                "I'll calculate it, but consider reducing to $20.",
                parse_mode='Markdown'
            )
        context.user_data['risk'] = risk
        await update.message.reply_text(
            "📏 *Stop Loss Distance*\n\n"
            "How far is your stop loss from entry? (in USD, e.g., 3.00)",
            parse_mode='Markdown'
        )
        return STOP_DISTANCE
    except ValueError:
        await update.message.reply_text("Please enter a valid number (e.g., 20)")
        return RISK

async def stop_distance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get stop distance"""
    try:
        stop = float(update.message.text)
        if stop <= 0:
            await update.message.reply_text("Stop distance must be greater than 0")
            return STOP_DISTANCE
        context.user_data['stop'] = stop
        await update.message.reply_text(
            "💰 *Pip Value*\n\n"
            "What's the pip value per lot?\n"
            "• Micro lot (0.01): $0.10\n"
            "• Mini lot (0.1): $1.00\n"
            "• Standard lot (1.0): $10.00",
            parse_mode='Markdown'
        )
        return PIP_VALUE
    except ValueError:
        await update.message.reply_text("Please enter a valid number (e.g., 3.00)")
        return STOP_DISTANCE

async def pip_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get pip value and calculate"""
    try:
        pip_val = float(update.message.text)
        context.user_data['pip_value'] = pip_val

        risk = context.user_data['risk']
        stop = context.user_data['stop']

        # Calculate lot size
        lot_size = risk / (stop * pip_val)
        lot_size_rounded = int(lot_size)  # Round down

        # Calculate actual risk with rounded lot size
        actual_risk = lot_size_rounded * stop * pip_val

        # Determine if within framework
        within_framework = risk <= 20 and actual_risk <= 20

        result_text = f"""
🧮 *RISK CALCULATION RESULT*

*Inputs:*
• Risk Amount: ${risk:.2f}
• Stop Distance: ${stop:.2f}
• Pip Value: ${pip_val:.2f}

*Calculation:*
Lot Size = ${risk:.2f} ÷ (${stop:.2f} × ${pip_val:.2f})
Lot Size = {lot_size:.2f} lots

*Recommended:*
🎯 **{lot_size_rounded} lots** (rounded down)

*Actual Risk:* ${actual_risk:.2f}

*Framework Check:*
{"✅ Within $20 limit" if within_framework else "⚠️ Exceeds $20 framework limit"}

*Next Steps:*
1. Set stop loss at ${stop:.2f} from entry
2. Set take profit at ${stop * 2:.2f} from entry (1:2 RR)
3. Only trade if setup is A+

*Educational purposes only.*
        """

        keyboard = [
            [InlineKeyboardButton("🔄 Calculate Again", callback_data='calc_risk')],
            [InlineKeyboardButton("📋 View Rules", callback_data='show_rules')],
            [InlineKeyboardButton("📊 Log to Journal", callback_data='log_journal')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(result_text, parse_mode='Markdown', reply_markup=reply_markup)
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("Please enter a valid number (e.g., 0.10)")
        return PIP_VALUE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text("Calculation cancelled. Type /risk to start again.")
    return ConversationHandler.END

# ========== JOURNAL HANDLER ==========

async def journal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show journal template"""
    journal_text = """
📊 *DAILY TRADE JOURNAL*

Copy this template and fill it in:

*Date:* [Today's date]
*Trades Taken:* [0-3]
*Risk Used:* [$X / $60]

*Trade 1:*
• Direction: [Long/Short]
• Entry: [$X]
• Stop: [$X]
• Target: [$X]
• Result: [Win/Loss/Breakeven]
• Lesson: [What did you learn?]

*Trade 2:*
[Same format]

*Trade 3:*
[Same format]

*Today's Lesson:*
[One thing you'll do differently tomorrow]

Send me your completed journal and I'll track your streak!
    """
    await update.message.reply_text(journal_text, parse_mode='Markdown')

async def streak_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show streak info"""
    streak_text = """
🔥 *CONSISTENCY STREAK*

Track your discipline, not your profits.

*What counts as a "good day":*
✅ Followed $60 budget
✅ Took 3 or fewer trades
✅ Used stop losses on every trade
✅ Waited for A+ setups
✅ Logged trades in journal

*Your streak builds when you:*
• Follow rules for 5 days → 🥉 Bronze
• Follow rules for 15 days → 🥈 Silver  
• Follow rules for 30 days → 🥇 Gold (Ready for live)

*Remember:* One rule break resets to zero.
That's the point. Discipline is binary.

Start your streak today. Type /journal
    """
    await update.message.reply_text(streak_text, parse_mode='Markdown')

# ========== CALLBACK HANDLERS ==========

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks"""
    query = update.callback_query
    await query.answer()

    if query.data == 'calc_risk':
        await query.message.reply_text(
            "🧮 *Risk Calculator*\n\n"
            "How much are you risking on this trade? (Max $20)",
            parse_mode='Markdown'
        )
        # Note: In production, you'd need to handle the conversation flow properly

    elif query.data == 'show_rules':
        await rules_command(update, context)

    elif query.data == 'show_journal':
        await journal_command(update, context)

    elif query.data == 'log_journal':
        await journal_command(update, context)

# ========== MAIN ==========

def main():
    """Start the bot"""
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler for risk calculator
    risk_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('risk', risk_start)],
        states={
            RISK: [MessageHandler(filters.TEXT & ~filters.COMMAND, risk_amount)],
            STOP_DISTANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, stop_distance)],
            PIP_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pip_value)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('rules', rules_command))
    application.add_handler(CommandHandler('journal', journal_command))
    application.add_handler(CommandHandler('streak', streak_command))
    application.add_handler(risk_conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler))

    # Start the bot
    print("SlipMint Risk Calculator Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()

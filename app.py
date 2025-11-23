from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackQueryHandler, ConversationHandler
)
import subprocess
import os
import logging
import shutil
import sys
import time
import json
import asyncio
import re
from datetime import datetime, timedelta
from colorama import init, Fore, Back, Style
import psutil

# Initialize colorama for colored logs
init(autoreset=True)

# Set up colorful logging
class ColorfulFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: Fore.CYAN + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
        logging.ERROR: Fore.RED + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
        logging.CRITICAL: Fore.RED + Back.WHITE + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + Style.RESET_ALL
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler with colorful formatter
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(ColorfulFormatter())
logger.addHandler(ch)

# Use environment variable for bot token
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '7855809575:AAGfScXgjxsGkuIOKWYkwpfr-u5CvyZ06wg')

# Project states for conversation handler
PROJECT_NAME, BOT_TOKEN, REQUIREMENTS, APP_PY, ADDITIONAL_FILES, BROADCAST_MESSAGE = range(6)

# Store user data and projects
user_projects = {}
user_sessions = {}
deployment_logs = {}
deployment_messages = {}  # Store message IDs for live updates
premium_users = {}  # Store premium users
banned_users = {} # Store banned users
admin_users = {}  # Store admin users
FREE_PREMIUM_MODE = False
MAINTENANCE_MODE = False

# Bot start time
BOT_START_TIME = datetime.now()

# M-PESA payment details
MPESA_NUMBER = "0111255045"
MPESA_AMOUNTS = {
    10: "1 week",
    50: "2 weeks",
    100: "unlimited"
}
MPESA_RECIPIENT = "Gibson Mbuani"

# Bot owner ID (replace with your actual Telegram user ID)
BOT_OWNER_ID = "7928993116"  # Example ID, replace with actual

# Developer info
DEVELOPER_INFO = {
    "name": "Tylor 💫Heis_Tech",
    "username": "@unknown_numeralx",
    "phone": "254111255045",
    "email": "heistech3@gmail.com",
    "support": "@unknown_numeralx"
}

# GIF URL for commands
GIF_URL = "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExMWVhZGY2amM0NjMxYjA0NT92NmlxbmZ3cWc4a3o0emRraTVrZ2RiOCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/WNVi7cLzDhGsrwdQxR/giphy.gif"

# Check Python environment
def get_python_environment():
    env_info = {
        'python_version': sys.version_info,
        'python_command': None,
        'pip_command': None
    }

    # Try different python commands
    python_commands = ['python3', 'python']
    pip_commands = ['pip3', 'pip', 'python3 -m pip', 'python -m pip']
    
    for py_cmd in python_commands:
        try:
            subprocess.run([py_cmd, '--version'], capture_output=True, check=True)
            env_info['python_command'] = py_cmd
            
            # Try to find a working pip command
            for pip_cmd in pip_commands:
                try:
                    if ' -m ' in pip_cmd:
                        # Handle python -m pip format
                        cmd_parts = pip_cmd.split(' ')
                        subprocess.run([env_info['python_command'], '-m', 'pip', '--version'], 
                                     capture_output=True, check=True)
                        env_info['pip_command'] = f"{env_info['python_command']} -m pip"
                    else:
                        subprocess.run([pip_cmd, '--version'], capture_output=True, check=True)
                        env_info['pip_command'] = pip_cmd
                    break
                except:
                    continue
            break
        except:
            continue

    # Fallback to basic commands if detection failed
    if not env_info['python_command']:
        env_info['python_command'] = 'python'
    if not env_info['pip_command']:
        env_info['pip_command'] = 'pip'
        
    return env_info

ENV_INFO = get_python_environment()

# Save data to files
def save_data():
    with open('user_projects.json', 'w') as f:
        json.dump(user_projects, f)
    with open('premium_users.json', 'w') as f:
        json.dump(premium_users, f)
    with open('banned_users.json', 'w') as f:
        json.dump(banned_users, f)
    with open('admin_users.json', 'w') as f:
        json.dump(admin_users, f)
    with open('bot_state.json', 'w') as f:
        json.dump({'free_premium_mode': FREE_PREMIUM_MODE, 'maintenance_mode': MAINTENANCE_MODE}, f)

# Load data from files
def load_data():
    global user_projects, premium_users, banned_users, admin_users, FREE_PREMIUM_MODE, MAINTENANCE_MODE
    try:
        with open('user_projects.json', 'r') as f:
            user_projects = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        user_projects = {}

    try:
        with open('premium_users.json', 'r') as f:
            premium_users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        premium_users = {}

    try:
        with open('banned_users.json', 'r') as f:
            banned_users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        banned_users = {}
        
    try:
        with open('admin_users.json', 'r') as f:
            admin_users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        admin_users = {}
        
    try:
        with open('bot_state.json', 'r') as f:
            state = json.load(f)
            FREE_PREMIUM_MODE = state.get('free_premium_mode', False)
            MAINTENANCE_MODE = state.get('maintenance_mode', False)
    except (FileNotFoundError, json.JSONDecodeError):
        FREE_PREMIUM_MODE = False
        MAINTENANCE_MODE = False

# Check if user is admin
def is_admin(user_id):
    user_id = str(user_id)
    return user_id == BOT_OWNER_ID or user_id in admin_users

# Check if user is premium with proper error handling
def is_premium_user(user_id):
    user_id = str(user_id)
    if user_id == BOT_OWNER_ID or FREE_PREMIUM_MODE:
        return True  # Bot owner always has premium, and so do all users in free premium mode

    if user_id not in premium_users:
        return False

    # Check if user data has the required fields
    user_data = premium_users[user_id]

    if 'expiry_date' not in user_data:
        logger.warning(f"User {user_id} has premium status but missing expiry_date. Removing premium access.")
        del premium_users[user_id]
        save_data()
        return False

    try:
        # Check if premium has expired
        expiry_date = datetime.fromisoformat(user_data['expiry_date'])

        if datetime.now() > expiry_date:
            # Premium expired, remove it and return False
            if user_id in premium_users:
                del premium_users[user_id]
                save_data()
            return False

        return True
    except (ValueError, KeyError) as e:
        logger.error(f"Error checking premium status for user {user_id}: {e}")
        # Remove invalid premium entry
        if user_id in premium_users:
            del premium_users[user_id]
            save_data()
        return False

# Check if user is banned
def is_banned_user(user_id):
    return str(user_id) in banned_users

# Check project limit
def check_project_limit(user_id):
    user_id = str(user_id)
    if is_premium_user(user_id) or FREE_PREMIUM_MODE:
        return True  # No limit for premium users and during free premium mode
    return len(user_projects.get(user_id, {})) < 1

# Get project status
def get_project_status(project_dir):
    pid_file = os.path.join(project_dir, "bot.pid")
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            # Check if process is running
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                # Verify it's the correct process
                if any('app.py' in cmd for cmd in process.cmdline()):
                    return "🟢 Running", pid
                else:
                    return "🔴 Stopped", None
            else:
                return "🔴 Stopped", None
        except (ValueError, FileNotFoundError, psutil.NoSuchProcess):
            return "🔴 Stopped", None
    return "🔴 Stopped", None

# Calculate expiry date based on amount
def calculate_expiry_date(amount):
    if amount == 10:
        return datetime.now() + timedelta(days=7)
    elif amount == 50:
        return datetime.now() + timedelta(days=14)
    elif amount == 100:
        return datetime.now() + timedelta(days=365*10)  # Use a large number of days
    else:
        return datetime.now() + timedelta(days=7)  # Default to 1 week

# Helper function to send an animation with a caption, handling different update types
async def send_animated_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    chat_id = update.effective_chat.id

    if update.callback_query:
        # Delete the previous message to avoid clutter
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=update.callback_query.message.message_id)
        except Exception as e:
            logger.warning(f"Failed to delete message: {e}")

    await context.bot.send_animation(
        chat_id=chat_id,
        animation=GIF_URL,
        caption=text,
        parse_mode='Markdown'
    )

# Broadcast a message to all users
async def broadcast_message(context: ContextTypes.DEFAULT_TYPE, message: str):
    user_list = list(user_projects.keys())
    for user_id in user_list:
        try:
            await context.bot.send_message(chat_id=int(user_id), text=f"📢 *BROADCAST MESSAGE*\n\n{message}", parse_mode='Markdown')
            await asyncio.sleep(0.1) # Small delay to avoid hitting API limits
        except Exception as e:
            logger.error(f"Failed to send broadcast to user {user_id}: {e}")

# Middleware to check for maintenance mode
async def maintenance_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if MAINTENANCE_MODE and not is_admin(update.effective_user.id):
        await update.effective_message.reply_text("👷‍♂️ The bot is currently undergoing maintenance and updates. Please try again later!")
        return True
    return False

# Progress bar for deployment
def create_progress_bar(progress, total=10):
    filled = int(progress * total / 100)
    empty = total - filled
    return f"[{'█' * filled}{'░' * empty}] {progress}%"

# Start command with welcome message and gif
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await maintenance_check(update, context): return
    user_id = str(update.message.from_user.id)
    if is_banned_user(user_id):
        await update.message.reply_text("You are banned from using this bot.")
        return

    welcome_message = (
        f"🤖 *Welcome to Heis_Tech Bot Hostinger XMD💫!* \n\n"
        f"✨ *What I can do:*\n"
        f"• Host and deploy your Telegram bots\n"
        f"• Manage multiple bot projects\n"
        f"• Monitor bot status and logs\n"
        f"• Auto-install dependencies\n\n"
        f"📋 *How to use me:*\n"
        f"1. Use /newproject to create a new bot project\n"
        f"2. Send your bot token, requirements.txt and app.py files\n"
        f"3. I'll deploy your bot automatically\n"
        f"4. Use /myprojects to manage your bots\n\n"
        f"⚡ *Quick commands:*\n"
        f"/menu - Main menu\n"
        f"/mainmenu - Complete command list\n"
        f"/mystatus - Check your account status\n"
        f"/newproject - Create new bot project\n"
        f"/myprojects - Your bot projects\n"
        f"/viewlogs - View deployment logs\n"
        f"/buypremium - Buy premium subscription\n"
        f"/stats - Check bot status\n"
        f"/ping - Check bot latency\n"
    )

    await send_animated_message(update, context, welcome_message)

    # Initialize user projects if not exists
    if user_id not in user_projects:
        user_projects[user_id] = {}
        save_data()

# Main menu command with tree structure and gif
async def mainmenu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await maintenance_check(update, context): return
    user_id = str(update.effective_user.id)
    if is_banned_user(user_id):
        await update.effective_message.reply_text("You are banned from using this bot.")
        return

    menu_text = (
        "╭──《 📋 Bot Commands 》──⊰\n\n"
        "🔹 *General Commands* 🔹\n"
        "├── /start - Start the bot\n"
        "├── /menu - Quick access menu\n"
        "├── /mainmenu - This command list\n"
        "├── /mystatus - Check your account status\n"
        "├── /about - About this service\n\n"
        "🔹 *Project Management* 🔹\n"
        "├── /newproject - Create new bot project\n"
        "├── /myprojects - List your projects\n"
        "├── /viewlogs - View deployment logs\n"
        "└── /restartproject - Restart a project\n\n"
        "🔹 *Bot Status* 🔹\n"
        "├── /stats - Check bot statistics\n"
        "├── /ping - Check bot latency\n"
        "└── /uptime - Check bot uptime\n\n"
        "🔹 *Premium Features* 🔹\n"
        "├── /buypremium - Buy premium subscription\n"
        "└── /mystatus - Check premium status\n\n"
        "🔹 *Admin Commands* 🔹\n"
        "├── /listpremiumusers - Manage premium users\n"
        "├── /broadcast - Broadcast message to all users\n"
        "├── /FreePremiumAccess - Activate free premium access\n"
        "├── /onlypremium - End free premium access\n"
        "└── /maintenancemode <on|off> - Toggle maintenance mode\n\n"
        "╰──⊰ *Use /menu for interactive buttons* ──⊰"
    )

    await send_animated_message(update, context, menu_text)

# Menu command with interactive buttons
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await maintenance_check(update, context): return
    user_id = str(update.effective_user.id)
    if is_banned_user(user_id):
        await update.effective_message.reply_text("You are banned from using this bot.")
        return

    if FREE_PREMIUM_MODE:
        premium_status = "🎉 FREE PREMIUM ACCESS ACTIVE!"
    elif is_premium_user(user_id):
        user_data = premium_users.get(user_id, {})
        expiry_date = datetime.fromisoformat(user_data.get('expiry_date', datetime.now().isoformat()))
        days_left = (expiry_date - datetime.now()).days
        premium_status = f"✅ Premium User ({days_left} days remaining)"
    else:
        project_count = len(user_projects.get(user_id, {}))
        premium_status = "❌ Free Tier (1 project limit)"

    keyboard = [
        [InlineKeyboardButton("🆕 New Project", callback_data="new_project")],
        [InlineKeyboardButton("📂 My Projects", callback_data="my_projects")],
        [InlineKeyboardButton("📊 View Logs", callback_data="view_logs")],
        [InlineKeyboardButton("📈 Bot Stats", callback_data="bot_stats")],
        [InlineKeyboardButton("⭐ Buy Premium", callback_data="buy_premium")],
        [InlineKeyboardButton("👤 My Status", callback_data="my_status")],
        [InlineKeyboardButton("📋 Command List", callback_data="command_list")],
    ]

    # Add admin menu for bot owner and admins
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text(
        f"📋 *Main Menu*\n\n{premium_status}\n\nChoose an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# My status command
async def mystatus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await maintenance_check(update, context): return
    user_id = str(update.effective_user.id)
    if is_banned_user(user_id):
        await update.effective_message.reply_text("You are banned from using this bot.")
        return

    if FREE_PREMIUM_MODE:
        status_message = (
            f"🎉 *Free Premium Access is Currently Active!* 🎉\n\n"
            f"You can deploy and manage unlimited projects for a limited time.\n\n"
            f"Projects: {len(user_projects.get(user_id, {}))} deployed\n"
            f"Enjoy unlimited deployment! 🚀"
        )
    elif is_premium_user(user_id):
        user_data = premium_users.get(user_id, {})
        expiry_date = datetime.fromisoformat(user_data.get('expiry_date', datetime.now().isoformat()))
        days_left = (expiry_date - datetime.now()).days
        plan = user_data.get('plan', 'unknown')

        status_message = (
            f"✅ *Premium Account Status*\n\n"
            f"• Plan: {plan}\n"
            f"• Expiry Date: {expiry_date.strftime('%d/%m/%Y')}\n"
            f"• Days Remaining: {days_left}\n"
            f"• Projects: {len(user_projects.get(user_id, {}))} deployed\n\n"
            f"✨ You have unlimited project deployment! 🚀"
        )
    else:
        project_count = len(user_projects.get(user_id, {}))
        status_message = (
            f"🔒 *Free Account Status*\n\n"
            f"• Plan: Free Tier\n"
            f"• Projects: {project_count}/1 deployed\n"
            f"• Limitations: 1 project maximum\n\n"
            f"⭐ Upgrade to premium for unlimited projects!\n"
            f"Use /buypremium to upgrade now!"
        )

    # Use effective_message for compatibility with buttons
    if update.callback_query:
        await update.callback_query.edit_message_text(status_message, parse_mode='Markdown')
    else:
        await update.effective_message.reply_text(status_message, parse_mode='Markdown')

# Buy premium command
async def buypremium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await maintenance_check(update, context): return
    user_id = str(update.effective_user.id)
    if is_banned_user(user_id):
        await update.effective_message.reply_text("You are banned from using this bot.")
        return

    if is_premium_user(user_id) and not FREE_PREMIUM_MODE:
        user_data = premium_users[user_id]
        expiry_date = datetime.fromisoformat(user_data['expiry_date'])
        days_left = (expiry_date - datetime.now()).days

        await update.effective_message.reply_text(
            f"🎉 *You already have premium access!*\n\n"
            f"Your premium expires in {days_left} days.\n"
            f"You can deploy unlimited projects with no restrictions. 🚀",
            parse_mode='Markdown'
        )
        return
    elif FREE_PREMIUM_MODE:
        await update.effective_message.reply_text(
            f"🎉 *Free Premium Access is Currently Active!* 🎉\n\n"
            f"You don't need to buy premium now. Enjoy unlimited projects!\n"
            f"I'll let you know when the free period ends."
        )
        return

    instructions = (
        f"⭐ *How to Buy Premium Subscription:*\n\n"
        f"💎 *Premium Plans:*\n"
        f"• Ksh10.00 - 1 week access\n"
        f"• Ksh50.00 - 2 weeks access\n"
        f"• Ksh100.00 - Unlimited access\n\n"
        f"📱 *Payment Instructions:*\n"
        f"1. Send your chosen amount to *{MPESA_NUMBER}* ({MPESA_RECIPIENT})\n"
        f"2. Forward the M-PESA confirmation message to this bot\n"
        f"3. Your account will be upgraded to premium instantly!\n\n"
        f"💎 *Premium Benefits:*\n"
        f"• Unlimited bot projects\n"
        f"• Priority support\n"
        f"• Faster deployment\n"
        f"• No project limitations\n\n"
        f"❓ *Need help? Contact support: {DEVELOPER_INFO['support']}*"
    )

    # Use effective_message for compatibility with buttons
    if update.callback_query:
        await update.callback_query.edit_message_text(instructions, parse_mode='Markdown')
    else:
        await update.effective_message.reply_text(instructions, parse_mode='Markdown')

# Verify M-PESA payment
async def verify_mpesa_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await maintenance_check(update, context): return
    user_id = str(update.message.from_user.id)
    if is_banned_user(user_id):
        await update.message.reply_text("You are banned from using this bot.")
        return

    message_text = update.message.text

    if is_premium_user(user_id):
        await update.message.reply_text("✅ You already have premium access!")
        return

    # M-PESA message pattern
    pattern = r"([A-Z0-9]+) Confirmed\. Ksh([0-9.]+) sent to ([A-Za-z\s]+) ([0-9]+) on ([0-9/]+) at ([0-9:APM\s]+)"

    match = re.search(pattern, message_text)
    if match:
        transaction_id = match.group(1)
        amount = float(match.group(2))
        recipient = match.group(3)
        number = match.group(4)
        date = match.group(5)
        time_str = match.group(6)

        # Verify payment details
        if (amount in [10, 50, 100] and
            number == MPESA_NUMBER and
            recipient.lower() in MPESA_RECIPIENT.lower()):

            # Calculate expiry date based on amount
            expiry_date = calculate_expiry_date(amount)
            start_date = datetime.now()

            # Grant premium access
            premium_users[user_id] = {
                "transaction_id": transaction_id,
                "purchase_date": start_date.isoformat(),
                "expiry_date": expiry_date.isoformat(),
                "amount": amount,
                "plan": MPESA_AMOUNTS[amount]
            }
            save_data()

            success_message = (
                f"🎉 *Premium Subscription Activated!* 🎉\n\n"
                f"✅ User ID: {user_id}\n"
                f"✅ Transaction ID: {transaction_id}\n"
                f"✅ Amount: Ksh{amount:.2f}\n"
                f"✅ Plan: {MPESA_AMOUNTS[amount]}\n"
                f"✅ Start Time: {start_date.strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"✅ End Time: {expiry_date.strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"✅ Expiry Date: {expiry_date.strftime('%d/%m/%Y')}\n\n"
                f"✨ *You now have premium access!*\n"
                f"• Deploy unlimited bot projects\n"
                f"• No restrictions\n"
                f"• Priority support\n"
                f"Thank you for your purchase! 🚀"
            )

            await update.message.reply_text(success_message, parse_mode='Markdown')

            # Notify bot owner
            await context.bot.send_message(
                chat_id=BOT_OWNER_ID,
                text=f"💎 New Premium User\n"
                     f"User: {update.message.from_user.first_name}\n"
                     f"ID: {user_id}\n"
                     f"Transaction: {transaction_id}\n"
                     f"Amount: Ksh{amount:.2f}\n"
                     f"Plan: {MPESA_AMOUNTS[amount]}\n"
                     f"Start: {start_date.strftime('%d/%m/%Y %H:%M:%S')}\n"
                     f"End: {expiry_date.strftime('%d/%m/%Y %H:%M:%S')}"
            )
        else:
            error_message = (
                f"❌ *Payment verification failed!*\n\n"
                f"Please make sure you sent the correct amount to the correct number.\n"
                f"Accepted amounts: Ksh10, Ksh50, or Ksh100 to {MPESA_NUMBER} ({MPESA_RECIPIENT})\n\n"
                f"ℹ️ Please recheck payment info or contact Support 📞 {DEVELOPER_INFO['support']}"
            )
            await update.message.reply_text(error_message, parse_mode='Markdown')
    else:
        error_message = (
            f"❌ *Invalid M-PESA message format!*\n\n"
            f"Please forward the exact confirmation message you received from M-PESA.\n\n"
            f"ℹ️ If the problem persists, contact Support 📞 {DEVELOPER_INFO['support']}"
        )
        await update.message.reply_text(error_message, parse_mode='Markdown')

# List premium users (admin only)
async def listpremiumusers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)

    if not is_admin(user_id):
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ This command is only available to admins.")
        else:
            await update.effective_message.reply_text("❌ This command is only available to admins.")
        return

    if not premium_users:
        if update.callback_query:
            await update.callback_query.edit_message_text("No premium users found.")
        else:
            await update.effective_message.reply_text("No premium users found.")
        return

    premium_list = "👑 *Premium Users List*\n\n"
    keyboard = []

    for user_id, user_data in premium_users.items():
        # Handle missing expiry_date key
        if 'expiry_date' not in user_data:
            premium_list += f"• User ID: {user_id} - ❌ INVALID (missing expiry date)\n\n"
            keyboard.append([InlineKeyboardButton(f"❌ Remove {user_id}", callback_data=f"remove_premium_{user_id}")])
            continue

        try:
            expiry_date = datetime.fromisoformat(user_data['expiry_date'])
            days_left = (expiry_date - datetime.now()).days
            plan = user_data.get('plan', 'unknown')

            premium_list += f"• User ID: {user_id}\n"
            premium_list += f"  Plan: {plan}\n"
            premium_list += f"  Expires: {expiry_date.strftime('%d/%m/%Y')} ({days_left} days left)\n"
            premium_list += f"  Amount: Ksh{user_data.get('amount', 0):.2f}\n\n"

            # Add remove button for each user
            keyboard.append([InlineKeyboardButton(f"❌ Remove {user_id}", callback_data=f"remove_premium_{user_id}")])
        except (ValueError, KeyError):
            premium_list += f"• User ID: {user_id} - ❌ INVALID (corrupted data)\n\n"
            keyboard.append([InlineKeyboardButton(f"❌ Remove {user_id}", callback_data=f"remove_premium_{user_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(premium_list, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.effective_message.reply_text(premium_list, reply_markup=reply_markup, parse_mode='Markdown')

# Remove premium user (admin only)
async def removepremium(update: Update, context: ContextTypes.DEFAULT_TYPE, user_to_remove: str) -> None:
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ This command is only available to admins.")
        else:
            await update.effective_message.reply_text("❌ This command is only available to admins.")
        return
        
    query = update.callback_query
    if query:
        await query.answer()

    if user_to_remove in premium_users:
        del premium_users[user_to_remove]
        save_data()
        await update.effective_message.reply_text(f"✅ Premium access for user `{user_to_remove}` has been removed.", parse_mode='Markdown')
        try:
            await context.bot.send_message(chat_id=int(user_to_remove), text="Your premium subscription has been removed by an admin.")
        except Exception as e:
            logger.error(f"Failed to notify user {user_to_remove}: {e}")
    else:
        await update.effective_message.reply_text(f"❌ User `{user_to_remove}` does not have premium access or was not found.", parse_mode='Markdown')
        
# New project command - starts conversation
async def newproject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await maintenance_check(update, context): return ConversationHandler.END
    user_id = str(update.effective_user.id)
    if is_banned_user(user_id):
        await update.effective_message.reply_text("You are banned from using this bot.")
        return ConversationHandler.END

    # Check project limit
    if not check_project_limit(user_id):
        await update.effective_message.reply_text(
            "❌ *Project Limit Reached!*\n\n"
            "You have reached the maximum number of projects (1) on the free tier.\n\n"
            "⭐ *Upgrade to Premium for:*\n"
            "• Unlimited projects\n"
            "• No restrictions\n"
            "• Priority support\n\n"
            "Use /buypremium to upgrade now! 🚀",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    user_sessions[user_id] = {'state': 'project_name'}

    await update.effective_message.reply_text(
        "🆕 *New Project*\n\nPlease enter a name for your new bot project:",
        parse_mode='Markdown'
    )
    return PROJECT_NAME

# Handle project name input
async def project_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await maintenance_check(update, context): return ConversationHandler.END
    user_id = str(update.message.from_user.id)
    if is_banned_user(user_id):
        await update.message.reply_text("You are banned from using this bot.")
        return ConversationHandler.END

    project_name = update.message.text.strip()

    # Validate project name
    if not re.match(r'^[a-zA-Z0-9_]+$', project_name):
        await update.message.reply_text(
            "❌ Invalid project name. Use only letters, numbers and underscores."
        )
        return PROJECT_NAME

    if user_id not in user_projects:
        user_projects[user_id] = {}

    if project_name in user_projects[user_id]:
        await update.message.reply_text(
            "❌ Project name already exists. Please choose a different name."
        )
        return PROJECT_NAME

    # Initialize project
    project_dir = os.path.join("projects", user_id, project_name)
    user_projects[user_id][project_name] = {
        'created': datetime.now().isoformat(),
        'status': 'not_started',
        'directory': project_dir,
        'files': [], # New list to store all file paths
    }
    user_sessions[user_id] = {
        'state': 'bot_token',
        'current_project': project_name
    }
    save_data()

    # Create project directory
    os.makedirs(project_dir, exist_ok=True)

    await update.message.reply_text(
        f"✅ Project '{project_name}' created!\n\n"
        f"🔑 *Bot Token Required*\n\n"
        f"Please send your bot token from @BotFather:\n\n"
        f"1. Message @BotFather\n"
        f"2. Use /mybots\n"
        f"3. Select your bot\n"
        f"4. Copy the API Token\n"
        f"5. Send it here",
        parse_mode='Markdown'
    )
    return BOT_TOKEN

# Handle bot token input
async def bot_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await maintenance_check(update, context): return ConversationHandler.END
    user_id = str(update.message.from_user.id)
    if is_banned_user(user_id):
        await update.message.reply_text("You are banned from using this bot.")
        return ConversationHandler.END

    if user_id not in user_sessions or 'current_project' not in user_sessions[user_id]:
        await update.message.reply_text("❌ Session expired. Please start over with /newproject")
        return ConversationHandler.END

    bot_token = update.message.text.strip()

    # Validate token format
    if not bot_token or ':' not in bot_token or len(bot_token) < 30:
        await update.message.reply_text(
            "❌ Invalid bot token format. Please send a valid token from @BotFather."
        )
        return BOT_TOKEN

    project_name = user_sessions[user_id]['current_project']
    user_projects[user_id][project_name]['bot_token'] = bot_token
    user_sessions[user_id]['state'] = 'requirements'
    save_data()

    await update.message.reply_text(
        "✅ Bot token saved!\n\nNow please send your requirements.txt file:",
        parse_mode='Markdown'
    )
    return REQUIREMENTS

# Handle requirements.txt file
async def requirements_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await maintenance_check(update, context): return ConversationHandler.END
    user_id = str(update.message.from_user.id)
    if is_banned_user(user_id):
        await update.message.reply_text("You are banned from using this bot.")
        return ConversationHandler.END

    if user_id not in user_sessions or 'current_project' not in user_sessions[user_id]:
        await update.message.reply_text("❌ Session expired. Please start over with /newproject")
        return ConversationHandler.END

    project_name = user_sessions[user_id]['current_project']
    project_dir = user_projects[user_id][project_name]['directory']
    
    # Create project directory if it doesn't exist
    os.makedirs(project_dir, exist_ok=True)
    
    file_path = os.path.join(project_dir, 'requirements.txt')

    # Check if it's a document or text
    if update.message.document:
        file = update.message.document
        if not file.file_name.lower().endswith('.txt'):
            await update.message.reply_text("❌ Please send a requirements.txt file")
            return REQUIREMENTS
        
        # Download file
        file_obj = await file.get_file()
        await file_obj.download_to_drive(custom_path=file_path)
    elif update.message.text:
        # Save text as requirements.txt
        with open(file_path, 'w') as f:
            f.write(update.message.text)
    else:
        # Create a default requirements.txt if nothing is sent
        with open(file_path, 'w') as f:
            f.write("python-telegram-bot\n")
        await update.message.reply_text("ℹ️ No requirements.txt provided. Created a default one with python-telegram-bot.")

    user_sessions[user_id]['state'] = 'app_py'
    user_projects[user_id][project_name]['requirements'] = True
    user_projects[user_id][project_name]['files'].append("requirements.txt")
    save_data()

    await update.message.reply_text(
        "✅ requirements.txt received!\n\nNow please send your app.py file:",
        parse_mode='Markdown'
    )
    return APP_PY

# Handle app.py file and ask for additional files
async def app_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await maintenance_check(update, context): return ConversationHandler.END
    user_id = str(update.message.from_user.id)
    if is_banned_user(user_id):
        await update.message.reply_text("You are banned from using this bot.")
        return ConversationHandler.END

    if user_id not in user_sessions or 'current_project' not in user_sessions[user_id]:
        await update.message.reply_text("❌ Session expired. Please start over with /newproject")
        return ConversationHandler.END

    project_name = user_sessions[user_id]['current_project']
    project_dir = user_projects[user_id][project_name]['directory']
    file_path = os.path.join(project_dir, 'app.py')

    # Check if it's a document or text
    if update.message.document:
        file = update.message.document
        if not file.file_name.lower().endswith('.py'):
            await update.message.reply_text("❌ Please send an app.py file")
            return APP_PY

        # Download file
        file_obj = await file.get_file()
        await file_obj.download_to_drive(custom_path=file_path)
    elif update.message.text:
        # Save text as app.py
        with open(file_path, 'w') as f:
            f.write(update.message.text)
    else:
        await update.message.reply_text("❌ Please send an app.py file or its content as text.")
        return APP_PY

    user_projects[user_id][project_name]['app'] = True
    user_projects[user_id][project_name]['files'].append("app.py")
    save_data()

    keyboard = [
        [InlineKeyboardButton("✅ Yes, add more files", callback_data="add_more_files")],
        [InlineKeyboardButton("🚀 No, deploy now!", callback_data="deploy_now")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ app.py received!\n\n"
        "Do you want to add additional files (config files, data files, etc.)?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return ADDITIONAL_FILES

# Handle additional files or deploy
async def additional_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await maintenance_check(update, context): return ConversationHandler.END
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    if is_banned_user(user_id):
        await query.edit_message_text("You are banned from using this bot.")
        return ConversationHandler.END
    if user_id not in user_sessions or 'current_project' not in user_sessions[user_id]:
        await query.edit_message_text("❌ Session expired. Please start over with /newproject")
        return ConversationHandler.END
    
    project_name = user_sessions[user_id]['current_project']

    if query.data == 'deploy_now':
        await query.edit_message_text("🚀 Starting deployment...")
        # Start deployment process
        await deploy_project(user_id, project_name, context)
        return ConversationHandler.END
    else:
        await query.edit_message_text(
            "📁 Please send your additional files one by one.\n\n"
            "When you're done, use /done to start deployment."
        )
        return ADDITIONAL_FILES

# Handle additional files upload
async def handle_additional_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await maintenance_check(update, context): return ConversationHandler.END
    user_id = str(update.message.from_user.id)
    if is_banned_user(user_id):
        await update.message.reply_text("You are banned from using this bot.")
        return ConversationHandler.END

    if user_id not in user_sessions or 'current_project' not in user_sessions[user_id]:
        await update.message.reply_text("❌ Session expired. Please start over with /newproject")
        return ConversationHandler.END

    project_name = user_sessions[user_id]['current_project']
    project_dir = user_projects[user_id][project_name]['directory']

    if update.message.document:
        file = update.message.document
        file_name = file.file_name
        # Download file
        file_obj = await file.get_file()
        file_path = os.path.join(project_dir, file_name)
        await file_obj.download_to_drive(custom_path=file_path)

        # Add to project files list
        if file_name not in user_projects[user_id][project_name]['files']:
            user_projects[user_id][project_name]['files'].append(file_name)
            save_data()
        
        await update.message.reply_text(f"✅ {file_name} received! Send more files or use /done to deploy.")
        return ADDITIONAL_FILES
    elif update.message.text:
        # Handle text as a file
        file_name = "additional_file.txt"
        file_path = os.path.join(project_dir, file_name)
        with open(file_path, 'w') as f:
            f.write(update.message.text)
        
        if file_name not in user_projects[user_id][project_name]['files']:
            user_projects[user_id][project_name]['files'].append(file_name)
            save_data()
        
        await update.message.reply_text(f"✅ Text saved as {file_name}! Send more files or use /done to deploy.")
        return ADDITIONAL_FILES
    else:
        await update.message.reply_text("Please send a file or use /done to deploy.")
        return ADDITIONAL_FILES

# Done command to finish file upload and deploy
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await maintenance_check(update, context): return ConversationHandler.END
    user_id = str(update.message.from_user.id)
    if is_banned_user(user_id):
        await update.message.reply_text("You are banned from using this bot.")
        return ConversationHandler.END

    if user_id not in user_sessions or 'current_project' not in user_sessions[user_id]:
        await update.message.reply_text("❌ Session expired. Please start over with /newproject")
        return ConversationHandler.END

    project_name = user_sessions[user_id]['current_project']
    await update.message.reply_text("🚀 Starting deployment...")
    await deploy_project(user_id, project_name, context)
    return ConversationHandler.END

# Deploy project function
async def deploy_project(user_id, project_name, context):
    try:
        project_data = user_projects[user_id][project_name]
        project_dir = project_data['directory']
        bot_token = project_data['bot_token']
        user_projects[user_id][project_name]['status'] = 'deploying'
        save_data()

        logger.info(f"Starting deployment for user {user_id}, project {project_name}")

        # Send initial deployment message with progress bar
        initial_message = await context.bot.send_message(
            chat_id=user_id,
            text=f"🏗️ *Deploying Project: {project_name}*\n\n"
                 f"1/4 ⚙️ Installing dependencies...",
            parse_mode='Markdown'
        )
        deployment_messages[user_id] = initial_message.message_id
        
        # Deployment logs
        deployment_logs[user_id] = (
            f"Deployment Log for Project: {project_name}\n"
            f"----------------------------------------\n"
        )
        
        def update_log(message):
            deployment_logs[user_id] += f"-> {message}\n"
            
        def update_message_text(text, progress=None):
            if progress is not None:
                progress_bar = create_progress_bar(progress)
                full_text = f"🏗️ *Deploying Project: {project_name}*\n\n{text}\n\n`{progress_bar}`"
            else:
                full_text = f"🏗️ *Deploying Project: {project_name}*\n\n{text}"
            
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(
                    context.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=deployment_messages[user_id],
                        text=full_text,
                        parse_mode='Markdown'
                    )
                )
            except Exception as e:
                logger.error(f"Failed to edit message: {e}")

        # Step 1: Install dependencies
        update_log("Installing dependencies...")
        update_message_text("1/4 ⚙️ Installing dependencies...", progress=25)
        
        requirements_path = os.path.join(project_dir, 'requirements.txt')
        if os.path.exists(requirements_path):
            try:
                # Use the correct pip command based on environment
                pip_cmd = ENV_INFO['pip_command'] or 'pip'
                command = f"{pip_cmd} install --no-cache-dir -r {requirements_path}"
                
                result = subprocess.run(
                    command.split(),
                    cwd=project_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )
                update_log(f"Dependencies installed successfully.\n\n{result.stdout}\n")
            except subprocess.CalledProcessError as e:
                update_log(f"❌ Error installing dependencies:\n{e.stderr}\n")
                # Continue deployment even if dependencies fail
                update_log("⚠️ Continuing deployment despite dependency installation errors")
        else:
            # Create a default requirements.txt if it doesn't exist
            with open(requirements_path, 'w') as f:
                f.write("python-telegram-bot\n")
            update_log("ℹ️ Created default requirements.txt with python-telegram-bot\n")

        # Step 2: Create .env file for bot token
        update_message_text("2/4 📄 Creating .env file...", progress=50)
        update_log("Creating .env file...")
        with open(os.path.join(project_dir, ".env"), "w") as f:
            f.write(f"TELEGRAM_BOT_TOKEN={bot_token}\n")
            f.write("PYTHONUNBUFFERED=1\n")
        update_log(".env file created successfully.\n")

        # Step 3: Run the project
        update_message_text("3/4 🚀 Starting bot...", progress=75)
        update_log("Starting bot...")
        
        # Kill any existing process for this project
        await kill_project_process(project_data)

        command = f"{ENV_INFO['python_command']} app.py"
        
        # Check if app.py exists before starting the process
        if not os.path.exists(os.path.join(project_dir, 'app.py')):
            raise FileNotFoundError("app.py not found in the project directory.")

        with open(os.path.join(project_dir, "bot.log"), "w") as log_file:
            process = subprocess.Popen(
                command.split(),
                cwd=project_dir,
                env={**os.environ, 'TELEGRAM_BOT_TOKEN': bot_token, 'PYTHONUNBUFFERED': '1'},
                stdout=log_file,
                stderr=log_file,
                preexec_fn=os.setsid
            )
        
        with open(os.path.join(project_dir, "bot.pid"), "w") as pid_file:
            pid_file.write(str(process.pid))
        
        user_projects[user_id][project_name]['status'] = 'running'
        user_projects[user_id][project_name]['pid'] = process.pid
        save_data()
        
        update_log(f"Bot started successfully with PID: {process.pid}\n")
        
        # Step 4: Finalizing
        update_message_text("4/4 ✅ Deployment successful!", progress=100)
        update_log("Deployment successful!\n")

        final_message = (
            f"🎉 *Deployment Complete!* 🎉\n\n"
            f"✅ Project Name: `{project_name}`\n"
            f"• Status: 🟢 Running\n"
            f"• PID: `{process.pid}`\n\n"
            f"Your bot is now live! Use /myprojects to manage your bots.\n\n"
            f"*Deployment logs:*\n"
            f"```ansi\n"
            f"{deployment_logs[user_id].strip()}\n"
            f"```"
        )
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=deployment_messages[user_id],
            text=final_message,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Deployment failed for user {user_id}, project {project_name}: {e}")
        user_projects[user_id][project_name]['status'] = 'failed'
        save_data()
        
        final_message = (
            f"❌ *Deployment Failed for {project_name}!* ❌\n\n"
            f"An error occurred during deployment: `{e}`\n\n"
            f"Please check your code and try again.\n\n"
            f"*Deployment logs:*\n"
            f"```ansi\n"
            f"{deployment_logs[user_id].strip()[-3500:]}\n"
            f"```"
        )
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=deployment_messages[user_id],
            text=final_message,
            parse_mode='Markdown'
        )

# My projects command
async def myprojects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await maintenance_check(update, context): return
    user_id = str(update.effective_user.id)
    if is_banned_user(user_id):
        await update.effective_message.reply_text("You are banned from using this bot.")
        return

    projects = user_projects.get(user_id, {})
    if not projects:
        await update.effective_message.reply_text("You have no projects yet. Use /newproject to create one.")
        return

    project_list = "📂 *Your Projects*\n\n"
    keyboard = []
    for project_name, project_data in projects.items():
        status, pid = get_project_status(project_data['directory'])
        project_list += f"• `{project_name}`\n  Status: {status}\n  Created: {datetime.fromisoformat(project_data['created']).strftime('%d/%m/%Y')}\n\n"
        keyboard.append([InlineKeyboardButton(f"⚙️ Manage: {project_name}", callback_data=f"manage_{project_name}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text(
        project_list,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Admin panel
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.effective_message.reply_text("❌ This command is only available to admins.")
        return

    keyboard = [
        [InlineKeyboardButton("📂 Manage All Projects", callback_data="admin_manage_projects")],
        [InlineKeyboardButton("⭐ Manage Premium Users", callback_data="listpremiumusers")],
        [InlineKeyboardButton("📣 Broadcast Message", callback_data="start_broadcast")],
        [InlineKeyboardButton("👑 Add Admin", callback_data="add_admin")],
        [InlineKeyboardButton("❌ Remove Admin", callback_data="remove_admin")],
        [InlineKeyboardButton("🔨 Toggle Maintenance", callback_data="toggle_maintenance")],
        [InlineKeyboardButton("🎉 Toggle Free Premium", callback_data="toggle_free_premium")],
        [InlineKeyboardButton("📈 View Global Stats", callback_data="bot_stats")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text("👑 *Admin Panel*", reply_markup=reply_markup, parse_mode='Markdown')

# Admin management of projects
async def admin_manage_projects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.effective_message.reply_text("❌ This command is only available to admins.")
        return

    query = update.callback_query
    await query.answer()

    all_projects = []
    for uid, projects in user_projects.items():
        for project_name in projects.keys():
            all_projects.append({'user_id': uid, 'project_name': project_name})

    if not all_projects:
        await query.edit_message_text("No projects have been created yet.")
        return

    message = "📂 *All User Projects*\n\n"
    keyboard = []
    for project_data in all_projects:
        uid = project_data['user_id']
        p_name = project_data['project_name']
        project = user_projects[uid][p_name]
        status, _ = get_project_status(project['directory'])
        
        message += f"• `{p_name}`\n  User ID: `{uid}`\n  Status: {status}\n\n"
        
        # Add a management button for each project
        keyboard.append([InlineKeyboardButton(f"⚙️ Manage {p_name} ({uid})", callback_data=f"admin_manage_project_{uid}_{p_name}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

# Admin manage a single project
async def admin_manage_single_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.effective_message.reply_text("❌ This command is only available to admins.")
        return

    query = update.callback_query
    await query.answer()

    try:
        data = query.data.split('_')
        uid_to_manage = data[3]
        project_name = data[4]
        
        if uid_to_manage not in user_projects or project_name not in user_projects[uid_to_manage]:
            await query.edit_message_text("❌ Project not found.")
            return

        project_data = user_projects[uid_to_manage][project_name]
        status, pid = get_project_status(project_data['directory'])
        
        message = (
            f"⚙️ *Managing Project: {project_name}*\n\n"
            f"• User ID: `{uid_to_manage}`\n"
            f"• Status: {status}\n"
            f"• PID: `{pid if pid else 'N/A'}`\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🟢 Start", callback_data=f"admin_start_{uid_to_manage}_{project_name}"),
             InlineKeyboardButton("🔴 Stop", callback_data=f"admin_stop_{uid_to_manage}_{project_name}")],
            [InlineKeyboardButton("🔁 Restart", callback_data=f"admin_restart_{uid_to_manage}_{project_name}")],
            [InlineKeyboardButton("🗑️ Delete", callback_data=f"admin_delete_{uid_to_manage}_{project_name}")],
            [InlineKeyboardButton("📄 View Logs", callback_data=f"admin_view_logs_{uid_to_manage}_{project_name}")],
            [InlineKeyboardButton("📁 View Files", callback_data=f"admin_view_files_{uid_to_manage}_{project_name}")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_manage_projects")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except (IndexError, KeyError) as e:
        logger.error(f"Error managing single project: {e}")
        await query.edit_message_text("❌ Invalid project or user ID. Please go back and try again.")

# Admin view project files
async def admin_view_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.effective_message.reply_text("❌ This command is only available to admins.")
        return

    query = update.callback_query
    await query.answer()

    try:
        data = query.data.split('_')
        uid_to_manage = data[3]
        project_name = data[4]
        
        project_data = user_projects[uid_to_manage][project_name]
        project_dir = project_data['directory']
        
        if not os.path.isdir(project_dir):
            await query.edit_message_text("Project directory not found.")
            return

        files = [f for f in os.listdir(project_dir) if os.path.isfile(os.path.join(project_dir, f))]
        
        if not files:
            await query.edit_message_text(
                f"📁 *Files in {project_name}*\n\n"
                f"No files found in this project.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=f"admin_manage_project_{uid_to_manage}_{project_name}")]])
            )
            return

        message = f"📁 *Files in {project_name}*\n\n"
        keyboard = []
        for file_name in files:
            message += f"• `{file_name}`\n"
            keyboard.append([InlineKeyboardButton(f"⬇️ Download {file_name}", callback_data=f"admin_download_file_{uid_to_manage}_{project_name}_{file_name}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"admin_manage_project_{uid_to_manage}_{project_name}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    except (IndexError, KeyError) as e:
        logger.error(f"Error viewing project files: {e}")
        await query.edit_message_text("❌ Invalid project or user ID. Please go back and try again.")

# Admin download a specific file
async def admin_download_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.effective_message.reply_text("❌ This command is only available to admins.")
        return

    query = update.callback_query
    await query.answer("Preparing file for download...")

    try:
        data = query.data.split('_')
        uid_to_manage = data[3]
        project_name = data[4]
        file_name = "_".join(data[5:])
        
        project_dir = user_projects[uid_to_manage][project_name]['directory']
        file_path = os.path.join(project_dir, file_name)
        
        if not os.path.isfile(file_path):
            await query.edit_message_text(
                f"❌ File `{file_name}` not found in project `{project_name}`.",
                parse_mode='Markdown'
            )
            return
        
        await context.bot.send_document(
            chat_id=user_id,
            document=InputFile(file_path, filename=file_name),
            caption=f"⬇️ Downloaded from project `{project_name}`",
            parse_mode='Markdown'
        )
        
    except (IndexError, KeyError) as e:
        logger.error(f"Error downloading file: {e}")
        await query.edit_message_text("❌ Invalid file, project, or user ID.")
        
# Button handler for general callbacks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    if is_banned_user(user_id):
        await query.edit_message_text("You are banned from using this bot.")
        return

    data = query.data
    
    # Handle admin-specific callbacks
    if data.startswith("admin_"):
        if not is_admin(user_id):
            await query.edit_message_text("❌ This action is only available to admins.")
            return

        parts = data.split('_')
        action = parts[1]
        
        if action == 'manage' and len(parts) == 3:
            await admin_manage_projects(update, context)
        elif action == 'manage' and len(parts) == 5:
            await admin_manage_single_project(update, context)
        elif action == 'view':
            if parts[2] == 'logs':
                await admin_view_logs(update, context)
            elif parts[2] == 'files':
                await admin_view_files(update, context)
        elif action == 'download' and parts[2] == 'file':
            await admin_download_file(update, context)
        elif action in ['start', 'stop', 'restart', 'delete']:
            uid = parts[2]
            p_name = parts[3]
            if action == 'start':
                await start_project_cmd(update, context, uid, p_name)
            elif action == 'stop':
                await stop_project_cmd(update, context, uid, p_name)
            elif action == 'restart':
                await restart_project_cmd(update, context, uid, p_name)
            elif action == 'delete':
                await delete_project_cmd(update, context, uid, p_name)
        elif action == 'panel':
            await admin_panel(update, context)
        
        return

    # Handle user-specific callbacks
    if data == "new_project":
        await newproject(update, context)
    elif data == "my_projects":
        await myprojects(update, context)
    elif data == "view_logs":
        await viewlogs_menu(update, context)
    elif data == "bot_stats":
        await stats(update, context)
    elif data == "buy_premium":
        await buypremium(update, context)
    elif data == "my_status":
        await mystatus(update, context)
    elif data == "command_list":
        await mainmenu(update, context)
    elif data == "admin_panel":
        await admin_panel(update, context)
    elif data.startswith("manage_"):
        project_name = data.split('_')[1]
        await manage_project(update, context, project_name)
    elif data.startswith("start_"):
        project_name = data.split('_')[1]
        await start_project_cmd(update, context, user_id, project_name)
    elif data.startswith("stop_"):
        project_name = data.split('_')[1]
        await stop_project_cmd(update, context, user_id, project_name)
    elif data.startswith("restart_"):
        project_name = data.split('_')[1]
        await restart_project_cmd(update, context, user_id, project_name)
    elif data.startswith("delete_"):
        project_name = data.split('_')[1]
        await delete_project_cmd(update, context, user_id, project_name)
    elif data.startswith("view_log_"):
        project_name = data.split('_')[2]
        await viewlogs_for_project(update, context, project_name)
    elif data == "listpremiumusers":
        await listpremiumusers(update, context)
    elif data.startswith("remove_premium_"):
        user_to_remove = data.split('_')[2]
        await removepremium(update, context, user_to_remove)
    elif data == "start_broadcast":
        await update.callback_query.edit_message_text("📝 Please enter the message you want to broadcast to all users.")
        context.user_data['state'] = 'broadcast'
        return
    elif data == "toggle_maintenance":
        # Toggle maintenance mode
        global MAINTENANCE_MODE
        MAINTENANCE_MODE = not MAINTENANCE_MODE
        save_data()
        status = "ON" if MAINTENANCE_MODE else "OFF"
        await update.callback_query.edit_message_text(f"Maintenance mode is now {status}")
    elif data == "toggle_free_premium":
        # Toggle free premium mode
        global FREE_PREMIUM_MODE
        FREE_PREMIUM_MODE = not FREE_PREMIUM_MODE
        save_data()
        status = "ON" if FREE_PREMIUM_MODE else "OFF"
        await update.callback_query.edit_message_text(f"Free premium mode is now {status}")
    elif data == "add_admin":
        await update.callback_query.edit_message_text("Please reply with the user ID of the user you want to add as an admin.")
        context.user_data['state'] = 'add_admin'
    elif data == "remove_admin":
        await update.callback_query.edit_message_text("Please reply with the user ID of the admin you want to remove.")
        context.user_data['state'] = 'remove_admin'

# Manage a single project from myprojects
async def manage_project(update: Update, context: ContextTypes.DEFAULT_TYPE, project_name: str) -> None:
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    if is_banned_user(user_id):
        await query.edit_message_text("You are banned from using this bot.")
        return

    if project_name not in user_projects.get(user_id, {}):
        await query.edit_message_text("❌ Project not found.")
        return

    project_data = user_projects[user_id][project_name]
    status, pid = get_project_status(project_data['directory'])

    message = (
        f"⚙️ *Managing Project: {project_name}*\n\n"
        f"• Status: {status}\n"
        f"• PID: `{pid if pid else 'N/A'}`\n\n"
        f"• Created: {datetime.fromisoformat(project_data['created']).strftime('%d/%m/%Y')}\n"
    )

    keyboard = [
        [InlineKeyboardButton("🟢 Start", callback_data=f"start_{project_name}"),
         InlineKeyboardButton("🔴 Stop", callback_data=f"stop_{project_name}")],
        [InlineKeyboardButton("🔁 Restart", callback_data=f"restart_{project_name}")],
        [InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{project_name}")],
        [InlineKeyboardButton("📄 View Logs", callback_data=f"view_log_{project_name}")],
        [InlineKeyboardButton("⬅️ Back to Projects", callback_data="my_projects")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

# Start a project
async def start_project_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str, project_name: str) -> None:
    try:
        query = update.callback_query
        if query:
            await query.answer()
            
        user_id = str(user_id)
        if project_name not in user_projects.get(user_id, {}):
            await update.effective_message.reply_text("❌ Project not found.")
            return

        project_data = user_projects[user_id][project_name]
        project_dir = project_data['directory']
        status, _ = get_project_status(project_dir)

        if status == "🟢 Running":
            await update.effective_message.reply_text("Project is already running.")
            return

        if not os.path.exists(os.path.join(project_dir, 'app.py')):
            await update.effective_message.reply_text("❌ app.py not found in project directory. Deployment failed.")
            user_projects[user_id][project_name]['status'] = 'failed'
            save_data()
            return
            
        await update.effective_message.reply_text("🟢 Starting project...")
        
        # Kill any old process
        await kill_project_process(project_data)

        bot_token = project_data.get('bot_token')
        if not bot_token:
            await update.effective_message.reply_text("❌ Bot token not found. Please re-deploy the project.")
            return
        
        command = f"{ENV_INFO['python_command']} app.py"
        
        with open(os.path.join(project_dir, "bot.log"), "w") as log_file:
            process = subprocess.Popen(
                command.split(),
                cwd=project_dir,
                env={**os.environ, 'TELEGRAM_BOT_TOKEN': bot_token, 'PYTHONUNBUFFERED': '1'},
                stdout=log_file,
                stderr=log_file,
                preexec_fn=os.setsid
            )
        
        with open(os.path.join(project_dir, "bot.pid"), "w") as pid_file:
            pid_file.write(str(process.pid))
            
        user_projects[user_id][project_name]['status'] = 'running'
        user_projects[user_id][project_name]['pid'] = process.pid
        save_data()
        
        await update.effective_message.reply_text(
            f"✅ Project `{project_name}` started successfully with PID: `{process.pid}`",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to start project {project_name}: {e}")
        await update.effective_message.reply_text(f"❌ Failed to start project: {e}")

# Stop a project
async def stop_project_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str, project_name: str) -> None:
    try:
        query = update.callback_query
        if query:
            await query.answer()
        
        user_id = str(user_id)
        if project_name not in user_projects.get(user_id, {}):
            await update.effective_message.reply_text("❌ Project not found.")
            return

        project_data = user_projects[user_id][project_name]
        status, _ = get_project_status(project_data['directory'])
        
        if status == "🔴 Stopped":
            await update.effective_message.reply_text("Project is already stopped.")
            return
            
        await update.effective_message.reply_text("🔴 Stopping project...")

        await kill_project_process(project_data)

        user_projects[user_id][project_name]['status'] = 'stopped'
        save_data()
        await update.effective_message.reply_text(f"✅ Project `{project_name}` stopped successfully.", parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Failed to stop project {project_name}: {e}")
        await update.effective_message.reply_text(f"❌ Failed to stop project: {e}")

# Kill a running process
async def kill_project_process(project_data):
    project_dir = project_data['directory']
    pid_file = os.path.join(project_dir, "bot.pid")
    
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"Terminated process with PID: {pid}")
            os.remove(pid_file)
        except (ValueError, FileNotFoundError, psutil.NoSuchProcess):
            pass

# Restart a project
async def restart_project_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str, project_name: str) -> None:
    try:
        query = update.callback_query
        if query:
            await query.answer()
        
        user_id = str(user_id)
        if project_name not in user_projects.get(user_id, {}):
            await update.effective_message.reply_text("❌ Project not found.")
            return

        await update.effective_message.reply_text(f"🔁 Restarting project `{project_name}`...", parse_mode='Markdown')
        await stop_project_cmd(update, context, user_id, project_name)
        time.sleep(2) # Wait for the process to fully stop
        await start_project_cmd(update, context, user_id, project_name)
    except Exception as e:
        logger.error(f"Failed to restart project {project_name}: {e}")
        await update.effective_message.reply_text(f"❌ Failed to restart project: {e}")

# Delete a project
async def delete_project_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str, project_name: str) -> None:
    try:
        query = update.callback_query
        if query:
            await query.answer()
        
        user_id = str(user_id)
        if project_name not in user_projects.get(user_id, {}):
            await update.effective_message.reply_text("❌ Project not found.")
            return

        await update.effective_message.reply_text(f"🗑️ Deleting project `{project_name}`...", parse_mode='Markdown')
        
        project_data = user_projects[user_id][project_name]
        project_dir = project_data['directory']

        # Stop the project first
        await kill_project_process(project_data)

        # Delete the project directory
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
            
        # Remove from user_projects
        del user_projects[user_id][project_name]
        if not user_projects[user_id]:
            del user_projects[user_id]
            
        save_data()
        
        await update.effective_message.reply_text(f"✅ Project `{project_name}` deleted successfully.", parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Failed to delete project {project_name}: {e}")
        await update.effective_message.reply_text(f"❌ Failed to delete project: {e}")

# View logs menu
async def viewlogs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await maintenance_check(update, context): return
    user_id = str(update.effective_user.id)
    if is_banned_user(user_id):
        await update.effective_message.reply_text("You are banned from using this bot.")
        return

    projects = user_projects.get(user_id, {})
    if not projects:
        await update.effective_message.reply_text("You have no projects with logs to view.")
        return

    message = "📊 *View Logs*\n\nChoose a project to view its logs:"
    keyboard = []
    for project_name in projects.keys():
        keyboard.append([InlineKeyboardButton(f"📄 {project_name} Logs", callback_data=f"view_log_{project_name}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

# View logs for a specific project
async def viewlogs_for_project(update: Update, context: ContextTypes.DEFAULT_TYPE, project_name: str) -> None:
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    
    if project_name not in user_projects.get(user_id, {}):
        await query.edit_message_text("❌ Project not found.")
        return

    project_data = user_projects[user_id][project_name]
    project_dir = project_data['directory']
    log_file_path = os.path.join(project_dir, "bot.log")

    if not os.path.exists(log_file_path):
        await query.edit_message_text("❌ No log file found for this project.")
        return

    with open(log_file_path, 'r') as f:
        logs = f.read()

    log_message = (
        f"📄 *Logs for Project: {project_name}*\n\n"
        f"```ansi\n"
        f"{logs.strip()[-3500:]}\n"
        f"```\n\n"
        f"**Note:** Only the last 3500 characters are shown due to Telegram message limits."
    )
    
    keyboard = [[InlineKeyboardButton("⬅️ Back to Logs Menu", callback_data="view_logs")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(log_message, reply_markup=reply_markup, parse_mode='Markdown')
    
# Admin view all logs
async def admin_view_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.effective_message.reply_text("❌ This action is only available to admins.")
        return
        
    query = update.callback_query
    await query.answer()

    try:
        data = query.data.split('_')
        uid_to_manage = data[3]
        project_name = data[4]
        
        if project_name not in user_projects.get(uid_to_manage, {}):
            await query.edit_message_text("❌ Project not found.")
            return

        project_data = user_projects[uid_to_manage][project_name]
        project_dir = project_data['directory']
        log_file_path = os.path.join(project_dir, "bot.log")

        if not os.path.exists(log_file_path):
            await query.edit_message_text("❌ No log file found for this project.")
            return

        with open(log_file_path, 'r') as f:
            logs = f.read()

        log_message = (
            f"📄 *Logs for Project: {project_name} (User: {uid_to_manage})*\n\n"
            f"```ansi\n"
            f"{logs.strip()[-3500:]}\n"
            f"```\n\n"
            f"**Note:** Only the last 3500 characters are shown due to Telegram message limits."
        )
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Management", callback_data=f"admin_manage_project_{uid_to_manage}_{project_name}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(log_message, reply_markup=reply_markup, parse_mode='Markdown')
    except (IndexError, KeyError) as e:
        logger.error(f"Error viewing admin logs: {e}")
        await query.edit_message_text("❌ An error occurred. Please try again.")

# Statistics command - FIXED
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if await maintenance_check(update, context): return
        user_id = str(update.effective_user.id)
        if is_banned_user(user_id):
            await update.effective_message.reply_text("You are banned from using this bot.")
            return
            
        query = update.callback_query
        if query:
            await query.answer()

        total_users = len(user_projects)
        total_projects = sum(len(projects) for projects in user_projects.values())
        
        running_projects = 0
        try:
            for uid, projects in user_projects.items():
                for p_name, p_data in projects.items():
                    status, _ = get_project_status(p_data['directory'])
                    if status == "🟢 Running":
                        running_projects += 1
        except Exception as e:
            logger.error(f"Error while calculating running projects: {e}")
            running_projects = "N/A"

        total_premium_users = len(premium_users)
        
        uptime = datetime.now() - BOT_START_TIME
        
        # Get system health
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        mem_percent = memory.percent
        
        status_message = (
            f"📈 *Bot Statistics*\n\n"
            f"👥 Total Users: {total_users}\n"
            f"📂 Total Projects: {total_projects}\n"
            f"🚀 Running Projects: {running_projects}\n\n"
            f"⭐ Total Premium Users: {total_premium_users}\n"
            f"✨ Free Premium Mode: {'ON' if FREE_PREMIUM_MODE else 'OFF'}\n"
            f"👷‍♂️ Maintenance Mode: {'ON' if MAINTENANCE_MODE else 'OFF'}\n\n"
            f"⏰ Uptime: {str(uptime).split('.')[0]}\n\n"
            f"💻 *System Health:*\n"
            f"• CPU Usage: {cpu_usage:.1f}%\n"
            f"• Memory Usage: {mem_percent:.1f}%\n"
            f"• Developer: {DEVELOPER_INFO['username']}\n"
        )

        if query:
            await query.edit_message_text(status_message, parse_mode='Markdown')
        else:
            await update.effective_message.reply_text(status_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        error_msg = "❌ An error occurred while retrieving bot statistics. Please try again later."
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.effective_message.reply_text(error_msg)

# Ping command
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await maintenance_check(update, context): return
    start_time = time.time()
    sent_message = await update.effective_message.reply_text("Pinging...")
    end_time = time.time()
    latency = round((end_time - start_time) * 1000, 2)
    await sent_message.edit_text(f"Pong! 🏓\nLatency: {latency}ms")

# Uptime command
async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await maintenance_check(update, context): return
    delta = datetime.now() - BOT_START_TIME
    days, seconds = delta.days, delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    uptime_str = f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
    await update.effective_message.reply_text(f"Bot Uptime: {uptime_str}")

# About command - FIXED
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if await maintenance_check(update, context): return
        about_text = (
            f"🤖 *About Heis_Tech Bot Hostinger XMD💫*\n\n"
            f"This bot allows users to host and deploy their own Telegram bots directly from their Telegram chat.\n\n"
            f"Powered by: `Python` & `python-telegram-bot`\n"
            f"Version: `1.0.0`\n"
            f"Developer: {DEVELOPER_INFO['username']}\n"
        )
        
        # Handle both regular messages and callback queries
        if update.callback_query:
            await update.callback_query.edit_message_text(about_text, parse_mode='Markdown')
        else:
            await update.effective_message.reply_text(about_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in about command: {e}")
        error_msg = "❌ An error occurred while retrieving bot information. Please try again later."
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.effective_message.reply_text(error_msg)

# Admin access (owner only)
async def adminaccess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if user_id != BOT_OWNER_ID:
        await update.effective_message.reply_text("❌ This command is only available to the bot owner.")
        return
    await admin_panel(update, context)

# Add admin
async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if user_id != BOT_OWNER_ID:
        await update.effective_message.reply_text("❌ This command is only available to the bot owner.")
        return
        
    try:
        new_admin_id = context.args[0]
        if new_admin_id not in admin_users:
            admin_users[new_admin_id] = True
            save_data()
            await update.effective_message.reply_text(f"✅ User `{new_admin_id}` has been added as an admin.", parse_mode='Markdown')
        else:
            await update.effective_message.reply_text(f"❌ User `{new_admin_id}` is already an admin.", parse_mode='Markdown')
    except (IndexError, KeyError):
        await update.effective_message.reply_text("Please provide a user ID to add as admin. E.g., `/addadmin 123456789`")

# Remove admin
async def removeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if user_id != BOT_OWNER_ID:
        await update.effective_message.reply_text("❌ This command is only available to the bot owner.")
        return
        
    try:
        admin_to_remove = context.args[0]
        if admin_to_remove in admin_users:
            del admin_users[admin_to_remove]
            save_data()
            await update.effective_message.reply_text(f"✅ User `{admin_to_remove}` has been removed from admin.", parse_mode='Markdown')
        else:
            await update.effective_message.reply_text(f"❌ User `{admin_to_remove}` is not an admin.", parse_mode='Markdown')
    except (IndexError, KeyError):
        await update.effective_message.reply_text("Please provide a user ID to remove. E.g., `/removeadmin 123456789`")

# Free Premium Access
async def freepremiumaccess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.effective_message.reply_text("❌ This command is only available to admins.")
        return

    global FREE_PREMIUM_MODE
    FREE_PREMIUM_MODE = True
    save_data()
    await update.effective_message.reply_text("🎉 *Free Premium Access Activated!* All users now have unlimited project slots.", parse_mode='Markdown')
    await broadcast_message(context, "🎉 *FREE PREMIUM ACCESS* is now active! Enjoy unlimited project deployments for a limited time!")

# End Free Premium Access
async def onlypremium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.effective_message.reply_text("❌ This command is only available to admins.")
        return

    global FREE_PREMIUM_MODE
    FREE_PREMIUM_MODE = False
    save_data()
    await update.effective_message.reply_text("🔒 *Free Premium Access Deactivated.* The bot is now in normal mode. Only premium users have unlimited access.", parse_mode='Markdown')
    await broadcast_message(context, "🔒 The free premium access period has ended. The bot is now in normal mode. Only premium users have unlimited access. Use /buypremium to get premium.")

# Maintenance Mode
async def maintenancemode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.effective_message.reply_text("❌ This command is only available to admins.")
        return
    
    global MAINTENANCE_MODE
    
    if context.args:
        mode = context.args[0].lower()
        if mode == 'on':
            MAINTENANCE_MODE = True
            save_data()
            await update.effective_message.reply_text("👷‍♂️ *Maintenance Mode Activated.* The bot is now offline for regular users.", parse_mode='Markdown')
            await broadcast_message(context, "👷‍♂️ The bot is now in maintenance mode. Some features may be temporarily unavailable. We'll be back online soon!")
        elif mode == 'off':
            MAINTENANCE_MODE = False
            save_data()
            await update.effective_message.reply_text("✅ *Maintenance Mode Deactivated.* The bot is now back online.", parse_mode='Markdown')
            await broadcast_message(context, "✅ We're back! Maintenance mode has ended. You can now use all bot features.")
        else:
            await update.effective_message.reply_text("❌ Invalid argument. Use `/maintenancemode on` or `/maintenancemode off`.")
    else:
        current_status = "ON" if MAINTENANCE_MODE else "OFF"
        await update.effective_message.reply_text(f"Current Maintenance Mode status: `{current_status}`.", parse_mode='Markdown')

# Handle broadcast conversation
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.effective_message.reply_text("❌ This command is only available to admins.")
        return ConversationHandler.END
        
    await update.effective_message.reply_text("📝 Please enter the message you want to broadcast to all users:")
    context.user_data['state'] = 'broadcast'
    return BROADCAST_MESSAGE
    
async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("❌ This command is only available to admins.")
        return ConversationHandler.END

    message_to_broadcast = update.message.text
    
    await update.message.reply_text("📣 Broadcasting message to all users...")
    
    user_list = list(user_projects.keys())
    
    for uid in user_list:
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"📢 *BROADCAST MESSAGE*\n\n{message_to_broadcast}", parse_mode='Markdown')
            await asyncio.sleep(0.1) # Small delay to avoid hitting API limits
        except Exception as e:
            logger.error(f"Failed to send broadcast to user {uid}: {e}")
            
    await update.message.reply_text("✅ Broadcast complete!")
    return ConversationHandler.END
    
async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Broadcast cancelled.")
    return ConversationHandler.END

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update.effective_message:
        await update.effective_message.reply_text("❌ An error occurred while processing your request. Please try again or contact support.")

def main() -> None:
    load_data()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handler for new projects
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("newproject", newproject), CallbackQueryHandler(newproject, pattern="^new_project$")],
        states={
            PROJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, project_name)],
            BOT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_token)],
            REQUIREMENTS: [MessageHandler(filters.Document.ALL | (filters.TEXT & ~filters.COMMAND), requirements_file)],
            APP_PY: [MessageHandler(filters.Document.ALL | (filters.TEXT & ~filters.COMMAND), app_file)],
            ADDITIONAL_FILES: [
                CallbackQueryHandler(additional_files, pattern="^add_more_files$|^deploy_now$"),
                MessageHandler(filters.Document.ALL | (filters.TEXT & ~filters.COMMAND), handle_additional_file),
                CommandHandler("done", done)
            ],
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_message)]
        },
        fallbacks=[CommandHandler("cancel", cancel_broadcast)],
        per_user=True,
    )

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("mainmenu", mainmenu))
    application.add_handler(CommandHandler("mystatus", mystatus))
    application.add_handler(CommandHandler("buypremium", buypremium))
    application.add_handler(CommandHandler("myprojects", myprojects))
    application.add_handler(CommandHandler("viewlogs", viewlogs_menu))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("uptime", uptime))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("freepremiumaccess", freepremiumaccess))
    application.add_handler(CommandHandler("onlypremium", onlypremium))
    application.add_handler(CommandHandler("maintenancemode", maintenancemode))
    application.add_handler(CommandHandler("listpremiumusers", listpremiumusers))
    application.add_handler(CommandHandler("adminaccess", adminaccess))
    application.add_handler(CommandHandler("addadmin", addadmin))
    application.add_handler(CommandHandler("removeadmin", removeadmin))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler))

    # Add handler for M-PESA payment verification
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify_mpesa_payment))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start the Bot with asyncio
    logger.info("🤖 Bot is starting...")
    print(f"{Fore.GREEN}Initializing Heis_Tech bot hostinger XMD 💫...{Style.RESET_ALL}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

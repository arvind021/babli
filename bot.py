#!/usr/bin/env python3
"""
🔥 TELEGRAM MULTI-ACCOUNT REPORT BOT v4.0
✅ UNLIMITED Accounts ✅ Auto-login ✅ Session Manager ✅ Reports
"""

import asyncio
import logging
import re
import sqlite3
import os
import json
import aiosqlite
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import (
    PhoneCodeInvalidError, SessionPasswordNeededError, 
    FloodWaitError, PhoneNumberBannedError
)

# 🔥 CONFIG - Edit these
API_ID = 21552265  # Your API ID
API_HASH = "1c971ae7e62cc416ca977e040e700d09"  # Your API Hash
BOT_TOKEN = "8057384324:AAFiDKf4vZZdS0hsmu2hMk4GnS2Bhpiz5tY"  # Bot token

# Categories
REPORT_CATEGORIES = {
    'spam': 2, 'scam': 4, 'porn': 5, 'violence': 5, 'leak': 4,
    'copyright': 2, 'harassment': 3, 'illegal': 5, 'fake': 3, 'other': 1
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class MultiAccountBot:
    def __init__(self):
        self.accounts_db = 'accounts.db'
        self.reports_db = 'reports.db'
        self.active_clients = {}
        self.client = None
    
    async def init_dbs(self):
        """Initialize all databases"""
        async with aiosqlite.connect(self.accounts_db) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    name TEXT PRIMARY KEY,
                    phone TEXT UNIQUE,
                    session TEXT,
                    status TEXT DEFAULT 'active',
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()
        
        async with aiosqlite.connect(self.reports_db) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_name TEXT,
                    account_phone TEXT,
                    target_type TEXT,
                    target_id INTEGER,
                    target_username TEXT,
                    target_title TEXT,
                    category TEXT,
                    reason TEXT,
                    severity INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()
        logger.info("✅ Databases ready")
    
    async def list_accounts(self):
        """List all accounts"""
        async with aiosqlite.connect(self.accounts_db) as db:
            async with db.execute('SELECT name, phone, status FROM accounts ORDER BY last_used DESC') as cursor:
                rows = await cursor.fetchall()
        
        if not rows:
            return "**📱 No accounts**"
        
        text = f"**📱 {len(rows)} Accounts:**\n\n"
        for name, phone, status in rows[:10]:  # Top 10
            emoji = "🟢" if status == 'active' else "🔴"
            text += f"{emoji} `{name}`: `{phone}`\n"
        return text
    
    async def add_account(self, name: str, phone: str):
        """Add/login new account"""
        try:
            # Create session directory
            os.makedirs('sessions', exist_ok=True)
            
            client = TelegramClient(
                f'sessions/{name}', API_ID, API_HASH
            )
            
            await client.connect()
            
            if not await client.is_user_authorized():
                # Send code
                sent = await client.send_code_request(phone)
                code = input(f"📱 [{name}] Enter code for {phone}: ").strip()
                
                try:
                    await client.sign_in(phone, code, force_sms=False)
                except SessionPasswordNeededError:
                    password = input(f"🔐 [{name}] 2FA Password: ")
                    await client.sign_in(password=password)
                except PhoneCodeInvalidError:
                    return False, "❌ Wrong code!"
            
            me = await client.get_me()
            session = client.session.save()
            
            # Save to DB
            async with aiosqlite.connect(self.accounts_db) as db:
                await db.execute(
                    'INSERT OR REPLACE INTO accounts (name, phone, session, status) VALUES (?, ?, ?, ?)',
                    (name, me.phone, session, 'active')
                )
                await db.commit()
            
            logger.info(f"✅ [{name}] {me.phone} added")
            await client.disconnect()
            return True, f"✅ **{name}** ({me.phone}) **ADDED**"
            
        except PhoneNumberBannedError:
            return False, f"🚫 **{phone}** is **BANNED**"
        except FloodWaitError as e:
            return False, f"⏳ **FloodWait:** Wait {e.seconds} seconds"
        except Exception as e:
            logger.error(f"❌ Add account failed: {e}")
            return False, f"❌ **Error:** {str(e)}"
    
    async def get_client(self, account_name: str):
        """Get active client"""
        if account_name in self.active_clients:
            return self.active_clients[account_name]
        
        async with aiosqlite.connect(self.accounts_db) as db:
            async with db.execute('SELECT session FROM accounts WHERE name = ?', (account_name,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
        
        try:
            client = TelegramClient(
                StringSession(row[0]), API_ID, API_HASH
            )
            await client.connect()
            if await client.is_user_authorized():
                self.active_clients[account_name] = client
                return client
        except:
            pass
        return None
    
    async def report_target(self, account_name: str, target_type: str, target: str, reason: str):
        """Create report from account"""
        client = await self.get_client(account_name)
        if not client:
            return None, f"❌ Account `{account_name}` **not ready**"
        
        parsed = self.parse_report(target_type, target, reason)
        if not parsed:
            return None, "❌ **Invalid format**"
        
        try:
            entity = await client.get_entity(parsed['target'])
            entity_info = {
                'type': self.get_entity_type(entity),
                'id': entity.id,
                'username': getattr(entity, 'username', None),
                'title': getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown'))
            }
        except:
            return None, f"⚠️ **@{parsed['target']}** not found"
        
        # Save report
        async with aiosqlite.connect(self.reports_db) as db:
            me = await client.get_me()
            await db.execute('''
                INSERT INTO reports (account_name, account_phone, target_type, target_id,
                target_username, target_title, category, reason, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                account_name, me.phone, entity_info['type'], entity_info['id'],
                entity_info['username'] or parsed['target'], entity_info['title'],
                parsed['category'], parsed['reason'], parsed['severity']
            ))
            await db.commit()
            
            async with db.execute('SELECT last_insert_rowid()') as cursor:
                report_id = (await cursor.fetchone())[0]
        
        return report_id, f"✅ **#{report_id}** SAVED (Lv{parsed['severity']})"
    
    def parse_report(self, cmd_type, target, reason):
        """Parse report command"""
        target = target.strip().lstrip('@')
        if len(target) < 3:
            return None
        
        category = self.detect_category(reason)
        return {
            'type': cmd_type,
            'target': target,
            'category': category,
            'reason': f"{category.capitalize()}: {reason}",
            'severity': REPORT_CATEGORIES.get(category, 1)
        }
    
    def detect_category(self, reason):
        reason = reason.lower()
        for cat in REPORT_CATEGORIES:
            if cat in reason:
                return cat
        return 'other'
    
    def get_entity_type(self, entity):
        if hasattr(entity, 'bot') and entity.bot:
            return 'bot'
        if hasattr(entity, 'broadcast') and entity.broadcast:
            return 'channel'
        if hasattr(entity, 'megagroup') and entity.megagroup:
            return 'group'
        return 'user'

# 🔥 Bot instance
bot = MultiAccountBot()

# ✅ Proper event handler registration
async def register_handlers(client):
    """Register all event handlers"""
    
    @client.on(events.NewMessage(pattern=r'/add_account\s+(\w+)\s*(\+?\d{10,15})'))
    async def add_account(event):
        name = event.pattern_match.group(1)
        phone = event.pattern_match.group(2)
        
        await event.reply(f"🔄 **Adding** `{name}`...")
        success, msg = await bot.add_account(name, phone)
        await event.edit(msg)

    @client.on(events.NewMessage(pattern='/accounts'))
    async def list_accounts(event):
        text = await bot.list_accounts()
        await event.reply(text)

    @client.on(events.NewMessage(pattern=r'/report_(\w+)\s+(\w+)\s+(.+?)(?:\s+(.+))?'))
    async def report_handler(event):
        """ /report_user main @target spam """
        cmd_type = event.pattern_match.group(1)  # user/bot/group/channel
        account = event.pattern_match.group(2)   # main
        target = event.pattern_match.group(3)    # @target  
        reason = event.pattern_match.group(4) or 'spam'
        
        await event.reply(f"🔍 **[{account}]** checking `{target}`...")
        
        report_id, msg = await bot.report_target(account, cmd_type, target, reason)
        await event.edit(msg)

    @client.on(events.NewMessage(pattern='/stats'))
    async def stats(event):
        async with aiosqlite.connect(bot.reports_db) as db:
            async with db.execute('SELECT COUNT(*) FROM reports') as c:
                total = (await c.fetchone())[0]
            
            if total == 0:
                await event.reply("📊 **No reports**")
                return
            
            async with db.execute('''
                SELECT account_name, COUNT(*), AVG(severity) 
                FROM reports GROUP BY account_name ORDER BY COUNT(*) DESC
            ''') as c:
                rows = await c.fetchall()
        
        stats_text = f"**📊 {total} Reports:**\n\n"
        for acc, count, avg in rows[:5]:
            stats_text += f"• `{acc}`: **{count}** (Ø{avg:.1f})\n"
        await event.reply(stats_text)

    @client.on(events.NewMessage(pattern='/help'))
    async def help_cmd(event):
        help_text = """
**🔥 Multi-Account Bot**

**📱 Accounts:**
`/add_account name +919876543210`
`/accounts` - List all

**📤 Reports:**
`/report_bot main @ApiHashGeneratorBot porn`
`/report_group main -100123456 leak`
`/report_user main @username spam`

**📊 Stats:** `/stats`

**Example flow:**
1. `/add_account acc1 +919876543210`
2. Enter code when prompted  
3. `/report_bot acc1 @target scam`
        """
        await event.reply(help_text)

async def main():
    # ✅ पहले databases initialize करो
    await bot.init_dbs()
    
    # फिर bot client बनाओ
    client = TelegramClient('bot_session', API_ID, API_HASH)
    await client.start(bot_token=BOT_TOKEN)
    bot.client = client
    await register_handlers(client)
    print("🚀 Multi-Account Bot LIVE!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())

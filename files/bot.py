import discord
from discord.ext import commands
import os
import asyncio
from database import init_db

# ── Config ────────────────────────────────────────────────────────────────────
TOKEN      = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_ID   = int(os.getenv("OWNER_ID", "0"))   # Your Discord user ID

# ── Bot setup ─────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix="!",   # unused but required
    intents=intents,
    owner_id=OWNER_ID
)

COGS = ["cogs.keys", "cogs.users", "cogs.admin"]


@bot.event
async def on_ready():
    await init_db()
    print(f"[✓] Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"[✓] Database initialized.")
    print(f"[✓] Loaded cogs: {COGS}")
    print("─" * 40)
    print("Run /synccommands to register slash commands.")


async def main():
    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())

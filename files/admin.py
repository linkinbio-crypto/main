import discord
from discord import app_commands
from discord.ext import commands
from database import get_audit_log, log_action
from utils import is_admin, admin_only_embed


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /auditlog ─────────────────────────────────────────────────────────────
    @app_commands.command(name="auditlog", description="View the last N audit log entries.")
    @app_commands.describe(limit="Number of entries to show (max 25)")
    async def auditlog(self, interaction: discord.Interaction, limit: int = 10):
        if not await is_admin(interaction):
            await interaction.response.send_message(embed=admin_only_embed(), ephemeral=True)
            return

        limit = min(max(limit, 1), 25)
        await interaction.response.defer(ephemeral=True)
        entries = await get_audit_log(limit)

        embed = discord.Embed(title="📋 Audit Log", color=discord.Color.blurple())

        if not entries:
            embed.description = "No audit log entries found."
        else:
            lines = []
            for e in entries:
                ts = e["timestamp"][:16].replace("T", " ")
                target = f"→ `{e['target']}`" if e["target"] else ""
                detail = f"({e['detail']})" if e["detail"] else ""
                lines.append(f"`{ts}` **{e['action']}** by <@{e['actor']}> {target} {detail}")
            embed.description = "\n".join(lines)

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /stats ────────────────────────────────────────────────────────────────
    @app_commands.command(name="stats", description="Show bot database statistics.")
    async def stats(self, interaction: discord.Interaction):
        if not await is_admin(interaction):
            await interaction.response.send_message(embed=admin_only_embed(), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        import aiosqlite
        async with aiosqlite.connect("bot.db") as db:
            async with db.execute("SELECT COUNT(*) FROM keys") as cur:
                total_keys = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM keys WHERE is_redeemed=1") as cur:
                redeemed = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM keys WHERE is_lifetime=1") as cur:
                lifetime = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM keys WHERE is_blacklisted=1") as cur:
                bl_keys = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM users") as cur:
                total_users = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM users WHERE blacklisted=1") as cur:
                bl_users = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM users WHERE whitelisted=1") as cur:
                wl_users = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM hwid_resets") as cur:
                hwid_resets = (await cur.fetchone())[0]

        embed = discord.Embed(title="📊 Bot Statistics", color=discord.Color.gold())
        embed.add_field(name="Total Keys", value=str(total_keys), inline=True)
        embed.add_field(name="Redeemed", value=str(redeemed), inline=True)
        embed.add_field(name="Lifetime Keys", value=str(lifetime), inline=True)
        embed.add_field(name="Blacklisted Keys", value=str(bl_keys), inline=True)
        embed.add_field(name="Total Users", value=str(total_users), inline=True)
        embed.add_field(name="Whitelisted Users", value=str(wl_users), inline=True)
        embed.add_field(name="Blacklisted Users", value=str(bl_users), inline=True)
        embed.add_field(name="HWID Resets", value=str(hwid_resets), inline=True)

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /synccommands ─────────────────────────────────────────────────────────
    @app_commands.command(name="synccommands", description="Sync slash commands (owner only).")
    async def synccommands(self, interaction: discord.Interaction):
        if interaction.user.id != self.bot.owner_id:
            await interaction.response.send_message("❌ Only the bot owner can sync commands.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        synced = await self.bot.tree.sync()
        await log_action("SYNC_COMMANDS", str(interaction.user.id), detail=f"{len(synced)} commands synced")
        await interaction.followup.send(f"✅ Synced **{len(synced)}** slash commands.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(AdminCog(bot))

import discord
from discord import app_commands
from discord.ext import commands
from database import (
    get_user, set_whitelist, set_blacklist,
    reset_hwid, bind_hwid, log_action, redeem_key
)
from utils import is_admin, admin_only_embed


class UsersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /redeem ───────────────────────────────────────────────────────────────
    @app_commands.command(name="redeem", description="Redeem a license key.")
    @app_commands.describe(key="Your license key", hwid="Your hardware ID")
    async def redeem(self, interaction: discord.Interaction, key: str, hwid: str):
        await interaction.response.defer(ephemeral=True)
        success, msg = await redeem_key(key.upper(), str(interaction.user.id), hwid)
        await log_action("REDEEM", str(interaction.user.id), key.upper(), msg)

        color = discord.Color.green() if success else discord.Color.red()
        embed = discord.Embed(description=msg, color=color)
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /userinfo ─────────────────────────────────────────────────────────────
    @app_commands.command(name="userinfo", description="Look up a user's license info.")
    @app_commands.describe(user="The Discord user to inspect")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member):
        if not await is_admin(interaction):
            await interaction.response.send_message(embed=admin_only_embed(), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        data = await get_user(str(user.id))

        embed = discord.Embed(
            title=f"👤 User Info — {user}",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        if not data:
            embed.description = "No record found for this user."
        else:
            embed.add_field(name="Key ID", value=f"`{data['key_id']}`" if data["key_id"] else "None", inline=False)
            embed.add_field(name="HWID Bound", value="✅ Yes" if data["hwid"] else "❌ No", inline=True)
            embed.add_field(name="Whitelisted", value="✅ Yes" if data["whitelisted"] else "❌ No", inline=True)
            embed.add_field(name="Blacklisted", value="🚫 Yes" if data["blacklisted"] else "✅ No", inline=True)
            embed.add_field(name="Joined", value=data["joined_at"][:10] if data["joined_at"] else "N/A", inline=True)

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /whitelist ────────────────────────────────────────────────────────────
    @app_commands.command(name="whitelist", description="Whitelist a user.")
    @app_commands.describe(user="User to whitelist", state="True to whitelist, False to remove")
    async def whitelist(self, interaction: discord.Interaction, user: discord.Member, state: bool):
        if not await is_admin(interaction):
            await interaction.response.send_message(embed=admin_only_embed(), ephemeral=True)
            return

        await set_whitelist(str(user.id), state)
        await log_action(
            "WHITELIST" if state else "UNWHITELIST",
            str(interaction.user.id), str(user.id)
        )
        action = "whitelisted ✅" if state else "removed from whitelist ❌"
        await interaction.response.send_message(f"{user.mention} has been **{action}**.", ephemeral=True)

    # ── /blacklist ────────────────────────────────────────────────────────────
    @app_commands.command(name="blacklist", description="Blacklist a user.")
    @app_commands.describe(user="User to blacklist", state="True to blacklist, False to remove")
    async def blacklist(self, interaction: discord.Interaction, user: discord.Member, state: bool):
        if not await is_admin(interaction):
            await interaction.response.send_message(embed=admin_only_embed(), ephemeral=True)
            return

        await set_blacklist(str(user.id), state)
        await log_action(
            "BLACKLIST" if state else "UNBLACKLIST",
            str(interaction.user.id), str(user.id)
        )
        action = "blacklisted 🚫" if state else "removed from blacklist ✅"
        await interaction.response.send_message(f"{user.mention} has been **{action}**.", ephemeral=True)

    # ── /hwidreset ────────────────────────────────────────────────────────────
    @app_commands.command(name="hwidreset", description="Reset a user's bound HWID.")
    @app_commands.describe(user="User whose HWID to reset", reason="Reason for the reset")
    async def hwidreset(self, interaction: discord.Interaction, user: discord.Member, reason: str = None):
        if not await is_admin(interaction):
            await interaction.response.send_message(embed=admin_only_embed(), ephemeral=True)
            return

        success, msg = await reset_hwid(str(user.id), str(interaction.user.id), reason)
        await log_action("HWID_RESET", str(interaction.user.id), str(user.id), reason)

        color = discord.Color.green() if success else discord.Color.red()
        embed = discord.Embed(description=f"{user.mention} — {msg}", color=color)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /hwidbind ─────────────────────────────────────────────────────────────
    @app_commands.command(name="hwidbind", description="Manually bind an HWID to a user.")
    @app_commands.describe(user="Target user", hwid="Hardware ID to bind")
    async def hwidbind(self, interaction: discord.Interaction, user: discord.Member, hwid: str):
        if not await is_admin(interaction):
            await interaction.response.send_message(embed=admin_only_embed(), ephemeral=True)
            return

        success, msg = await bind_hwid(str(user.id), hwid)
        await log_action("HWID_BIND", str(interaction.user.id), str(user.id))

        color = discord.Color.green() if success else discord.Color.red()
        embed = discord.Embed(description=f"{user.mention} — {msg}", color=color)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(UsersCog(bot))

import discord
from discord import Interaction
from datetime import datetime, timezone
import os


ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", "0"))


async def is_admin(interaction: Interaction) -> bool:
    """Returns True if the user is the bot owner or has the admin role."""
    bot = interaction.client
    if interaction.user.id == bot.owner_id:
        return True
    if isinstance(interaction.user, discord.Member):
        return any(r.id == ADMIN_ROLE_ID for r in interaction.user.roles)
    return False


def admin_only_embed() -> discord.Embed:
    return discord.Embed(
        description="❌ You don't have permission to use this command.",
        color=discord.Color.red()
    )


async def format_key_embed(data: dict, bot) -> discord.Embed:
    """Build a rich embed for key info."""
    is_lifetime = bool(data["is_lifetime"])
    is_redeemed = bool(data["is_redeemed"])
    is_blacklisted = bool(data["is_blacklisted"])

    # Status color
    if is_blacklisted:
        color = discord.Color.red()
        status = "🚫 Blacklisted"
    elif is_redeemed:
        color = discord.Color.green()
        status = "✅ Redeemed"
    else:
        color = discord.Color.gold()
        status = "⏳ Unredeemed"

    embed = discord.Embed(title="🔑 Key Info", color=color)
    embed.add_field(name="Key ID", value=f"`{data['key_id']}`", inline=False)
    embed.add_field(name="Status", value=status, inline=True)
    embed.add_field(name="Type", value="♾️ Lifetime" if is_lifetime else f"⏳ {data['duration_days']}d", inline=True)

    # Creator
    creator_mention = f"<@{data['created_by']}>" if data["created_by"] else "Unknown"
    embed.add_field(name="Created By", value=creator_mention, inline=True)
    embed.add_field(name="Created At", value=data["created_at"][:10], inline=True)

    if is_redeemed:
        redeemer_mention = f"<@{data['redeemed_by']}>" if data["redeemed_by"] else "Unknown"
        embed.add_field(name="Redeemed By", value=redeemer_mention, inline=True)
        embed.add_field(name="Redeemed At", value=data["redeemed_at"][:10] if data["redeemed_at"] else "N/A", inline=True)

        # Expiry
        if not is_lifetime and data["expires_at"]:
            expires = datetime.fromisoformat(data["expires_at"])
            now = datetime.now(timezone.utc)
            remaining = (expires - now).days
            expired = now > expires
            expiry_str = f"{data['expires_at'][:10]} ({'❌ Expired' if expired else f'~{remaining}d left'})"
            embed.add_field(name="Expires", value=expiry_str, inline=True)

        embed.add_field(name="HWID Bound", value="✅ Yes" if data["hwid"] else "❌ No", inline=True)

    if data["note"]:
        embed.add_field(name="Note", value=data["note"], inline=False)

    return embed

from src.discord_client import *
from src.models import BossEntry,ALL_BOSSES

# Build the mapping from key -> BossEntry based on the 'key' field
BOSSES_INFORMATION = {entry.name: entry for entry in ALL_BOSSES}


@tree.command(name="boss", description="Find a boss information by its name")
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.describe(
    name="The name of the boss to find.",
    just_for_me="Only show the definition to me. (Default: False)",
)
async def boss(
    interaction: discord.Interaction,
    name: str,
    just_for_me: bool = False,
) -> None:
    embed = discord.Embed()
    entry = BOSSES_INFORMATION.get(name.lower())
    if entry is None:
        await interaction.response.send_message(f"Unknown boss: {name}", ephemeral=just_for_me)
        return
    embed.title = name.capitalize()
    embed.description = f"""
    Key needed: **{entry.key.capitalize()}**
    Attack style: 🛡️{entry.attack_style}
    Attack style weakness: ⚔️{entry.attack_weakness}"""
    embed.url = "https://wiki.idleclans.com/index.php/" + entry.wiki
    embed.color = entry.trim_color
    await interaction.response.send_message(embeds=[embed], ephemeral=just_for_me)

@boss.autocomplete("name")
async def boss_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[discord.app_commands.Choice]:
    choices = [
        discord.app_commands.Choice(name=key.capitalize(), value=key)
        for key in BOSSES_INFORMATION.keys()
        if current.lower() in key.lower()
    ]
    return choices[:25]
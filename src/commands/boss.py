from src.discord_client import *

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
    key = KEYS_INFORMATION.get(name.lower())
    if key is None:
        await interaction.response.send_message(f"Unknown key: {name}", ephemeral=just_for_me)
        return
    embed.title = name.capitalize() + " key"
    embed.description = f"""
    **{key.name}**
    Attack style: 🛡️{key.attack_style}
    Attack style weakness: ⚔️{key.attack_weakness}"""
    embed.url = "https://wiki.idleclans.com/index.php/" + key.wiki
    embed.color = key.trim_color
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
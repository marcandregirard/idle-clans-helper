from src.discord_client import *

MESSAGES = {
    "zeus": """
Key needed: **Godly**
Attack style: 🛡️Magic
Attack style weakness: ⚔️Archery""",
    "medusa": """
Key needed: **Stone**
Attack style: 🛡️Archery
Attack style weakness: ⚔️Slash""",
    "hades": """
Key needed: **Underworld**
Attack style: 🛡️Magic
Attack style weakness: Stab""",
    "griffin": """
Key needed: **Mountain**
Attack style: 🛡️Melee
Attack style weakness: ⚔️Crush
""",
    "devil": """
Key needed: **Burning**
Attack style: 🛡️Melee
Attack style weakness: ⚔️Pound""",
    "chimera": """
Key  needed: **Mutated** 
Attack style: 🛡️Melee
Attack style weakness: ⚔️Magic"""
}


@tree.command(name="boss", description="Find a boss")
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
    message = MESSAGES.get(name.lower())
    message = message if message else "No bosses associated with this value"
    embed.title = name.capitalize() + " :"
    embed.description = message
    await interaction.response.send_message(embeds=[embed], ephemeral=just_for_me)

@boss.autocomplete("name")
async def boss_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[discord.app_commands.Choice[str]]:
    choices = [
        discord.app_commands.Choice(name=key.capitalize(), value=key)
        for key in MESSAGES.keys()
        if current.lower() in key.lower()
    ]
    return choices[:25]
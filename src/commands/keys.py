from src.discord_client import *

MESSAGES = {
    "godly": """ 
Boss name: **ZEUS**
Attack style: 🛡️Magic
Attack style weakness: ⚔️Archery""",
    "stone": """ 
Boss name: **Medusa**
Attack style: 🛡️Archery
Attack style weakness: ⚔️Slash""",
    "underworld": """ 
Boss name: **Hades**
Attack style: 🛡️Magic
Attack style weakness: Stab""",
    "mountain": """ 
Boss name: **Griffin**
Attack style: 🛡️Melee
Attack style weakness: ⚔️Crush
""",
    "burning": """ 
Boss name: **Devil**
Attack style: 🛡️Melee
Attack style weakness: ⚔️Pound""",
    "mutated": """
Boss name: **Chimera**
Attack style: 🛡️Melee
Attack style weakness: ⚔️Magic"""
}


@tree.command(name="keys", description="Find a boss")
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.describe(
    name="The name of the key you have and will return the boss information.",
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
    embed.title = name.capitalize() + " key:"
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
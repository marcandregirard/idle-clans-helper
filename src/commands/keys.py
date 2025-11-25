from src.discord_client import *

KEYS_INFORMATION = {
    "godly": {"description": """ 
Boss name: **ZEUS**
Attack style: 🛡️Magic
Attack style weakness: ⚔️Archery""", "wiki": "Zeus", "trim_color": discord.Color.gold()},
    "stone": {"description": """ 
Boss name: **Medusa**
Attack style: 🛡️Archery
Attack style weakness: ⚔️Slash""", "wiki": "Medusa", "trim_color": discord.Color.light_grey()},
    "underworld": {"description": """ 
Boss name: **Hades**
Attack style: 🛡️Magic
Attack style weakness: Stab""", "wiki": "Hades", "trim_color": discord.Color.blue()},
    "mountain": {"description": """ 
Boss name: **Griffin**
Attack style: 🛡️Melee
Attack style weakness: ⚔️Crush
""", "wiki": "Griffin", "trim_color": discord.Color.dark_gold()},
    "burning": {"description": """ 
Boss name: **Devil**
Attack style: 🛡️Melee
Attack style weakness: ⚔️Pound""", "wiki": "Devil", "trim_color": discord.Color.red()},
    "mutated": {"description": """
Boss name: **Chimera**
Attack style: 🛡️Melee
Attack style weakness: ⚔️Magic""", "wiki": "Chimera", "trim_color": discord.Color.green()}
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
    key = KEYS_INFORMATION.get(name.lower())
    embed.title = name.capitalize() + " key:"
    embed.description = key["description"]
    embed.url = "https://wiki.idleclans.com/index.php/" + key["wiki"]
    embed.color = key["trim_color"]
    await interaction.response.send_message(embeds=[embed], ephemeral=just_for_me)


@boss.autocomplete("name")
async def boss_autocomplete(
        interaction: discord.Interaction,
        current: str,
) -> list[discord.app_commands.Choice[str]]:
    choices = [
        discord.app_commands.Choice(name=key.capitalize(), value=key)
        for key in KEYS_INFORMATION.keys()
        if current.lower() in key.lower()
    ]
    return choices[:25]

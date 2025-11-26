from .bossEntry import BossEntry
import discord

__all__ = ["BossEntry"]

# Define list of BossEntry objects so other code can import the list if needed
ALL_BOSSES = [
    BossEntry(name="ZEUS", attack_style="Magic", attack_weakness="Archery", wiki="Zeus",
              trim_color=discord.Color.gold(), key="godly"),
    BossEntry(name="Medusa", attack_style="Archery", attack_weakness="Slash", wiki="Medusa",
              trim_color=discord.Color.light_grey(), key="stone"),
    BossEntry(name="Hades", attack_style="Magic", attack_weakness="Stab", wiki="Hades",
              trim_color=discord.Color.blue(), key="underworld"),
    BossEntry(name="Griffin", attack_style="Melee", attack_weakness="Crush", wiki="Griffin",
              trim_color=discord.Color.dark_gold(), key="mountain"),
    BossEntry(name="Devil", attack_style="Melee", attack_weakness="Pound", wiki="Devil",
              trim_color=discord.Color.red(), key="burning"),
    BossEntry(name="Chimera", attack_style="Melee", attack_weakness="Magic", wiki="Chimera",
              trim_color=discord.Color.green(), key="mutated"),
]
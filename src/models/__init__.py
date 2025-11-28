from .bossEntry import BossEntry
import discord

__all__ = ["BossEntry"]

# Define list of BossEntry objects so other code can import the list if needed
ALL_BOSSES = [
    BossEntry(name="zeus", attack_style="Magic", attack_weakness="Archery", wiki="Zeus",
              trim_color=discord.Color.gold(), key="godly"),
    BossEntry(name="medusa", attack_style="Archery", attack_weakness="Slash", wiki="Medusa",
              trim_color=discord.Color.light_grey(), key="stone"),
    BossEntry(name="hades", attack_style="Magic", attack_weakness="Stab", wiki="Hades",
              trim_color=discord.Color.blue(), key="underworld"),
    BossEntry(name="griffin", attack_style="Melee", attack_weakness="Crush", wiki="Griffin",
              trim_color=discord.Color.dark_gold(), key="mountain"),
    BossEntry(name="devil", attack_style="Melee", attack_weakness="Pound", wiki="Devil",
              trim_color=discord.Color.red(), key="burning"),
    BossEntry(name="chimera", attack_style="Melee", attack_weakness="Magic", wiki="Chimera",
              trim_color=discord.Color.green(), key="mutated"),
    BossEntry(name="sobek", attack_style="Archery", attack_weakness="None", wiki="Sobek",
              trim_color=discord.Color.green(), key="ancient"),
    BossEntry(name="kronos", attack_style="Archery,Magic,Melee", attack_weakness="Differs(Archery,Magic,Melee)", wiki="Kronos",
              trim_color=discord.Color.green(), key="krono's book"),
    BossEntry(name="mesines", attack_style="Melee/Magic", attack_weakness="Archery", wiki="Mesines",
              trim_color=discord.Color.green(), key="otherworldly"),
]
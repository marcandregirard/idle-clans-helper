class BossEntry:
    def __init__(self, name: str, attack_style: str, attack_weakness: str, wiki: str, trim_color: int, key: str):
        self.name = name
        self.attack_style = attack_style
        self.attack_weakness = attack_weakness
        self.wiki = wiki
        self.trim_color = trim_color
        self.key = key

    def get_description(self) -> str:
        return f"**{self.name}**\nAttack style: 🛡️{self.attack_style}\nAttack style weakness: ⚔️{self.attack_weakness}"

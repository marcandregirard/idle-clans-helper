import discord

_channel_cache: dict[str, discord.TextChannel] = {}


def find_channel_by_name(client: discord.Client, name: str) -> discord.TextChannel | None:
    cached = _channel_cache.get(name)
    if cached is not None:
        return cached

    for channel in client.get_all_channels():
        if isinstance(channel, discord.TextChannel) and channel.name == name:
            _channel_cache[name] = channel
            return channel
    return None

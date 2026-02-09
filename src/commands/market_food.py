"""Market food command - shows cost-effective food items based on current market prices."""

import logging
from dataclasses import dataclass

import aiohttp
import discord
from discord import app_commands

from src.discord_client import tree

# Food items (name_id) and their healing values
FOOD_HEALING_VALUES = {
    "cooked_piranha": 2,
    "cooked_perch": 3,
    "cooked_mackerel": 4,
    "cooked_cod": 6,
    "cooked_trout": 7,
    "cooked_salmon": 8,
    "cooked_carp": 10,
    "cooked_zander": 12,
    "cooked_pufferfish": 14,
    "cooked_anglerfish": 16,
    "cooked_tuna": 17,
    "cooked_bloodmoon_eel": 24,
    "cooked_meat": 4,
    "cooked_giant_meat": 8,
    "cooked_quality_meat": 12,
    "cooked_superior_meat": 18,
    "cooked_apex_meat": 20,
    "potato_soup": 5,
    "meat_burger": 7,
    "cod_soup": 10,
    "blueberry_pie": 11,
    "salmon_salad": 14,
    "porcini_soup": 17,
    "stew": 19,
    "power_pizza": 22,
}

# Item ID mapping (name_id -> internal_id)
ITEM_ID_MAPPING = {
    "cooked_mackerel": 100,
    "cooked_perch": 102,
    "cooked_trout": 104,
    "cooked_salmon": 105,
    "cooked_carp": 106,
    "cooked_meat": 114,
    "cooked_giant_meat": 115,
    "cooked_quality_meat": 116,
    "cooked_superior_meat": 117,
    "potato_soup": 140,
    "meat_burger": 141,
    "cod_soup": 143,
    "blueberry_pie": 144,
    "salmon_salad": 145,
    "porcini_soup": 146,
    "power_pizza": 148,
    "cooked_anglerfish": 156,
    "cooked_zander": 158,
    "cooked_piranha": 160,
    "cooked_pufferfish": 162,
    "cooked_cod": 164,
    "stew": 559,
    "cooked_tuna": 562,
    "cooked_bloodmoon_eel": 888,
    "cooked_apex_meat": 906,
}


@dataclass
class FoodValueResult:
    """Represents calculated food value results for display."""

    name: str
    healing: int
    price: float
    cost_per_healing: float


async def _fetch_market_prices() -> dict[int, float]:
    """Fetch latest market prices from the Idle Clans API.

    Returns:
        Dictionary mapping item ID to lowest sell price

    Raises:
        Exception: If all retry attempts fail
    """
    url = "https://query.idleclans.com/api/PlayerMarket/items/prices/latest?includeAveragePrice=true"

    # Retry logic: 3 attempts with exponential backoff
    for attempt in range(3):
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logging.warning(
                            "[market-food] API returned status %d on attempt %d",
                            response.status,
                            attempt + 1,
                        )
                        if attempt < 2:
                            continue
                        raise Exception(f"API returned status {response.status}")

                    data = await response.json()

                    # Build price map
                    price_map = {}
                    for item in data:
                        item_id = item.get("itemId")
                        lowest_price = item.get("lowestSellPrice")
                        if item_id is not None and lowest_price is not None:
                            price_map[item_id] = lowest_price

                    logging.info(
                        "[market-food] fetched prices for %d items", len(price_map)
                    )
                    return price_map

        except Exception as e:
            logging.warning(
                "[market-food] attempt %d failed: %s", attempt + 1, e
            )
            if attempt == 2:
                raise Exception(f"Failed after 3 attempts: {e}")

    raise Exception("Failed to fetch market prices")


def _calculate_food_values(price_map: dict[int, float]) -> list[FoodValueResult]:
    """Calculate cost per HP for all food items.

    Args:
        price_map: Dictionary mapping item ID to price

    Returns:
        List of FoodValueResult sorted by cost per healing (best value first)
    """
    results = []

    for food_name, healing in FOOD_HEALING_VALUES.items():
        item_id = ITEM_ID_MAPPING.get(food_name)
        if item_id is None:
            logging.warning("[market-food] no item ID found for: %s", food_name)
            continue

        price = price_map.get(item_id)
        if price is None:
            logging.debug("[market-food] no price data for: %s", food_name)
            continue

        if price <= 0:
            logging.warning(
                "[market-food] invalid price for %s: %.2f", food_name, price
            )
            continue

        cost_per_healing = price / healing

        results.append(
            FoodValueResult(
                name=food_name,
                healing=healing,
                price=price,
                cost_per_healing=cost_per_healing,
            )
        )

    # Sort by cost per healing (best value first)
    results.sort(key=lambda x: x.cost_per_healing)

    return results


def _filter_dominated_items(results: list[FoodValueResult]) -> list[FoodValueResult]:
    """Remove items that are economically dominated.

    An item is dominated if another item exists that heals >= HP and costs < per HP.

    Args:
        results: List of food value results

    Returns:
        List of non-dominated items
    """
    non_dominated = []

    for i, item_i in enumerate(results):
        is_dominated = False

        # Check if this item is dominated by any other item
        for j, item_j in enumerate(results):
            if i != j:
                # Item j dominates item i if:
                # - j heals >= i's healing, AND
                # - j costs less per HP than i
                if (
                    item_j.healing >= item_i.healing
                    and item_j.cost_per_healing < item_i.cost_per_healing
                ):
                    is_dominated = True
                    break

        if not is_dominated:
            non_dominated.append(item_i)

    return non_dominated


def _format_food_embed(results: list[FoodValueResult]) -> discord.Embed:
    """Create Discord embed for food values.

    Args:
        results: List of food value results to display

    Returns:
        Discord embed with formatted food values
    """
    embed = discord.Embed(
        title="Market Food Values - Cost Effective Options",
        description=f"Showing {len(results)} economically viable food items based on current market prices",
        color=0x00FF00,  # Green
    )

    # Add a field for each food item
    for result in results:
        # Format the food name (title case and replace underscores)
        food_name = result.name.replace("_", " ").title()

        # Format: "{HP value} HP - {item name}" for title
        field_name = f"{result.healing} HP - {food_name}"

        # Format: "{Cost} g, {Cost per HP} g/HP" for value
        field_value = f"{result.price:.0f} g, {result.cost_per_healing:.1f} g/HP"

        embed.add_field(name=field_name, value=field_value, inline=True)

    embed.set_footer(text="Data from Idle Clans market API")

    return embed


@tree.command(
    name="market-food",
    description="Show cost-effective food items based on current market prices",
)
@app_commands.describe(
    just_for_me="Only show the results to me (default: visible to everyone)"
)
async def market_food(
    interaction: discord.Interaction,
    just_for_me: bool = False,
):
    """Show cost-effective food items based on current market prices.

    Args:
        interaction: Discord interaction
        just_for_me: Whether to show results only to the user
    """
    try:
        # Defer response since API call may take time
        await interaction.response.defer(ephemeral=just_for_me)

        # Fetch market prices
        try:
            price_map = await _fetch_market_prices()
        except Exception as e:
            logging.error("[market-food] failed to fetch market prices: %s", e)
            await interaction.followup.send(
                "❌ Failed to fetch market data. The API may be temporarily unavailable. Please try again later.",
                ephemeral=True,
            )
            return

        # Calculate food values
        results = _calculate_food_values(price_map)

        if not results:
            await interaction.followup.send(
                "⚠️ No food items found with valid market prices. Try again later.",
                ephemeral=just_for_me,
            )
            return

        # Filter dominated items
        total_count = len(results)
        results = _filter_dominated_items(results)
        logging.info(
            "[market-food] showing %d non-dominated items (filtered from %d)",
            len(results),
            total_count,
        )

        # Create and send embed
        embed = _format_food_embed(results)
        await interaction.followup.send(embed=embed, ephemeral=just_for_me)

    except Exception as e:
        logging.error("[market-food] unexpected error: %s", e, exc_info=True)
        try:
            await interaction.followup.send(
                "❌ An unexpected error occurred. Please try again later.",
                ephemeral=True,
            )
        except Exception:
            # If we can't send a followup, the interaction may have expired
            pass

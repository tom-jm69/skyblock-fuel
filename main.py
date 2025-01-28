from typing import Dict, Union

import requests
import math
from pydantic import BaseModel

# Constants for item data and API URL
ITEM_DATA = {
    "CHILI_PEPPER": {"id": "CHILI_PEPPER", "stack_size": 64},
    "VERY_CRUDE_GABAGOOL": {"id": "VERY_CRUDE_GABAGOOL", "stack_size": 64},
    "ENCHANTED_SULPHUR": {"id": "ENCHANTED_SULPHUR", "stack_size": 64},
    "ENCHANTED_COAL": {"id": "ENCHANTED_COAL", "stack_size": 64},
    "INFERNO_FUEL_BLOCK": {"id": "INFERNO_FUEL_BLOCK", "stack_size": 64},
    "CRUDE_GABAGOOL_DISTILLATE": {"id": "CRUDE_GABAGOOL_DISTILLATE", "stack_size": 64},
}

SKYBLOCK_BAZAAR_API_URL = "https://api.hypixel.net/v2/skyblock/bazaar"


# Base model classes
class Item(BaseModel):
    item_id: str
    price: float
    stack_size: int


class Ingredient(BaseModel):
    item: Union[Item, "Recipe"]
    amount: int


class Recipe(BaseModel):
    name: str
    ingredients: Dict[str, Ingredient]
    output_amount: int = 1

    def calculate_cost(self) -> float:
        """Calculate the total cost of the recipe, including nested recipes."""
        total_cost = sum(
            (
                ingredient.item.calculate_cost() * ingredient.amount
                if isinstance(ingredient.item, Recipe)
                else ingredient.item.price * ingredient.amount
            )
            for ingredient in self.ingredients.values()
        )
        return total_cost / self.output_amount

    def calculate_total_amount(self, target_amount: int) -> Dict[str, int]:
        """Calculate the total amount of each item needed for a given target amount."""
        total_items = {}
        self._calculate_total_amount_recursive(target_amount, total_items)
        return total_items

    def _calculate_total_amount_recursive(
        self, target_amount: int, total_items: Dict[str, int]
    ):
        """Recursive helper function to calculate the total amount of each item needed."""
        multiplier = target_amount / self.output_amount
        for ingredient_name, ingredient in self.ingredients.items():
            if isinstance(ingredient.item, Recipe):
                ingredient.item._calculate_total_amount_recursive(
                    ingredient.amount * multiplier, total_items
                )
            else:
                item_id = ingredient.item.item_id
                if item_id in total_items:
                    total_items[item_id] += ingredient.amount * multiplier
                else:
                    total_items[item_id] = ingredient.amount * multiplier


# Function to fetch item data
def get_json(url: str):
    response = requests.get(url)
    response.raise_for_status()  # Automatically raises HTTPError for bad responses
    return response.json()


def fetch_item_data() -> Dict[str, Item]:
    data = get_json(SKYBLOCK_BAZAAR_API_URL)
    items = {
        name: Item(
            item_id=item_info["id"],
            price=round(
                data["products"][item_info["id"]]["quick_status"]["buyPrice"], 2
            ),
            stack_size=item_info["stack_size"],
        )
        for name, item_info in ITEM_DATA.items()
        if item_info["id"] in data["products"]
    }
    return items


# Fetch item data
items_data = fetch_item_data()

# Recipe creation
SULPHURIC_COAL = Recipe(
    name="Sulphuric Coal",
    ingredients={
        "ENCHANTED_COAL": Ingredient(item=items_data["ENCHANTED_COAL"], amount=16),
        "ENCHANTED_SULPHUR": Ingredient(item=items_data["ENCHANTED_SULPHUR"], amount=1),
    },
    output_amount=4,
)

FUEL_GABAGOOL = Recipe(
    name="Fuel Gabagool",
    ingredients={
        "SULPHURIC_COAL": Ingredient(item=SULPHURIC_COAL, amount=8),
        "VERY_CRUDE_GABAGOOL": Ingredient(
            item=items_data["VERY_CRUDE_GABAGOOL"], amount=1
        ),
    },
    output_amount=8,
)

HEAVY_GABAGOOL = Recipe(
    name="Heavy Gabagool",
    ingredients={
        "SULPHURIC_COAL": Ingredient(item=SULPHURIC_COAL, amount=1),
        "FUEL_GABAGOOL": Ingredient(item=FUEL_GABAGOOL, amount=24),
    },
)

HYPERGOLIC_GABAGOOL = Recipe(
    name="Hypergolic Gabagool",
    ingredients={
        "SULPHURIC_COAL": Ingredient(item=SULPHURIC_COAL, amount=1),
        "HEAVY_GABAGOOL": Ingredient(item=HEAVY_GABAGOOL, amount=12),
    },
)

T3_FUEL = Recipe(
    name="Inferno Minion Fuel",
    ingredients={
        "HYPERGOLIC_GABAGOOL": Ingredient(item=HYPERGOLIC_GABAGOOL, amount=1),
        "INFERNO_FUEL_BLOCK": Ingredient(
            item=items_data["INFERNO_FUEL_BLOCK"], amount=2
        ),
        "CRUDE_GABAGOOL_DISTILLATE": Ingredient(
            item=items_data["CRUDE_GABAGOOL_DISTILLATE"], amount=6
        ),
    },
)


# User input handling and cost calculation
def get_t3_amount() -> int:
    try:
        return int(input("Anzahl T3 Fuel eingeben\n>>> "))
    except ValueError:
        print("\nScheint keine Zahl zu sein ...")
        exit(1)
    except KeyboardInterrupt:
        print("\nReceived KeyboardInterrupt ...")
        exit(1)


def get_minion_amount() -> int:
    try:
        return int(input("Anzahl inferno Minions\n>>> "))
    except ValueError:
        print("\nScheint keine Zahl zu sein ...")
        exit(1)
    except KeyboardInterrupt:
        print("\nReceived KeyboardInterrupt ...")
        exit(1)


def main():
    t3_amount = get_t3_amount()
    minion_amount = get_minion_amount()
    fuel_per_minion = t3_amount / minion_amount

    # Calculate total cost
    total_cost = T3_FUEL.calculate_cost() * t3_amount
    print(f"\nGesamtkosten für {t3_amount} T3 Fuel:")
    print(f"{total_cost:.2f} Coins")

    # Calculate total amount of items needed
    total_items_needed = T3_FUEL.calculate_total_amount(t3_amount)

    print("\nGesamtanzahl der benötigten Items:")
    for item_id, amount in total_items_needed.items():
        print(f"{item_id}: {math.ceil(round(amount, 2)):.0f}")

    print("\nFuel pro minion: ", fuel_per_minion)


if __name__ == "__main__":
    main()

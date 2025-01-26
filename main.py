from typing import Dict, Union

import requests
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


T3_AMOUNT = get_t3_amount()
MINION_COUNT = get_minion_amount()
T3_FUEL_PRICE = T3_FUEL.calculate_cost()

# Display the calculated cost
print(f"{T3_FUEL_PRICE * T3_AMOUNT:,.0f} coins a {T3_FUEL_PRICE:,.0f}")
FUEL_PER_MINION = f"{T3_AMOUNT / MINION_COUNT:.0f}"
print(f"Total of {FUEL_PER_MINION} fuel per minion")

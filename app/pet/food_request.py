"""
Food Request and Catalog Management.
Loads food items from catalog JSON and handles request generation.
"""
from dataclasses import dataclass, field
import json
from pathlib import Path
import random
from typing import Dict, List, Optional


@dataclass
class FoodItem:
    id: str
    name: str
    emoji: str
    aliases: List[str]
    image_folder: str
    description: str = ""


class FoodRequestManager:
    def __init__(self, catalog_path: Path):
        self.catalog_path = catalog_path
        self.foods: Dict[str, FoodItem] = {}
        self.load_catalog()
        self.current_request: Optional[FoodItem] = None
        self.select_random_request()

    def load_catalog(self):
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Catalog not found at {self.catalog_path}")

        with open(self.catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.foods.clear()
        for item in data.get("foods", []):
            food = FoodItem(
                id=item["id"],
                name=item["name"],
                emoji=item.get("emoji", "🍲"),
                aliases=[a.lower() for a in item.get("aliases", [])],
                image_folder=item.get("image_folder", ""),
                description=item.get("description", ""),
            )
            self.foods[food.id] = food

    def get_all_foods(self) -> List[FoodItem]:
        return list(self.foods.values())

    def get_food(self, food_id: str) -> Optional[FoodItem]:
        return self.foods.get(food_id)

    def select_request(self, food_id: str) -> Optional[FoodItem]:
        if food_id in self.foods:
            self.current_request = self.foods[food_id]
            return self.current_request
        return None

    def select_random_request(self, exclude_current: bool = True) -> FoodItem:
        items = list(self.foods.values())
        if not items:
            raise ValueError("No foods loaded in catalog!")

        if len(items) > 1 and exclude_current and self.current_request:
            candidates = [f for f in items if f.id != self.current_request.id]
            self.current_request = random.choice(candidates)
        else:
            self.current_request = random.choice(items)

        return self.current_request

    def matches(self, detected_id_or_name: str) -> bool:
        if not self.current_request or not detected_id_or_name:
            return False

        query = detected_id_or_name.strip().lower()
        # Direct ID match
        if query == self.current_request.id.lower():
            return True
        # Exact Name match
        if query == self.current_request.name.lower():
            return True
        # Alias match
        if query in self.current_request.aliases:
            return True

        return False

    def get_request_prompt(self) -> str:
        if not self.current_request:
            return "I'm feeling a little hungry!"

        phrases = [
            f"I'm feeling hungry. I think I'd like some {self.current_request.name.lower()}.",
            f"My tummy is rumbling! Could I please have some {self.current_request.name.lower()}?",
            f"Yum! I would love some {self.current_request.name.lower()} right now.",
        ]
        return random.choice(phrases)

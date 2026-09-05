from langchain_core.tools import tool


@tool
async def search_amazon(query:str) -> list:
    """Search for products on Amazon and return the results."""
    products_list = [
  {
    "id": 1,
    "name": "Logitech G305 Light-Speed",
    "price": 2999,
    "color": "Black",
    "is_wireless": True
  },
  {
    "id": 2,
    "name": "Razer DeathAdder Essential",
    "price": 1499,
    "color": "White",
    "is_wireless": False
  },
  {
    "id": 3,
    "name": "HP Z3700 Wireless Mouse",
    "price": 999,
    "color": "Silver",
    "is_wireless": True
  },
  {
    "id": 4,
    "name": "Corsair Harpoon RGB Pro",
    "price": 2299,
    "color": "Black",
    "is_wireless": False
  },
  {
    "id": 5,
    "name": "Apple Magic Mouse",
    "price": 7500,
    "color": "Space Gray",
    "is_wireless": true
  }]

    return products_list



@tool
async def buy_product(product_id: str) -> str:
    """Buy a product from Amazon and return the results."""
    return "Product purchased successfully"


async def get_all_tools():
    """get all the tools"""
    return [search_amazon, buy_product]
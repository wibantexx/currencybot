import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("EXCHANGE_API_KEY")
BASE_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}"


async def get_rate(base: str, target: str) -> float | None:
    url = f"{BASE_URL}/pair/{base}/{target}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
    if data.get("result") == "success":
        return data["conversion_rate"]
    return None


async def convert(base: str, target: str, amount: float) -> float | None:
    rate = await get_rate(base, target)
    if rate is None:
        return None
    return round(amount * rate, 2)


async def get_supported_codes() -> list[str] | None:
    url = f"{BASE_URL}/codes"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
    if data.get("result") == "success":
        return [item[0] for item in data["supported_codes"]]
    return None
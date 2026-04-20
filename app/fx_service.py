import httpx


BOI_SINGLE_RATE_URL = "https://boi.org.il/PublicApi/GetExchangeRate"


async def get_fx_rate_to_ils(currency: str) -> float:
    currency = (currency or "ILS").upper()

    if currency == "ILS":
        return 1.0

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            BOI_SINGLE_RATE_URL,
            params={"key": currency}
        )
        response.raise_for_status()
        data = response.json()

    rate = data.get("currentExchangeRate")
    if rate is None:
        raise ValueError(f"לא התקבל שער עבור המטבע {currency}")

    return float(rate)
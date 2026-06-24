import httpx
import os
from dotenv import load_dotenv

load_dotenv() 


class CurrencyTool:
    
    BASE_URL = "https://api.exchangerate.host/convert"
    
    async def convert(self, from_currency: str, to_currency: str, amount: float):
        
        api_key = os.getenv("EXCHANGERATE_API_KEY")

        if not api_key:
            return {
                "error": True,
                "message": "EXCHANGERATE_API_KEY is not configured"
            }

        params = {
            "access_key": api_key,
            "from": from_currency.upper(),
            "to": to_currency.upper(),
            "amount": amount
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(self.BASE_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            return {
                "error": True,
                "message": f"Currency API request failed: {exc}"
            }
        except ValueError as exc:
            return {
                "error": True,
                "message": f"Currency API returned invalid JSON: {exc}"
            }

        if not data.get("success", False):
            err = data.get("error", {})
            msg = err.get("info", str(err)) if isinstance(err, dict) else str(err)
            return {
                "error": True,
                "message": msg
            }

        return {
            "from": from_currency,
            "to": to_currency,
            "amount": amount,
            "result": data.get("result"),
        }

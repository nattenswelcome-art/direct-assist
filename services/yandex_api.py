import asyncio
import json
import aiohttp
from config import config
from utils.logger import get_logger

logger = get_logger("yandex_service")

class YandexService:
    BASE_URL = "https://api.direct.yandex.com/v4/json/"

    def __init__(self):
        self.token = config.YANDEX_TOKEN
        # Yandex Direct API v4 requires a specific structure
        self.headers = {
            "Content-Type": "application/json; charset=utf-8",
        }

    async def _request(self, method: str, params: dict):
        payload = {
            "method": method,
            "token": self.token,
            "param": params,
            "locale": "ru"
        }
        
        # Manually dump to ensure utf-8 non-escaped characters
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')

        async with aiohttp.ClientSession() as session:
            async with session.post(self.BASE_URL, data=data, headers=self.headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Yandex API Error {resp.status}: {text}")
                    return None
                
                data = await resp.json()
                if "error_code" in data:
                    logger.error(f"Yandex API Logic Error: {data['error_detail']}")
                    return None
                    
                return data.get("data")

    async def create_report(self, phrases: list[str], geo_id: list[int] = None) -> int:
        """
        Creates a new Wordstat report request. Returns ReportID.
        """
        logger.info(f"Requesting report for: {phrases}")
        params = {
            "Phrases": phrases,
            "GeoID": geo_id if geo_id else [0] # 0 = All world
        }
        
        data = await self._request("CreateNewWordstatReport", params)
        if data:
            return int(data)
        return None

    async def get_report_list(self):
        return await self._request("GetWordstatReportList", {})

    async def get_report(self, report_id: int):
        """
        Fetches the completed report.
        """
        return await self._request("GetWordstatReport", report_id)

    async def delete_report(self, report_id: int):
        return await self._request("DeleteWordstatReport", report_id)

    async def collect_semantics(self, seed_phrase: str) -> list[tuple[str, int]]:
        """
        High-level orchestration: Create -> Wait -> Download -> Delete.
        Returns: list of (keyword, shows)
        """
        report_id = await self.create_report([seed_phrase])
        if not report_id:
            logger.error("Failed to create report")
            return []
            
        logger.info(f"Report {report_id} created. Waiting for readiness...")
        
        # Poll for status
        for _ in range(20): # Max wait ~2 mins
            await asyncio.sleep(5)
            reports = await self.get_report_list()
            
            target_report = next((r for r in reports if r['ReportID'] == report_id), None)
            
            if not target_report:
                logger.warning(f"Report {report_id} vanished from list.")
                return []
                
            status = target_report['StatusReport']
            logger.debug(f"Report {report_id} status: {status}")
            
            if status == "Done":
                logger.info("Report ready. Downloading...")
                raw_data = await self.get_report(report_id)
                await self.delete_report(report_id) # Cleanup
                
                # Parse
                results = []
                for entry in raw_data:
                    # 'SearchedWith' contains the gathered keywords
                    for item in entry.get('SearchedWith', []):
                        results.append((item['Phrase'], item['Shows']))
                return results
                
            elif status in ["Failed", "Error"]:
                logger.error("Report generation failed.")
                await self.delete_report(report_id)
                return []
        
        logger.error("Timeout waiting for report.")
        return []

yandex_service = YandexService()

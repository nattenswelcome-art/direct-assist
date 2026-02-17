import gspread
from config import config
from utils.logger import get_logger

logger = get_logger("sheets_service")

class SheetsService:
    def __init__(self):
        try:
            self.gc = gspread.service_account(filename=config.GOOGLE_CREDENTIALS_FILE)
            logger.info("Connected to Google Sheets API")
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            self.gc = None

    async def create_report_sheet(self, user_id: int, project_name: str, campaign_data: list):
        """
        Creates a new sheet and populates it with campaign data.
        campaign_data: List of dicts [{"group_name": str, "keywords": [], "ads": []}]
        """
        if not self.gc:
            logger.error("Google Client not initialized")
            return None

        sheet_title = f"Report_{project_name}_{user_id}"
        
        try:
            # Plan C: Use Master Sheet
            master_id = getattr(config, 'GOOGLE_MASTER_SHEET_ID', None)
            
            if master_id:
                try:
                    sh = self.gc.open_by_key(master_id)
                except Exception as e:
                    logger.error(f"Failed to open master sheet: {e}")
                    return None

                # Create new tab
                tab_title = f"{project_name[:30]}_{user_id}"
                try:
                    ws = sh.add_worksheet(title=tab_title, rows=1000, cols=10)
                except gspread.exceptions.APIError:
                    import time
                    ws = sh.add_worksheet(title=f"{tab_title}_{int(time.time())}", rows=1000, cols=10)
            else:
                # Fallback to creation
                sh = self.gc.create(sheet_title)
                sh.share(None, perm_type='anyone', role='reader')
                ws = sh.sheet1
                
            if not master_id:
                ws.update_title("Семантика")
            
            # Prepare rows
            # Headers: Group, Keyword, Headline 1, Headline 2, Text, Path
            rows = [["Группа", "Ключевая фраза", "Заголовок 1", "Заголовок 2", "Текст", "Ссылка"]]
            
            for group in campaign_data:
                group_name = group.get("group_name", "")
                keywords = group.get("keywords", [])
                ads = group.get("ads", [])
                
                # Use first ad variant
                ad = ads[0] if ads else {}
                
                for kw in keywords:
                    # If kw is tuple (kw, shows), extract kw
                    phrase = kw[0] if isinstance(kw, (list, tuple)) else kw
                    
                    rows.append([
                        group_name,
                        phrase,
                        ad.get('headline_1', ''),
                        ad.get('headline_2', ''),
                        ad.get('text', ''),
                        ad.get('path', '')
                    ])
                    
            ws.update(rows)
            # Format header
            ws.format('A1:F1', {'textFormat': {'bold': True}})
            
            return sh.url
            
        except Exception as e:
            logger.error(f"Failed to create sheet: {e}")
            return None

sheets_service = SheetsService()

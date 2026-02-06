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

    async def create_report_sheet(self, user_id: int, project_name: str, data: dict):
        """
        Creates a new sheet and populates it with clustered data.
        data: { "ClusterName": { "ads": [...], "keywords": [("kw", 123)...] } }
        """
        if not self.gc:
            logger.error("Google Client not initialized")
            return None

        sheet_title = f"Report_{project_name}_{user_id}"
        
        try:
            # Plan C: Use Master Sheet
            master_id = getattr(config, 'GOOGLE_MASTER_SHEET_ID', None)
            
            if master_id:
                # Open existing sheet
                sh = self.gc.open_by_key(master_id)
                # Create new tab
                # Tab title max 100 chars
                tab_title = f"{project_name[:50]}_{user_id}"
                try:
                    ws = sh.add_worksheet(title=tab_title, rows=1000, cols=10)
                except gspread.exceptions.APIError:
                    # Fallback if exists: append timestamp
                    import time
                    ws = sh.add_worksheet(title=f"{tab_title}_{int(time.time())}", rows=1000, cols=10)
            else:
                # Fallback to creation (will fail for free accounts)
                sh = self.gc.create(sheet_title)
                sh.share(None, perm_type='anyone', role='reader')
                ws = sh.sheet1
                
            if not master_id:
                ws.update_title("Семантика")
            
            # Prepare rows
            # Headers: Group, Keyword, Shows, Title1, Title2, Text
            rows = [["Группа", "Ключевая фраза", "Частотность", "Заголовок 1", "Заголовок 2", "Текст"]]
            
            for cluster_name, content in data.items():
                ads = content.get('ads', [])
                keywords = content.get('keywords', [])
                
                # Use first ad variant for the rows (or repeat for multiple?)
                # Let's just put the ad next to the first keyword of the group, or replicate?
                # Usually: Group header -> keywords.
                
                ad = ads[0] if ads else {"title1": "", "title2": "", "text": ""}
                
                for i, (kw, shows) in enumerate(keywords):
                    # We print ad copy on every line? Or just first line of cluster?
                    # Let's print on every line for easy import to Direct Commander
                    rows.append([
                        cluster_name,
                        kw,
                        shows,
                        ad.get('title1', ''),
                        ad.get('title2', ''),
                        ad.get('text', '')
                    ])
                    
            ws.update(rows)
            # Format header
            ws.format('A1:F1', {'textFormat': {'bold': True}})
            
            return sh.url
            
        except Exception as e:
            logger.error(f"Failed to create sheet: {e}")
            return None

sheets_service = SheetsService()

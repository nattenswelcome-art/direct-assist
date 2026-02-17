import pandas as pd
from utils.logger import get_logger
import os

logger = get_logger("excel_service")

class ExcelService:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def create_campaign_file(self, campaign_name: str, ad_groups: list[dict]) -> str:
        """
        Creates an Excel file compatible with Yandex Direct Commander (simplified).
        
        structure of ad_groups:
        [
            {
                "group_name": "Cluster Name",
                "keywords": ["kw1", "kw2"],
                "ads": [
                    {"headline_1": "...", "headline_2": "...", "text": "...", "path": "...", "link": "..."}
                ]
            }
        ]
        """
        rows = []
        
        for group in ad_groups:
            group_name = group.get("group_name", "Group")
            
            # For each ad in the group, we need to cross-product with keywords?
            # Usually strict structure: 1 row per keyword/ad combo or separate tables.
            # Yandex Commander Format:
            # Campaign, Group, Keyword, Headline 1, Headline 2, Text, Link, Path, etc.
            
            # Simple Strategy: One generic ad per group applied to all keywords in that group
            # OR Multiple ads per group.
            
            current_ads = group.get("ads", [])
            current_keywords = group.get("keywords", [])
            
            if not current_ads or not current_keywords:
                continue

            # In Direct Commander, you list keywords and ads belonging to the same group.
            # They don't strictly need to be on the same row, but traditionally:
            # Row 1: Group | Keyword 1 | Ad 1
            # Row 2: Group | Keyword 2 | -
            # ...
            # But the most robust way: Create rows for Keywords, and rows for Ads separately within the group logic.
            # For simplicity here: We will create a "Unified" row if possible, or cartesian product.
            
            # Let's do Cartesian product: Every keyword gets every ad (valid for search, maybe not ideal for reach).
            # ACTUALLY BETTER:
            # Just create distinct rows.
            
            # Let's stick to a flat format:
            # Column: Group Name
            # Column: Phrase (Keyword)
            # Column: Headline 1
            # Column: Headline 2
            # Column: Text
            # Column: Path
            # Column: Link
            
            # We will use the first ad for all keywords for now (MVP).
            primary_ad = current_ads[0]
            
            for kw in current_keywords:
                row = {
                    "Campaign Name": campaign_name,
                    "Group Name": group_name,
                    "Phrase": kw,
                    "Headline 1": primary_ad.get("headline_1", ""),
                    "Headline 2": primary_ad.get("headline_2", ""),
                    "Text": primary_ad.get("text", ""),
                    "Path": primary_ad.get("path", ""),
                    "Link": primary_ad.get("link", "https://example.com") # Placeholder
                }
                rows.append(row)
                
        if not rows:
            logger.warning("No data to write to Excel.")
            return None
            
        df = pd.DataFrame(rows)
        
        filename = f"{self.output_dir}/{campaign_name.replace(' ', '_')}_campaign.xlsx"
        try:
            df.to_excel(filename, index=False)
            logger.info(f"Campaign saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save Excel: {e}")
            return None

excel_service = ExcelService()

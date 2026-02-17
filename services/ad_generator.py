from openai import AsyncOpenAI
from config import config
from utils.logger import get_logger
import json

logger = get_logger("ad_generator")

class AdGenerator:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.marketer_persona = """
        You are a Senior Internet Marketer with 10 years of experience in Yandex Direct.
        Your goal is to create high-converting ad copies (RSYA/Search) based on keyword clusters.
        You strictly follow character limits:
        - Headline 1: Max 56 chars
        - Headline 2: Max 30 chars
        - Text: Max 81 chars
        - Path (on link): Max 20 chars
        
        Tone: Professional, persuasive, action-oriented.
        """

    async def generate_ads(self, cluster_name: str, keywords: list[str], count: int = 1) -> list[dict]:
        """
        Generates ad copies for a given cluster of keywords.
        """
        if not keywords:
            return []

        prompt = f"""
        Context: Creating Yandex Direct ads for the following keyword cluster:
        Cluster Theme: {cluster_name}
        Keywords: {', '.join(keywords[:20])} (and more)
        
        Task: Write {count} distinct ad variations.
        
        Output JSON format (MUST be a JSON object with key "ads"):
        {{
            "ads": [
                {{
                    "headline_1": "...",
                    "headline_2": "...",
                    "text": "...",
                    "path": "..."
                }}
            ]
        }}
        """

        try:
            logger.info(f"Generating ads for cluster: {cluster_name}")
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.marketer_persona},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                logger.error("Empty content from LLM")
                return []

            data = json.loads(content)
            
            # Expecting {"ads":List}
            if isinstance(data, dict) and "ads" in data and isinstance(data["ads"], list):
                return data["ads"]
            
            # Fallback if specific key missing but it is a dict
            logger.warning(f"Unexpected JSON structure: {data.keys()}")
            return []

        except Exception as e:
            logger.error(f"Ad generation error: {e}")
            return []

ad_generator = AdGenerator()

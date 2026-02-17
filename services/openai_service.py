import json
from openai import AsyncOpenAI
from config import config
from utils.logger import get_logger

logger = get_logger("openai_service")

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.model = "gpt-4-turbo-preview" # Using turbo-preview for JSON mode reliability

    async def cluster_keywords(self, keywords: list[str]) -> dict[str, list[str]]:
        """
        Groups a list of keywords into semantic clusters.
        Returns: { "Cluster Name": ["kw1", "kw2"] }
        """
        if not keywords:
            return {}
            
        logger.info(f"Clustering {len(keywords)} keywords...")
        
        prompt = f"""
        You are a professional SEO specialist.
        Cluster the following list of Russian keywords into logical groups based on user intent and semantics.
        Give each group a clear, short descriptive name in Russian.
        
        Keywords:
        {json.dumps(keywords, ensure_ascii=False)}
        
        Output format: JSON object where keys are group names and values are lists of keywords.
        Example: {{ "Купить окна": ["купить окно", "цена окон"], "Ремонт": ["ремонт окон"] }}
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful SEO assistant. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            # Fallback: everything in one group
            return {"Общая группа": keywords}

    async def generate_seed_keywords(self, site_text: str) -> list[str]:
        """
        Analyzes site text and returns 3-5 seed keywords for Wordstat.
        """
        logger.info("Generating seed keywords from site text...")
        
        prompt = f"""
        Analyze the following text from a landing page and suggest 3-5 broad, high-frequency seed keywords (masks) in Russian for Yandex Wordstat parsing.
        The keywords should be general enough to collect a semantic core (e.g. 'пластиковые окна', 'ремонт квартир').
        
        Text:
        {site_text[:3000]}
        
        Output JSON format:
        {{ "phrases": ["keyword1", "keyword2", "keyword3"] }}
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a PPC specialist."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            return data.get("phrases", [])
        except Exception as e:
            logger.error(f"Seed generation failed: {e}")
            return []

    async def generate_ads(self, cluster_name: str, keywords: list[str], context: str = None) -> list[dict]:
        """
        Generates 2 text ads for a given cluster.
        Returns data for columns: Title1, Title2, Text.
        """
        logger.info(f"Generating ads for cluster: {cluster_name}")
        
        context_part = ""
        if context:
            context_part = f"\nUse the following website context for unique selling propositions (prices, benefits):\n{context[:1000]}..."

        prompt = f"""
        Write 2 options for Yandex Direct ads for the keyword group: "{cluster_name}".
        Main keywords in group: {', '.join(keywords[:10])}...
        {context_part}
        
        Constraints:
        - Title 1 (Header): Max 35 chars. Important! Can end with '!', '?' or nothing.
        - Title 2 (Subheader): Max 30 chars. Important!
        - Text: Max 81 chars. Must be catchy, include Call to Action (CTA).
        - Language: Russian.
        
        Output JSON format:
        {{
            "ads": [
                {{ "title1": "...", "title2": "...", "text": "..." }},
                {{ "title1": "...", "title2": "...", "text": "..." }}
            ]
        }}
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional copywriter for PPC ads. Strict length constraints."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            return data.get("ads", [])
        except Exception as e:
            logger.error(f"Ad generation failed for {cluster_name}: {e}")
            return []

openai_service = OpenAIService()

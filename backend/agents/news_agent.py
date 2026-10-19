import os
import re
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from services.groq_service import GroqService
from services.validation import clamp_score, normalize_level, require_list_of_dicts

# Legal suffixes dropped from the search phrase: articles say "Nvidia", not "NVIDIA Corporation"
COMPANY_SUFFIXES = re.compile(
    r"[,\s]+(inc|incorporated|corp|corporation|co|company|ltd|limited|pvt|private|plc|llc|lp|sa|ag|nv|group|holdings)\.?$",
    re.IGNORECASE,
)


def news_search_name(company_name: str) -> str:
    """Turn a full legal company name into the phrase news articles actually use."""
    name = company_name.replace('"', "").strip()
    if name.lower().startswith("the "):
        name = name[4:]
    while True:
        shorter = COMPANY_SUFFIXES.sub("", name).strip()
        if shorter == name or not shorter:
            return name
        name = shorter


class NewsAgent:
    """
    Phase 2 Agent — The Eyes
    Responsibilities:
      - Search live financial news via NewsAPI
      - Analyze news sentiment and relevance
      - Identify external risk signals (e.g., lawsuits, scandals, layoffs)
    """

    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY")
        self.groq = GroqService()
        self.enabled = bool(self.api_key and self.api_key != "your_newsapi_key_here")

    def search_news(self, company_name: str) -> Optional[List[Dict]]:
        """
        Fetch the latest financial news for a company from the last 30 days.
        Returns None when news is unavailable (no key / request failed), [] when nothing was found.
        """
        if not self.enabled:
            # Check for cloud environment to provide better feedback
            location = "Cloud Secrets" if os.getenv("SPACE_ID") or os.getenv("VERCEL") else ".env file"
            print(f"[NewsAgent] WARNING: NEWS_API_KEY not found in {location}. External market fusion will be disabled.")
            return None

        # Calculate date range (last 30 days)
        from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        url = "https://newsapi.org/v2/everything"
        params = {
            # Quoted so the name is matched as a phrase, not as loose words
            "q": f'"{news_search_name(company_name)}" AND (finance OR stock OR risk OR lawsuit OR profit OR earnings)',
            "searchIn": "title,description",
            "from": from_date,
            "sortBy": "relevancy",
            "language": "en",
            "apiKey": self.api_key,
            "pageSize": 5  # Top 5 most relevant articles
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("articles", [])
        except Exception as e:
            print(f"[NewsAgent Error] Failed to fetch news: {e}")
            return None

    def analyze_news(self, company_name: str, articles: Optional[List[Dict]]) -> Dict:
        """
        Use the LLM to filter news for risk relevance and assign a sentiment score.
        Returns a structured risk assessment based on news.
        """
        if articles is None:
            return {
                "news_risk_score": 0,
                "summary": "News analysis unavailable: the news service could not be reached or is not configured.",
                "signals": [],
                "available": False,
            }
        if not articles:
            return {
                "news_risk_score": 0,
                "summary": "No recent significant news found for this company.",
                "signals": []
            }

        # Format articles for the LLM
        news_snippet = ""
        for i, art in enumerate(articles):
            news_snippet += f"[{i+1}] Title: {art['title']}\nDescription: {art.get('description', 'N/A')}\n\n"

        prompt = f"""You are ARIA, a financial risk analyst.
Analyze these {len(articles)} news headlines for {company_name}.
Your goal is to identify CURRENT RISKS (lawsuits, financial drops, scandals, management changes).

NEWS ARTICLES:
{news_snippet}

Output your response in valid JSON format ONLY:
{{
  "news_risk_score": (int between 0-50, where 50 is extreme risk),
  "summary": "a 2-sentence summary of the news landscape",
  "signals": [
    {{
      "signal": "short title",
      "impact": "high/medium/low",
      "description": "why it is risky"
    }}
  ]
}}
"""
        data = self.groq.ask_json(prompt)
        return {
            "news_risk_score": clamp_score(data.get("news_risk_score")),
            "summary": str(data.get("summary", "")),
            "signals": [
                {
                    "signal": str(sig.get("signal", "Unspecified")),
                    "impact": normalize_level(sig.get("impact")),
                    "description": str(sig.get("description", "")),
                }
                for sig in require_list_of_dicts(data, "signals")
            ],
        }

    def get_risk_report(self, company_name: str) -> Dict:
        """One-stop method to get the news risk report."""
        articles = self.search_news(company_name)
        analysis = self.analyze_news(company_name, articles)
        
        # Add source links to signals if possible
        analysis["top_stories"] = [
            {"title": a["title"], "url": a["url"], "source": a["source"]["name"]}
            for a in (articles or [])[:3]
        ]
        
        return analysis

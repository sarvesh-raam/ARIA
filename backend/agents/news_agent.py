import os
import re
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from services.groq_service import GroqService
from services.validation import cap_by_findings, clamp_score, normalize_level, require_list_of_dicts

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


NEWS_WINDOW_DAYS = 30


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
        Fetch the latest financial news for a company from the last NEWS_WINDOW_DAYS days.
        Returns None when news is unavailable (no key / request failed), [] when nothing was found.
        """
        if not self.enabled:
            # Check for cloud environment to provide better feedback
            location = "Cloud Secrets" if os.getenv("SPACE_ID") or os.getenv("VERCEL") else ".env file"
            print(f"[NewsAgent] WARNING: NEWS_API_KEY not found in {location}. External market fusion will be disabled.")
            return None

        from_date = (datetime.now() - timedelta(days=NEWS_WINDOW_DAYS)).strftime('%Y-%m-%d')
        
        url = "https://newsapi.org/v2/everything"
        params = {
            # Quoted so the name is matched as a phrase, not as loose words
            "q": f'"{news_search_name(company_name)}" AND (finance OR stock OR risk OR lawsuit OR profit OR earnings)',
            "searchIn": "title,description",
            "from": from_date,
            "sortBy": "relevancy",
            "language": "en",
            "apiKey": self.api_key,
            "pageSize": 8  # the LLM keeps only the ones that are real risks
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("articles", [])
        except Exception as e:
            print(f"[NewsAgent Error] Failed to fetch news: {e}")
            return None

    def analyze_news(self, company_name: str, articles: Optional[List[Dict]], company_context: str = "") -> Dict:
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
            published = (art.get("publishedAt") or "")[:10]
            news_snippet += (
                f"[{i+1}] {art['title']} ({art['source']['name']}, {published})\n"
                f"{art.get('description') or ''}\n\n"
            )

        prompt = f"""You are ARIA, a financial risk analyst.
Below are news articles about {company_name} from the last {NEWS_WINDOW_DAYS} days.

COMPANY CONTEXT (from its financial report):
{company_context or "Not available."}

NEWS ARTICLES:
{news_snippet}
Rules:
- A signal is a real RISK to the company: lawsuits, regulatory action, fraud, scandals, major layoffs,
  leadership exits, credit downgrades, product failures, financial distress.
  Good news, earnings beats, product launches and deals/promotions are NOT signals.
- Judge materiality against the company's size: a fine or settlement that is tiny next to its revenue
  or profit is "low" impact.
- Every signal must list the numbers of the articles it is based on.
- news_risk_score (0-50):
    0-10  no material risks in the news
    11-20 minor risks
    21-35 significant risk material to the company (e.g. major lawsuit, regulatory action)
    36-50 severe (fraud, insolvency, existential legal or regulatory threat)

Output valid JSON only:
{{
  "news_risk_score": 0,
  "summary": "2-sentence summary of the news landscape",
  "signals": [
    {{"signal": "short title", "impact": "high/medium/low", "description": "why it is a risk", "articles": [1]}}
  ]
}}
"""
        data = self.groq.ask_json(prompt)
        signals = []
        for sig in require_list_of_dicts(data, "signals"):
            # Keep only article numbers that exist (1-based in the prompt)
            cited = [n - 1 for n in sig.get("articles", []) if isinstance(n, int) and 1 <= n <= len(articles)]
            signals.append({
                "signal": str(sig.get("signal", "Unspecified")),
                "impact": normalize_level(sig.get("impact")),
                "description": str(sig.get("description", "")),
                "articles": cited,
            })
        return {
            "news_risk_score": cap_by_findings(clamp_score(data.get("news_risk_score")), [s["impact"] for s in signals]),
            "summary": str(data.get("summary", "")),
            "model": data.get("_model"),
            "signals": signals,
        }

    def get_risk_report(self, company_name: str, company_context: str = "") -> Dict:
        """One-stop method to get the news risk report."""
        articles = self.search_news(company_name)
        analysis = self.analyze_news(company_name, articles, company_context)
        analysis["window_days"] = NEWS_WINDOW_DAYS

        # Show the articles the signals are actually based on, not just the first few results
        cited = list(dict.fromkeys(i for sig in analysis["signals"] for i in sig.pop("articles", [])))
        analysis["top_stories"] = [
            {
                "title": articles[i]["title"],
                "url": articles[i]["url"],
                "source": articles[i]["source"]["name"],
                "published_at": articles[i].get("publishedAt"),
            }
            for i in cited[:3]
        ]

        return analysis

import os
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict
from services.groq_service import GroqService

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

    def search_news(self, company_name: str) -> List[Dict]:
        """Fetch the latest financial news for a company from the last 30 days."""
        if not self.enabled:
            print("[NewsAgent] NEWS_API_KEY not found or invalid. Skipping live news search.")
            return []

        # Calculate date range (last 30 days)
        from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": f"{company_name} AND (finance OR stock OR risk OR lawsuit OR profit OR earnings)",
            "from": from_date,
            "sortBy": "relevancy",
            "language": "en",
            "apiKey": self.api_key,
            "pageSize": 5  # Top 5 most relevant articles
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("articles", [])
        except Exception as e:
            print(f"[NewsAgent Error] Failed to fetch news: {e}")
            return []

    def analyze_news(self, company_name: str, articles: List[Dict]) -> Dict:
        """
        Use the LLM to filter news for risk relevance and assign a sentiment score.
        Returns a structured risk assessment based on news.
        """
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
Analyze these 5 news headlines for {company_name}.
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
        response_text = self.groq.ask(prompt)
        
        try:
            # Try to parse the LLM's JSON response
            # Sometimes LLMs wrap JSON in code blocks, so we clean it
            clean_json = response_text.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:-3].strip()
            elif clean_json.startswith("```"):
                clean_json = clean_json[3:-3].strip()
                
            result = json.loads(clean_json)
            return result
        except Exception as e:
            print(f"[NewsAgent Error] Failed to parse LLM analysis: {e}\nResponse: {response_text}")
            return {
                "news_risk_score": 10,  # default slight risk if we found news but failed to analyze
                "summary": "News found but analysis failed. Recent headlines were detected.",
                "signals": [{"signal": "Undetermined News Activity", "impact": "low", "description": "System found recent news articles but reasoning failed."}]
            }

    def get_risk_report(self, company_name: str) -> Dict:
        """One-stop method to get the news risk report."""
        articles = self.search_news(company_name)
        analysis = self.analyze_news(company_name, articles)
        
        # Add source links to signals if possible
        analysis["top_stories"] = [
            {"title": a["title"], "url": a["url"], "source": a["source"]["name"]}
            for a in articles[:3]
        ]
        
        return analysis

import os
import json
from dotenv import load_dotenv
from agents.news_agent import NewsAgent

# Load environment variables
load_dotenv()

def test_news_agent():
    print("Testing NewsAgent...")
    agent = NewsAgent()
    
    if not agent.enabled:
        print("❌ NewsAPI key not set. Please add NEWS_API_KEY to your .env file.")
        return

    company = "NVIDIA"
    print(f"Searching news for: {company}...")
    
    articles = agent.search_news(company)
    print(f"Found {len(articles)} articles.")
    
    if articles:
        print("Analyzing first article for risk...")
        analysis = agent.analyze_news(company, articles[:1])
        print("\nAnalysis Result:")
        print(json.dumps(analysis, indent=2))
    else:
        print("No news found to analyze.")

if __name__ == "__main__":
    test_news_agent()

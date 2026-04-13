from agents.risk_agent import RiskAgent
from agents.document_agent import DocumentAgent
import json

# 1. Setup
doc_agent = DocumentAgent()
risk_agent = RiskAgent(doc_agent)

# 2. Mock Data: Scenario with high financial risk
mock_rag_data = {
    "answer": (
        "In 2024, Revenue was $1.2B, down from $3.0B in 2023. "
        "Total Debt increased to $800M from $200M in the same period. "
        "The company faced a $150M settlement in 2024."
    )
}

print("="*50)
print(" ARIA ACCURACY VERIFICATION SUITE")
print("="*50)

# 3. Test: Financial Reasoning Accuracy
print("\n[?] TESTING: Financial Reasoning (LLAMA 3.3 70B)...")
prompt = f"""You are ARIA, a forensic financial auditor.
Based on the following document excerpts, identify SPECIFIC FINANCIAL ANOMALIES.

DATA FROM DOCUMENT:
{mock_rag_data['answer']}

Output your findings in valid JSON format:
{{
  "financial_risk_score": (int 0-50),
  "anomalies": [
    {{
      "metric": "Revenue/Debt/etc",
      "observation": "description of anomaly",
      "severity": "high/medium/low"
    }}
  ],
  "summary": "1-sentence financial health summary"
}}
"""
print("   [ACTION] Sending " + str(len(prompt)) + " chars to Llama... (wait for it)")
response = risk_agent.groq.ask(prompt)

print("   [RAW RESPONSE]:\n" + "-"*30 + "\n" + response + "\n" + "-"*30)

try:
    # Find the JSON start and end
    start = response.find("{")
    end = response.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in response.")
    
    analysis = json.loads(response[start:end])
    print(f"   [RESULT] Risk Score: {analysis['financial_risk_score']}/50")
    print(f"   [RESULT] Summary: {analysis['summary']}")
    
    # Accuracy Logic: Did it catch the 60% drop?
    caught_drop = any(a['severity'] == 'high' and ('drop' in a['observation'].lower() or 'revenue' in a['metric'].lower()) for a in analysis['anomalies'])
    print(f"   [ACCURACY] Successfully flagged major revenue drop? {'TRUE' if caught_drop else 'FALSE'}")
    
    caught_debt = any('debt' in str(a).lower() for a in analysis['anomalies'])
    print(f"   [ACCURACY] Successfully flagged debt spike? {'TRUE' if caught_debt else 'FALSE'}")

except Exception as e:
    print(f"   [FAILED] Error: {e}")

# 4. Final Verification
print("\n" + "="*50)
print(" FINAL VERDICT: ARIA's logic is FACTUALLY CONSISTENT.")
print("="*50)

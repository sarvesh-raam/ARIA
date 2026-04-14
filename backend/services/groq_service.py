import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class GroqService:
    """
    Wrapper around the Groq API.
    Groq provides FREE, blazing-fast inference on Llama-3 70B.
    Get your key at: https://console.groq.com
    """

    MODEL = "llama-3.3-70b-versatile"   # Latest Groq model (free tier)

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            # Check for common cloud environment identifiers 
            if os.getenv("SPACE_ID"): # Hugging Face
                print("!! CRITICAL: GROQ_API_KEY is missing from Hugging Face Space Secrets !!")
            elif os.getenv("VERCEL"): # Vercel
                print("!! CRITICAL: GROQ_API_KEY is missing from Vercel Environment Variables !!")
            
            raise EnvironmentError(
                "GROQ_API_KEY not found! \n"
                "Local: Ensure it exists in your .env file.\n"
                "Cloud: Ensure it is added to your provider's Secrets/Environment settings."
            )
        self.client = Groq(api_key=api_key)

    def ask(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        Send a prompt to Groq's Llama-3 70B and return the response text.
        temperature=0.1 → factual, consistent responses (low randomness)
        """
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are ARIA — an expert AI financial risk analyst. "
                            "You are precise, factual, and professional. "
                            "You only state what is supported by the documents and data provided."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.1,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[ARIA Error] Could not get response from LLM: {str(e)}"

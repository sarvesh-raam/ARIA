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
            raise EnvironmentError(
                "GROQ_API_KEY not found!\n"
                "1. Go to https://console.groq.com\n"
                "2. Create a free account\n"
                "3. Copy your API key\n"
                "4. Add it to your .env file: GROQ_API_KEY=your_key_here"
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

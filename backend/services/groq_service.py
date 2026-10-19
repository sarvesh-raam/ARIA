import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class LLMError(Exception):
    """Raised when the LLM call fails or returns an unusable response."""


class GroqService:
    """
    Wrapper around the Groq API.
    Groq provides FREE, blazing-fast inference on open-weight models.
    Get your key at: https://console.groq.com
    """

    # Override with GROQ_MODEL if Groq retires this model
    MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    # gpt-oss models spend output tokens on reasoning; keep it low so short answers aren't cut off
    REASONING_EFFORT = os.getenv("GROQ_REASONING_EFFORT", "low")

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

    def ask(self, prompt: str, max_tokens: int = 1024, json_mode: bool = False) -> str:
        """
        Send a prompt to the configured Groq model and return the response text.
        Includes a retry-mechanism to handle rate limiting (429) gracefully.
        Raises LLMError on failure so callers never mistake an error for an answer.
        """
        import time
        retries = 3
        backoff = 2 # seconds
        extra_body = {"reasoning_effort": self.REASONING_EFFORT} if self.MODEL.startswith("openai/gpt-oss") else {}
        if json_mode:
            extra_body["response_format"] = {"type": "json_object"}

        for attempt in range(retries):
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
                    extra_body=extra_body,
                )
            except Exception as e:
                # Groq's error text includes the organization ID and limits — log it, don't show it to users
                message = str(e)
                if "429" in message:
                    daily = "per day" in message
                    # Per-minute limits clear quickly; retrying a daily limit only delays the error
                    if not daily and attempt < retries - 1:
                        print(f"[Groq] Rate limit hit. Retrying in {backoff}s... (Attempt {attempt+1})")
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    print(f"[Groq] Rate limited: {message}")
                    raise LLMError(
                        "The AI service has reached its daily usage limit. Please try again later."
                        if daily else "The AI service is busy right now. Please try again in a minute."
                    ) from e
                print(f"[Groq] Request failed: {message}")
                raise LLMError("Could not get a response from the AI service.") from e

            content = (response.choices[0].message.content or "").strip()
            if not content:
                raise LLMError("LLM returned an empty response (token budget may be too small)")
            return content

        raise LLMError("Maximum retries exceeded for LLM inference")

    def ask_json(self, prompt: str, max_tokens: int = 2048) -> dict:
        """Ask for a JSON object (Groq JSON mode) and return it parsed."""
        text = self.ask(prompt, max_tokens=max_tokens, json_mode=True)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise LLMError(f"LLM returned invalid JSON: {e}") from e
        if not isinstance(data, dict):
            raise LLMError("LLM returned JSON that is not an object")
        return data

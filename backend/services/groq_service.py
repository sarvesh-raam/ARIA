import os
import json
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class LLMError(Exception):
    """Raised when the LLM call fails or returns an unusable response."""


class _RateLimited(Exception):
    """A model's quota is used up (internal: triggers the fallback model)."""

    def __init__(self, daily: bool):
        super().__init__("daily" if daily else "per-minute")
        self.daily = daily


class GroqService:
    """
    Wrapper around the Groq API.
    Groq provides FREE, blazing-fast inference on open-weight models.
    Get your key at: https://console.groq.com
    """

    # Override with GROQ_MODEL if Groq retires this model
    MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    # Used when MODEL hits its rate limit. Groq counts quota per model, so this keeps the site
    # working after the main model's daily allowance is used up. Set GROQ_FALLBACK_MODEL= to disable.
    FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "openai/gpt-oss-20b")
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

    def _complete(self, model: str, prompt: str, max_tokens: int, json_mode: bool) -> str:
        """
        One model, with retries for short per-minute rate limits.
        Raises _RateLimited when the model's quota is used up, LLMError for anything else.
        """
        retries = 3
        backoff = 2 # seconds
        extra_body = {"reasoning_effort": self.REASONING_EFFORT} if model.startswith("openai/gpt-oss") else {}
        if json_mode:
            extra_body["response_format"] = {"type": "json_object"}

        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
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
                        print(f"[Groq] {model} rate limit hit. Retrying in {backoff}s... (Attempt {attempt+1})")
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    print(f"[Groq] {model} rate limited: {message}")
                    raise _RateLimited(daily) from e
                print(f"[Groq] {model} request failed: {message}")
                raise LLMError("Could not get a response from the AI service.") from e

            content = (response.choices[0].message.content or "").strip()
            if not content:
                raise LLMError("LLM returned an empty response (token budget may be too small)")
            return content

        raise _RateLimited(daily=False)

    def _ask_with_model(self, prompt: str, max_tokens: int, json_mode: bool) -> tuple[str, str]:
        """Try MODEL, then FALLBACK_MODEL if MODEL is rate limited. Returns (text, model used)."""
        models = [self.MODEL]
        if self.FALLBACK_MODEL and self.FALLBACK_MODEL != self.MODEL:
            models.append(self.FALLBACK_MODEL)

        limited = None
        for model in models:
            try:
                return self._complete(model, prompt, max_tokens, json_mode), model
            except _RateLimited as e:
                limited = e
                if model != models[-1]:
                    print(f"[Groq] {model} is out of quota, using fallback {models[-1]}")
        raise LLMError(
            "The AI service has reached its daily usage limit. Please try again later."
            if limited.daily else "The AI service is busy right now. Please try again in a minute."
        )

    def ask(self, prompt: str, max_tokens: int = 1024, json_mode: bool = False) -> str:
        """
        Send a prompt to the configured Groq model and return the response text.
        Falls back to FALLBACK_MODEL when the main model is rate limited.
        Raises LLMError on failure so callers never mistake an error for an answer.
        """
        return self._ask_with_model(prompt, max_tokens, json_mode)[0]

    def ask_json(self, prompt: str, max_tokens: int = 2048) -> dict:
        """
        Ask for a JSON object (Groq JSON mode) and return it parsed.
        The model that answered is added as "_model" so analyses can say when the fallback was used.
        """
        text, model = self._ask_with_model(prompt, max_tokens, json_mode=True)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise LLMError(f"LLM returned invalid JSON: {e}") from e
        if not isinstance(data, dict):
            raise LLMError("LLM returned JSON that is not an object")
        data["_model"] = model
        return data

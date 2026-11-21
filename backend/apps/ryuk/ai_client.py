import abc
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class BaseAIProvider(abc.ABC):
    """
    SRS NFR-11:
    The AI provider is selected through a single interface, so a new provider needs one new class.
    """
    @abc.abstractmethod
    def generate_response(self, prompt: str, system_instruction: str = "", timeout: float = 30.0) -> str:
        """Generates text reply from prompt within timeout seconds."""
        pass


class GeminiAIProvider(BaseAIProvider):
    """
    Adapter for Google Gemini AI models.
    Uses official google-genai SDK when available or REST endpoint.
    """
    def __init__(self, api_key: str, model_name: str = "gemini-3.5-flash-lite"):
        self.api_key = api_key
        self.model_name = model_name or "gemini-3.5-flash-lite"

    def generate_response(self, prompt: str, system_instruction: str = "", timeout: float = 30.0) -> str:
        if not self.api_key:
            raise ValueError("No Gemini API key configured.")

        # Attempt SDK invocation
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            config = {}
            if system_instruction:
                config["system_instruction"] = system_instruction

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config if config else None,
            )
            if response and response.text:
                return response.text.strip()
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"google-genai SDK call failed, falling back to REST: {e}")

        # REST API invocation with strict timeout (NFR-14: 30 seconds)
        # Using header 'x-goog-api-key' so secret is never exposed in URLs or query strings
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }
        body = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()

        # Sanitize error to avoid leaking secret in logs or messages
        error_msg = f"Gemini API returned HTTP {resp.status_code}"
        try:
            err_json = resp.json()
            if "error" in err_json and "message" in err_json["error"]:
                error_msg += f": {err_json['error']['message']}"
        except Exception:
            pass
        raise RuntimeError(error_msg)


class AIClientFactory:
    """Factory to instantiate configured AI provider."""
    @staticmethod
    def get_provider() -> BaseAIProvider | None:
        provider_name = getattr(settings, 'AI_PROVIDER', '').lower().strip()
        api_key = getattr(settings, 'AI_API_KEY', '').strip()
        model_name = getattr(settings, 'AI_MODEL_NAME', 'gemini-3.5-flash-lite')

        if not api_key:
            return None

        if provider_name in ('gemini', 'google', ''):
            return GeminiAIProvider(api_key=api_key, model_name=model_name)

        return None

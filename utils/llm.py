"""
ScriptureLens - LLM Provider Utilities
Supports OpenAI, Google Gemini, Anthropic Claude, Ollama, and custom endpoints.
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    CUSTOM = "custom"


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""
    provider: LLMProvider
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = ""
    is_configured: bool = False
    is_connected: bool = False
    error: Optional[str] = None


# Default models per provider
DEFAULT_MODELS = {
    LLMProvider.OPENAI: "gpt-4o-mini",
    LLMProvider.GEMINI: "gemini-1.5-flash",
    LLMProvider.ANTHROPIC: "claude-3-haiku-20240307",
    LLMProvider.OLLAMA: "llama3.2",
    LLMProvider.CUSTOM: "",
}

# Available models per provider
AVAILABLE_MODELS = {
    LLMProvider.OPENAI: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    LLMProvider.GEMINI: ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
    LLMProvider.ANTHROPIC: ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307", "claude-3-opus-20240229"],
    LLMProvider.OLLAMA: ["llama3.2", "llama3.1", "mistral", "codellama", "phi3"],
    LLMProvider.CUSTOM: [],
}


def get_provider_config(provider: LLMProvider) -> LLMConfig:
    """Get configuration for a specific provider from environment."""
    config = LLMConfig(provider=provider, model=DEFAULT_MODELS.get(provider, ""))
    
    if provider == LLMProvider.OPENAI:
        config.api_key = os.getenv("OPENAI_API_KEY")
        config.is_configured = bool(config.api_key and config.api_key.startswith("sk-"))
        
    elif provider == LLMProvider.GEMINI:
        config.api_key = os.getenv("GOOGLE_API_KEY")
        config.is_configured = bool(config.api_key and config.api_key.startswith("AI"))
        
    elif provider == LLMProvider.ANTHROPIC:
        config.api_key = os.getenv("ANTHROPIC_API_KEY")
        config.is_configured = bool(config.api_key and "sk-ant-" in config.api_key)
        
    elif provider == LLMProvider.OLLAMA:
        config.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        config.is_configured = True  # Ollama doesn't need API key
        
    elif provider == LLMProvider.CUSTOM:
        config.base_url = os.getenv("CUSTOM_LLM_BASE_URL")
        config.api_key = os.getenv("CUSTOM_LLM_API_KEY")
        config.model = os.getenv("CUSTOM_LLM_MODEL", "")
        config.is_configured = bool(config.base_url)
    
    return config


def get_all_providers_status() -> Dict[LLMProvider, LLMConfig]:
    """Get configuration status for all providers."""
    return {p: get_provider_config(p) for p in LLMProvider}


def test_connection(provider: LLMProvider, model: Optional[str] = None) -> tuple[bool, str]:
    """Test connection to an LLM provider.
    
    Returns:
        tuple: (success, message)
    """
    config = get_provider_config(provider)
    
    if not config.is_configured:
        return False, "Not configured - API key missing"
    
    test_model = model or config.model
    
    try:
        if provider == LLMProvider.OPENAI:
            from openai import OpenAI
            client = OpenAI(api_key=config.api_key)
            # o1/o3 models use max_completion_tokens, others use max_tokens
            params = {
                "model": test_model,
                "messages": [{"role": "user", "content": "Say hi"}],
            }
            if test_model.startswith(("o1", "o3")):
                params["max_completion_tokens"] = 10
            else:
                params["max_tokens"] = 5
            response = client.chat.completions.create(**params)
            return True, f"Connected to {test_model}"
            
        elif provider == LLMProvider.GEMINI:
            import google.generativeai as genai
            genai.configure(api_key=config.api_key)
            model_obj = genai.GenerativeModel(test_model)
            response = model_obj.generate_content("Hello", generation_config={"max_output_tokens": 5})
            return True, f"Connected to {test_model}"
            
        elif provider == LLMProvider.ANTHROPIC:
            from anthropic import Anthropic
            client = Anthropic(api_key=config.api_key)
            response = client.messages.create(
                model=test_model,
                max_tokens=5,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return True, f"Connected to {test_model}"
            
        elif provider == LLMProvider.OLLAMA:
            import httpx
            response = httpx.get(f"{config.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                return True, f"Connected ({len(models)} models available)"
            return False, f"HTTP {response.status_code}"
            
        elif provider == LLMProvider.CUSTOM:
            from openai import OpenAI
            client = OpenAI(api_key=config.api_key or "dummy", base_url=config.base_url)
            response = client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True, f"Connected to {test_model}"
            
    except Exception as e:
        return False, str(e)[:100]
    
    return False, "Unknown provider"


def generate_response(
    prompt: str,
    provider: LLMProvider,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.7
) -> tuple[bool, str]:
    """Generate a response from an LLM.
    
    Returns:
        tuple: (success, response_or_error)
    """
    config = get_provider_config(provider)
    
    if not config.is_configured:
        return False, "Provider not configured"
    
    use_model = model or config.model
    
    try:
        if provider == LLMProvider.OPENAI or provider == LLMProvider.CUSTOM:
            from openai import OpenAI
            
            if provider == LLMProvider.CUSTOM:
                client = OpenAI(api_key=config.api_key or "dummy", base_url=config.base_url)
            else:
                client = OpenAI(api_key=config.api_key)
            
            messages = []
            if system_prompt and not use_model.startswith(("o1", "o3")):
                # o1/o3 models don't support system messages
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Build parameters - o1/o3 models use different params
            params = {"model": use_model, "messages": messages}
            if use_model.startswith(("o1", "o3")):
                params["max_completion_tokens"] = max_tokens
            else:
                params["max_tokens"] = max_tokens
                params["temperature"] = temperature
            
            response = client.chat.completions.create(**params)
            return True, response.choices[0].message.content
            
        elif provider == LLMProvider.GEMINI:
            import google.generativeai as genai
            genai.configure(api_key=config.api_key)
            
            model_obj = genai.GenerativeModel(
                use_model,
                system_instruction=system_prompt
            )
            response = model_obj.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            return True, response.text
            
        elif provider == LLMProvider.ANTHROPIC:
            from anthropic import Anthropic
            client = Anthropic(api_key=config.api_key)
            
            response = client.messages.create(
                model=use_model,
                max_tokens=max_tokens,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}]
            )
            return True, response.content[0].text
            
        elif provider == LLMProvider.OLLAMA:
            import httpx
            response = httpx.post(
                f"{config.base_url}/api/generate",
                json={
                    "model": use_model,
                    "prompt": prompt,
                    "system": system_prompt or "",
                    "options": {"num_predict": max_tokens, "temperature": temperature}
                },
                timeout=60
            )
            if response.status_code == 200:
                return True, response.json().get("response", "")
            return False, f"HTTP {response.status_code}"
            
    except Exception as e:
        return False, str(e)
    
    return False, "Unknown provider"


def get_provider_display_name(provider: LLMProvider) -> str:
    """Get human-readable name for a provider."""
    names = {
        LLMProvider.OPENAI: "OpenAI",
        LLMProvider.GEMINI: "Google Gemini",
        LLMProvider.ANTHROPIC: "Anthropic Claude",
        LLMProvider.OLLAMA: "Ollama (Local)",
        LLMProvider.CUSTOM: "Custom Endpoint",
    }
    return names.get(provider, provider.value)


def get_provider_help_url(provider: LLMProvider) -> str:
    """Get URL to get API key for a provider."""
    urls = {
        LLMProvider.OPENAI: "https://platform.openai.com/api-keys",
        LLMProvider.GEMINI: "https://aistudio.google.com/apikey",
        LLMProvider.ANTHROPIC: "https://console.anthropic.com/settings/keys",
        LLMProvider.OLLAMA: "https://ollama.ai/download",
        LLMProvider.CUSTOM: "",
    }
    return urls.get(provider, "")


def fetch_available_models(provider: LLMProvider) -> tuple[bool, List[str]]:
    """Fetch available models from a provider's API.
    
    Returns:
        tuple: (success, list_of_models)
    """
    config = get_provider_config(provider)
    
    if not config.is_configured:
        return False, AVAILABLE_MODELS.get(provider, [])
    
    try:
        if provider == LLMProvider.OPENAI:
            from openai import OpenAI
            client = OpenAI(api_key=config.api_key)
            models = client.models.list()
            # Filter to chat models only
            chat_models = [
                m.id for m in models.data 
                if m.id.startswith(("gpt-4", "gpt-3.5", "o1", "o3"))
                and not m.id.endswith("-instruct")
            ]
            return True, sorted(chat_models, reverse=True)[:10]
            
        elif provider == LLMProvider.GEMINI:
            import google.generativeai as genai
            genai.configure(api_key=config.api_key)
            models = genai.list_models()
            # Filter to generative models
            gen_models = [
                m.name.replace("models/", "") 
                for m in models 
                if "generateContent" in m.supported_generation_methods
            ]
            return True, gen_models[:10]
            
        elif provider == LLMProvider.ANTHROPIC:
            # Anthropic doesn't have a models list endpoint
            # Return known models
            return True, AVAILABLE_MODELS.get(provider, [])
            
        elif provider == LLMProvider.OLLAMA:
            import httpx
            response = httpx.get(f"{config.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "").split(":")[0] for m in models]
                return True, list(set(model_names))  # Remove duplicates
            return False, AVAILABLE_MODELS.get(provider, [])
            
        elif provider == LLMProvider.CUSTOM:
            from openai import OpenAI
            client = OpenAI(api_key=config.api_key or "dummy", base_url=config.base_url)
            try:
                models = client.models.list()
                return True, [m.id for m in models.data][:10]
            except:
                # If /models endpoint not available, return empty
                return True, [config.model] if config.model else []
                
    except Exception as e:
        # Fall back to hardcoded list on error
        return False, AVAILABLE_MODELS.get(provider, [])
    
    return False, []


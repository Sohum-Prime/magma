from typing import Any

try:
    from magma import registry
except ImportError:
    # Provide a dummy for environments where the full package isn't installed,
    # or during initial bootstrapping/testing.
    class DummyRegistry:
        def add_model(self, name:str, model:Any): pass
    registry = DummyRegistry()

# Import BAML's ClientRegistry for type hinting and instantiation.
from baml_py import ClientRegistry

class Model:
    """
    A configuration class for a foundation model, acting as a universal
    wrapper around LiteLLM and a configuration source for BAML.
    """
    
    # A mapping to translate LiteLLM provider prefixes to BAML provider names.
    _PROVIDER_MAP = {
        "openai": "openai",
        "anthropic": "anthropic",
        "vertex_ai": "vertex-ai",
        "azure": "azure-openai",
        "google": "google-ai",
        "ollama": "openai-generic", # Ollama uses an OpenAI-compatible API
        "huggingface": "openai-generic", # So do many Hugging Face endpoints
    }

    def __init__(self, id: str, **kwargs: Any):
        """
        Initializes a Model configuration.

        Args:
            id (str): The LiteLLM model string (e.g., "openai/gpt-4o").
            **kwargs: Additional parameters to pass to LiteLLM, such as
                      `temperature`, `api_key`, `api_base`, etc.
        """
        if not isinstance(id, str) or '/' not in id:
            raise ValueError("The 'id' must be a string in 'provider/model_name' format.")
            
        self.id = id
        self.params = kwargs
        
        # Automatically register the instance upon creation.
        registry.add_model(self.id, self)

    def __repr__(self) -> str:
        return f"magma.Model(id='{self.id}', params={self.params})"

    def to_baml_client(self) -> ClientRegistry:
        """
        Translates this model's configuration into a BAML ClientRegistry.

        This is used internally by Magma to configure BAML prompts at runtime.
        
        Returns:
            A configured baml_py.ClientRegistry instance.
        """
        cr = ClientRegistry()
        
        provider_prefix, model_name = self.id.split('/', 1)
        
        baml_provider = self._PROVIDER_MAP.get(provider_prefix, provider_prefix)
        
        # For Azure, BAML expects the deployment name, which is what comes after 'azure/'
        # For other providers, it's the model name.
        baml_model_name = model_name
        
        baml_options = self.params.copy()
        baml_options['model'] = baml_model_name
        
        client_name = "magma-client"

        cr.add_llm_client(
            name=client_name,
            provider=baml_provider,
            options=baml_options,
        )
        cr.set_primary(client_name)
        
        return cr
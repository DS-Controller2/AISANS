import os
from openai import OpenAI

class LLMClient:
    """
    A client for interacting with an LLM provider, configured for OpenRouter.
    """
    def __init__(self, api_key: str | None = None):
        """
        Initializes the LLMClient.

        Args:
            api_key: The API key for the LLM provider. If not provided,
                     it will be fetched from the OPENROUTER_API_KEY environment variable.

        Raises:
            ValueError: If no API key is provided and not found in the environment.
        """
        resolved_api_key = api_key if api_key is not None else os.getenv('OPENROUTER_API_KEY')

        if not resolved_api_key:
            raise ValueError("API key not provided and OPENROUTER_API_KEY environment variable not set.")

        self._api_key = resolved_api_key

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self._api_key,
            # Default headers can be added here if needed for all requests,
            # or added per-request via extra_headers in chat.completions.create()
            # http_headers={
            #   "HTTP-Referer": $YOUR_SITE_URL, # To identify your site
            #   "X-Title": $YOUR_SITE_NAME, # To identify your site
            # }
        )

        default_openrouter_model = "gryphe/mythomist-7b:free" # A known free/low-cost model
        self.default_model_name = os.getenv('OPENROUTER_DEFAULT_MODEL', default_openrouter_model)

    def generate_chat_completion(self, model: str | None = None, messages: list[dict], **kwargs) -> str | None:
        """
        Generates a chat completion using the specified model and messages.

        Args:
            model: The model to use for the completion. If None, uses the client's
                   default model (from OPENROUTER_DEFAULT_MODEL env var or hardcoded fallback).
            messages: A list of message objects (e.g., [{"role": "user", "content": "Hello"}]).
            **kwargs: Additional keyword arguments to pass to the OpenAI client's
                      chat.completions.create method (e.g., temperature, max_tokens).

        Returns:
            The content of the first chat completion choice, or None if no content.

        Example Usage:
            client = LLMClient() # Assumes OPENROUTER_API_KEY is set
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"}
            ]
            response_content = client.generate_chat_completion(
                model="openai/gpt-3.5-turbo",
                messages=messages,
                temperature=0.7
            )
            if response_content:
                print(response_content)
            else:
                print("Failed to get a response.")

        Note on OpenRouter specific headers (Site URL/Title):
        These can be passed via extra_headers in the create call:
        completion = self.client.chat.completions.create(
            model=model,
            messages=messages,
            extra_headers={
                 "HTTP-Referer": "http://localhost:3000", # Replace with your actual site URL
                 "X-Title": "AIsans Search", # Replace with your actual site name
            },
            **kwargs
        )
        This method does not currently implement these headers by default.
        They should be added if required by OpenRouter for tracking/ranking.
        """
        model_to_use = model if model is not None else self.default_model_name
        try:
            completion = self.client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                **kwargs
            )
            if completion.choices and completion.choices[0].message:
                return completion.choices[0].message.content
            return None
        except Exception as e:
            # Basic error handling, can be expanded
            print(f"Error during chat completion: {e}")
            return None

    def generate_text(self, prompt: str, model_name: str | None = None, system_message: str | None = None, **kwargs) -> str | None:
        """
        Generates a text response for a single user prompt.

        This is a convenience wrapper around generate_chat_completion.

        Args:
            prompt: The user's prompt string.
            model_name: The model to use. If None, uses the client's default model.
            system_message: An optional system message to prepend.
            **kwargs: Additional keyword arguments to pass to the underlying
                      chat.completions.create method (e.g., temperature, max_tokens).

        Returns:
            The generated text content, or None if an error occurred or no content was returned.
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        # Add OpenRouter specific headers here if desired for this convenience function
        # For example:
        # openrouter_headers = {
        #     "HTTP-Referer": "YOUR_AISANS_URL", # Configure this
        #     "X-Title": "AISANS LLM Query",    # Configure this
        # }
        # merged_kwargs = {**kwargs, "extra_headers": openrouter_headers}
        # return self.generate_chat_completion(model=model_name, messages=messages, **merged_kwargs)
        # For now, let's keep it simple and not add extra_headers by default in this method.
        # Users can pass 'extra_headers' via kwargs if needed.

        model_to_use = model_name if model_name is not None else self.default_model_name
        return self.generate_chat_completion(model=model_to_use, messages=messages, **kwargs)

if __name__ == '__main__':
    # This is a basic example and requires OPENROUTER_API_KEY to be set in the environment
    # or passed directly to LLMClient.
    # DO NOT COMMIT YOUR API KEY
    print("Running LLMClient basic test...")
    try:
        # To run this test, you must have OPENROUTER_API_KEY set in your environment.
        # Example: export OPENROUTER_API_KEY="your_key_here"
        if not os.getenv('OPENROUTER_API_KEY'):
            print("OPENROUTER_API_KEY not set. Skipping live API call test.")
            # Create a dummy client to test instantiation logic if key was hypothetically passed
            try:
                dummy_client = LLMClient(api_key="dummy_key_for_init_test")
                print("LLMClient instantiated with dummy key (no API call).")
            except ValueError as ve:
                print(f"Error instantiating with dummy key: {ve}") # Should not happen if key is provided
            raise SystemExit(0)


        client = LLMClient()
        print(f"LLMClient initialized with API key from env var.")
        print(f"Using default model: {client.default_model_name}")

        # Test generate_text with client's default model
        default_model_prompt = "Tell me a short joke."
        print(f"\nTesting generate_text with default model ('{client.default_model_name}')...")
        default_text_response = client.generate_text(prompt=default_model_prompt, max_tokens=50)
        if default_text_response:
            print(f"Response using default model for generate_text: {default_text_response}")
        else:
            print("Failed to get response using default model for generate_text.")

        # Test generate_chat_completion with client's default model
        default_chat_messages = [{"role": "user", "content": "What is 2+2?"}]
        print(f"\nTesting generate_chat_completion with default model ('{client.default_model_name}')...")
        default_chat_response = client.generate_chat_completion(messages=default_chat_messages, max_tokens=50) # No model specified
        if default_chat_response:
            print(f"Response using default model for generate_chat_completion: {default_chat_response}")
        else:
            print("Failed to get response using default model for generate_chat_completion.")

        print(f"\n--- Explicit model override tests ---")
        messages = [
            {"role": "system", "content": "You are a test assistant. Respond with 'Test successful.'"},
            {"role": "user", "content": "Ping"}
        ]

        # Using a free, fast model for testing
        # Check OpenRouter docs for currently available free/low-cost models if this one fails.
        # e.g., "mistralai/mistral-7b-instruct-v0.1" or "nousresearch/nous-capybara-7b-v1.9"
        # For this example, let's use a known small model.
        test_model = "gryphe/mythomist-7b:free"
        # As of early 2024, some free models might be like "mistralai/mistral-7b-instruct"
        # or specific versions like "nousresearch/nous-hermes-yi-34b" (not free, just example)
        # Check OpenRouter.ai for current free tier model options.
        # The specific model "gryphe/mythomist-7b:free" might change availability.

        print(f"Attempting to generate chat completion with model: {test_model}...")
        response = client.generate_chat_completion(
            model=test_model,
            messages=messages,
            temperature=0.1,
            max_tokens=50
        )

        if response:
            print(f"Received response: '{response}'")
            if "test successful" in response.lower():
                print("LLMClient test completion successful.")
            else:
                print("LLMClient test completion response did not match expected output.")
        else:
            print("Failed to get a response from the LLM for chat completion test.")

        # Test generate_text method
        print("\nTesting generate_text method...")
        simple_prompt = "What is the color of the sky on a clear day?"
        # Using the same test_model or another appropriate one
        text_response = client.generate_text(prompt=simple_prompt, model_name=test_model, max_tokens=50)
        if text_response:
            print(f"Response for '{simple_prompt}': {text_response}")
        else:
            print(f"Failed to get a response for '{simple_prompt}'.")

        system_prompt_text = "Describe a cat in two words."
        system_response = client.generate_text(
            prompt=system_prompt_text,
            model_name=test_model,
            system_message="You are a succinct and poetic assistant.",
            max_tokens=50
        )
        if system_response:
            print(f"Response for '{system_prompt_text}' with system message: {system_response}")
        else:
            print(f"Failed to get a response for '{system_prompt_text}' with system message.")

        # Example of temporarily setting the env var for default model to test that logic
        # This part is tricky to place perfectly without refactoring the whole test structure,
        # but illustrates the idea. For a real test suite, this would be a separate test case.
        print("\n--- Testing OPENROUTER_DEFAULT_MODEL environment variable override ---")
        original_env_default_model = os.environ.pop('OPENROUTER_DEFAULT_MODEL', None)
        # Use a model known to be different and very small/fast if possible, e.g. a dummy or specific small one
        # For this example, we'll just use a variation or assume another free model exists
        # Note: The availability of specific free models on OpenRouter can change.
        # Using "mistralai/mistral-7b-instruct:free" as an example of a potentially different free model.
        # If "gryphe/mythomist-7b:free" was already the hardcoded default, this tests if env var overrides it.
        # Ensure it's a model that's likely to be available.
        # For robustness, this could be a model you know is *different* from the hardcoded default.
        # Let's assume the hardcoded default is "gryphe/mythomist-7b:free".
        # We'll try to set OPENROUTER_DEFAULT_MODEL to something else, like "google/gemma-7b-it:free" if available
        # or just re-use "mistralai/mistral-7b-instruct:free" if that's different enough or for demonstration.
        # For this example, let's try "mistralai/mistral-7b-instruct:free"
        # A less ideal choice if it's the same as the hardcoded, but demonstrates the mechanism.
        # A better choice would be a model like "google/gemma-2b-it:free" if available and different.

        # For the sake of a clearer test, let's use a distinct model name that is likely free.
        # Check OpenRouter for a very small, fast, free model.
        # If "gryphe/mythomist-7b:free" is the default, let's try another one.
        # "openrouter/cinematika-7b:free" is another option often available.
        env_test_model_override = "openrouter/cinematika-7b:free"
        # If the hardcoded default_openrouter_model is the same as env_test_model_override, this test won't be as effective.
        # Ensure they are different for a proper test of the environment variable override.
        # If default_openrouter_model = "gryphe/mythomist-7b:free", then this is a good test.

        os.environ['OPENROUTER_DEFAULT_MODEL'] = env_test_model_override

        # Re-initialize client to pick up new env var for default_model_name
        try:
            env_client = LLMClient()
            print(f"LLMClient initialized with OPENROUTER_DEFAULT_MODEL set to: {env_client.default_model_name}")
            self.assertEqual(env_client.default_model_name, env_test_model_override, "OPENROUTER_DEFAULT_MODEL env var was not picked up.")

            env_default_prompt = "Briefly, what is OpenRouter?"
            print(f"Testing generate_text with overridden default model ('{env_client.default_model_name}')...")
            env_default_response = env_client.generate_text(prompt=env_default_prompt, max_tokens=60)
            if env_default_response:
                print(f"Response using overridden default model: {env_default_response}")
            else:
                print(f"Failed to get response using overridden default model for generate_text.")
        finally:
            if original_env_default_model is not None:
                os.environ['OPENROUTER_DEFAULT_MODEL'] = original_env_default_model
            else:
                os.environ.pop('OPENROUTER_DEFAULT_MODEL', None)
            print(f"Restored OPENROUTER_DEFAULT_MODEL to original state (was: {original_env_default_model}).")


    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        # This will catch API errors if the key is invalid or network issues.
        print(f"An unexpected error occurred during the test: {e}")
        print("Ensure your OPENROUTER_API_KEY is valid and you have internet access.")
        print("Also check if the model is currently available on OpenRouter.")

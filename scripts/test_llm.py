import sys
import os

# Add project root to sys.path to allow imports from aisans package
# This assumes 'scripts/' is one level down from the project root.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aisans.llm.client import LLMClient

def main():
    """
    Main function to test the LLMClient.
    """
    print("Starting LLMClient test script...")

    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("\nError: The OPENROUTER_API_KEY environment variable is not set.")
        print("Please set it before running this script.")
        print("Example: export OPENROUTER_API_KEY='your_api_key_here'")
        print("Aborting test.")
        return

    print(f"OPENROUTER_API_KEY found (length: {len(api_key)}).")

    try:
        # Instantiate LLMClient
        # The client will use OPENROUTER_API_KEY from the environment by default.
        # It will also use OPENROUTER_DEFAULT_MODEL or its internal fallback.
        client = LLMClient()
        print(f"LLMClient instantiated successfully.")
        print(f"Using default model for generation: {client.default_model_name}")

        # Define a sample prompt
        prompt = "What is the capital of France? Explain in one concise sentence."
        print(f"\nSending prompt: \"{prompt}\"")

        # Call generate_text (will use the client's default model)
        # Explicitly setting max_tokens for a concise response.
        response = client.generate_text(prompt=prompt, max_tokens=60)

        if response:
            print("\n--- LLM Response ---")
            print(response)
            print("--- End of Response ---")
        else:
            print("\nFailed to get a response from the LLM.")
            print("This could be due to various reasons such as network issues,")
            print("API key problems (e.g., insufficient credits), or model unavailability.")

        # Example with a specific model (overriding client's default)
        # Note: Ensure this model is available on OpenRouter and your key has access.
        # Using a common small model for this example.
        specific_model = "mistralai/mistral-7b-instruct:free"
        # Check if this model is different from client.default_model_name for a more meaningful test
        if specific_model.lower() != client.default_model_name.lower():
            print(f"\nSending prompt to a specific model: \"{specific_model}\"")
            prompt_specific = "Briefly describe the concept of a Large Language Model."
            print(f"Prompt: \"{prompt_specific}\"")
            response_specific = client.generate_text(
                prompt=prompt_specific,
                model_name=specific_model,
                max_tokens=100
            )
            if response_specific:
                print("\n--- LLM Response (Specific Model) ---")
                print(response_specific)
                print("--- End of Response (Specific Model) ---")
            else:
                print(f"\nFailed to get a response from the specific model {specific_model}.")
        else:
            print(f"\nSkipping specific model test as it's the same as the default: {specific_model}")


    except ValueError as ve:
        print(f"\nConfiguration Error: {ve}")
        print("This might happen if the API key is considered invalid by the client's initial checks.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("This could be an API error (e.g. authentication, rate limits, model not found)")
        print("or a network problem. Check your API key and internet connection.")

    print("\nLLMClient test script finished.")

if __name__ == "__main__":
    main()

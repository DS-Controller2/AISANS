import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from aisans.llm.client import LLMClient
# from openai import OpenAI # Not strictly needed unless for type hinting complex mocks

class TestLLMClient(unittest.TestCase):

    def setUp(self):
        # Store and clear relevant environment variables before each test
        self.original_openrouter_api_key = os.environ.pop('OPENROUTER_API_KEY', None)
        self.original_openrouter_default_model = os.environ.pop('OPENROUTER_DEFAULT_MODEL', None)

    def tearDown(self):
        # Restore environment variables after each test
        if self.original_openrouter_api_key is not None:
            os.environ['OPENROUTER_API_KEY'] = self.original_openrouter_api_key
        else:
            os.environ.pop('OPENROUTER_API_KEY', None) # Ensure it's gone if it wasn't there

        if self.original_openrouter_default_model is not None:
            os.environ['OPENROUTER_DEFAULT_MODEL'] = self.original_openrouter_default_model
        else:
            os.environ.pop('OPENROUTER_DEFAULT_MODEL', None) # Ensure it's gone

    # Test API Key Handling
    @patch('aisans.llm.client.OpenAI') # Mock OpenAI to prevent actual client instantiation
    def test_init_with_api_key_arg(self, mock_openai_class):
        client = LLMClient(api_key="test_key_arg")
        self.assertEqual(client._api_key, "test_key_arg")
        mock_openai_class.assert_called_once_with(
            base_url="https://openrouter.ai/api/v1",
            api_key="test_key_arg"
        )

    @patch('aisans.llm.client.OpenAI')
    def test_init_with_env_var(self, mock_openai_class):
        os.environ['OPENROUTER_API_KEY'] = 'env_test_key'
        client = LLMClient()
        self.assertEqual(client._api_key, "env_test_key")
        mock_openai_class.assert_called_once_with(
            base_url="https://openrouter.ai/api/v1",
            api_key="env_test_key"
        )

    @patch('aisans.llm.client.OpenAI') # Still mock OpenAI, though error should be pre-init
    def test_init_no_api_key_raises_value_error(self, mock_openai_class):
        # Ensure OPENROUTER_API_KEY is not in os.environ (handled by setUp)
        with self.assertRaisesRegex(ValueError, "API key not provided and OPENROUTER_API_KEY environment variable not set."):
            LLMClient()

    @patch('aisans.llm.client.OpenAI')
    def test_init_api_key_arg_overrides_env_var(self, mock_openai_class):
        os.environ['OPENROUTER_API_KEY'] = 'env_key'
        client = LLMClient(api_key="arg_key")
        self.assertEqual(client._api_key, "arg_key")
        mock_openai_class.assert_called_once_with(
            base_url="https://openrouter.ai/api/v1",
            api_key="arg_key"
        )

    # Test Default Model Logic
    @patch('aisans.llm.client.OpenAI')
    def test_default_model_hardcoded(self, mock_openai_class):
        # OPENROUTER_DEFAULT_MODEL is cleared by setUp
        client = LLMClient(api_key="test_key")
        self.assertEqual(client.default_model_name, "gryphe/mythomist-7b:free")

    @patch('aisans.llm.client.OpenAI')
    def test_default_model_from_env_var(self, mock_openai_class):
        os.environ['OPENROUTER_DEFAULT_MODEL'] = 'env_default_model_name'
        # API key needs to be set for successful instantiation
        client = LLMClient(api_key="test_key")
        self.assertEqual(client.default_model_name, 'env_default_model_name')

    # Test generate_chat_completion with Mocking
    @patch('aisans.llm.client.OpenAI')
    def test_generate_chat_completion_success(self, mock_openai_class):
        mock_instance = mock_openai_class.return_value
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Test response"))]
        )

        client = LLMClient(api_key="test_key")
        response = client.generate_chat_completion(model="test_model", messages=[{"role": "user", "content": "Hi"}])

        self.assertEqual(response, "Test response")
        mock_instance.chat.completions.create.assert_called_once_with(
            model="test_model",
            messages=[{"role": "user", "content": "Hi"}]
        )

    @patch('aisans.llm.client.OpenAI')
    def test_generate_chat_completion_uses_default_model(self, mock_openai_class):
        mock_instance = mock_openai_class.return_value
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Default model response"))]
        )

        # API key needs to be set
        client = LLMClient(api_key="test_key")
        # OPENROUTER_DEFAULT_MODEL is cleared by setUp, so it uses hardcoded default

        response = client.generate_chat_completion(messages=[{"role": "user", "content": "Hi"}]) # No model specified

        self.assertEqual(response, "Default model response")
        mock_instance.chat.completions.create.assert_called_once_with(
            model=client.default_model_name, # Should be "gryphe/mythomist-7b:free"
            messages=[{"role": "user", "content": "Hi"}]
        )
        self.assertEqual(client.default_model_name, "gryphe/mythomist-7b:free")


    @patch('aisans.llm.client.OpenAI')
    def test_generate_chat_completion_api_error_returns_none(self, mock_openai_class):
        mock_instance = mock_openai_class.return_value
        mock_instance.chat.completions.create.side_effect = Exception("API Error")

        client = LLMClient(api_key="test_key")
        response = client.generate_chat_completion(model="test_model", messages=[{"role": "user", "content": "Hi"}])

        self.assertIsNone(response)

    # Test generate_text (mocking generate_chat_completion)
    # We mock generate_chat_completion here because we've already tested its direct interaction
    # with the OpenAI client. Now we're testing the logic within generate_text itself.
    def test_generate_text_success(self):
        with patch.object(LLMClient, 'generate_chat_completion', return_value="Mocked text response") as mock_gcc:
            # Need to ensure LLMClient can be instantiated, so provide dummy key
            # or ensure env var is set if that's the preferred path for this test.
            # Since we are mocking out the actual call, a dummy key is fine.
            client = LLMClient(api_key="dummy_key_for_generate_text_test")

            response = client.generate_text(prompt="Hello", model_name="text_model_explicit")

            self.assertEqual(response, "Mocked text response")
            mock_gcc.assert_called_once_with(
                model="text_model_explicit",
                messages=[{"role": "user", "content": "Hello"}]
            )

    def test_generate_text_with_system_message(self):
        with patch.object(LLMClient, 'generate_chat_completion', return_value="System response") as mock_gcc:
            client = LLMClient(api_key="dummy_key") # Dummy key is fine

            response = client.generate_text(
                prompt="User prompt",
                model_name="text_model_sys",
                system_message="System intro"
            )

            self.assertEqual(response, "System response")
            mock_gcc.assert_called_once_with(
                model="text_model_sys",
                messages=[
                    {"role": "system", "content": "System intro"},
                    {"role": "user", "content": "User prompt"}
                ]
            )

    def test_generate_text_uses_default_model(self):
        with patch.object(LLMClient, 'generate_chat_completion', return_value="Default model text response") as mock_gcc:
            # Ensure API key is available for instantiation
            client = LLMClient(api_key="dummy_key")
            # Default model will be the hardcoded one since env var is cleared by setUp

            response = client.generate_text(prompt="Hi") # No model_name specified

            self.assertEqual(response, "Default model text response")
            mock_gcc.assert_called_once_with(
                model=client.default_model_name, # Should be "gryphe/mythomist-7b:free"
                messages=[{"role": "user", "content": "Hi"}]
            )
            self.assertEqual(client.default_model_name, "gryphe/mythomist-7b:free")

if __name__ == '__main__':
    unittest.main()

import tiktoken

from src.database.models import (
    AIModel,
    StylePrompt,
    Language,
)
import logging

logger = logging.getLogger('app')


def estimate_translation_tokens(
    input_text: str,
    prompt: StylePrompt,
    model: AIModel,
) -> int:
    """
    Estimates the number of input and output tokens required for translating text
    from one language to another using a GPT model via an API like OpenAI or OpenRouter.

    This function uses the `tiktoken` library to count tokens based on the specified model.
    It's crucial to choose the correct model name for accurate token estimation.  The output token
    estimation includes the translated text *and* a safety margin since the exact output token
    count will vary based on the translation and the model's response.

    Args:
        input_text: The text to be translated.
        source_language: The language of the input text (e.g., "English").
        target_language: The language to translate to (e.g., "French").
        model_name: The name of the GPT model to use for token estimation
                    (e.g., "gpt-3.5-turbo", "gpt-4").  Defaults to "gpt-3.5-turbo".

    Returns:
        A tuple containing:
            - input_tokens: The estimated number of input tokens.
            - output_tokens: The estimated number of output tokens (translation + margin).
    """

    try:
        encoding = tiktoken.encoding_for_model(model.name)
    except KeyError:
        logger.warning(
            'model %s not found. Using cl100k_base encoding.', model.name
        )
        encoding = tiktoken.get_encoding(
            'cl100k_base'
        )  # Good default for many models

    # 1. Estimate input tokens
    input_tokens = len(encoding.encode(input_text))

    # 2. Estimate output tokens.  This is tricky because the translated text
    #    length can vary.  We'll use a heuristic:  Assume the translated text
    #    is roughly the same length as the input text in terms of token count.
    #    Add a safety margin in case the translation is more verbose.
    #    Also include tokens for system prompt and instructions.

    # System prompt for translation.
    system_prompt_tokens = len(encoding.encode(prompt.text))

    # Total input tokens for translation
    input_tokens += system_prompt_tokens

    base_output_tokens = len(
        encoding.encode(input_text)
    )  # Rough estimate of translated text length

    # Add a safety margin (e.g., 50% more tokens than the estimated base length)
    safety_margin = int(0.5 * base_output_tokens)

    # Include tokens for the system prompt and instructions in the output estimate
    output_tokens = base_output_tokens + safety_margin

    return input_tokens + output_tokens

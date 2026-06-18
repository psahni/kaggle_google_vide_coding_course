"""Groq API integration for customer support agent."""

import os

from groq import Groq


def get_groq_client() -> Groq:
    """Initialize Groq client with API key from environment."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    return Groq(api_key=api_key)


def call_groq_model(
    messages: list,
    system_prompt: str = "",
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """Call Groq API and return the response text.

    Args:
        messages: List of message dicts with 'role' and 'content'
        system_prompt: System prompt for the model
        model: Groq model name (default: llama-3.3-70b-versatile)
        temperature: Model temperature
        max_tokens: Maximum tokens in response

    Returns:
        Response text from Groq model
    """
    client = get_groq_client()

    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    response = client.chat.completions.create(
        model=model,
        messages=full_messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content

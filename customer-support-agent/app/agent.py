# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.workflow import Workflow
from google.adk.apps import App
from google.adk.events.event import Event
import os

from .groq_utils import call_groq_model

os.environ.setdefault("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))


def classify_query(node_input: str) -> Event:
    """Classify if user query is shipping-related or unrelated.

    Shipping-related topics: rates, tracking, delivery, returns
    """
    shipping_keywords = [
        "rate",
        "track",
        "delivery",
        "return",
        "shipping",
        "cost",
        "price",
        "when",
        "arrive",
    ]
    query_lower = node_input.lower()

    is_shipping = any(keyword in query_lower for keyword in shipping_keywords)

    if is_shipping:
        return Event(output=node_input, route="shipping")  # type: ignore
    else:
        return Event(output=node_input, route="unrelated")  # type: ignore


def shipping_faq_agent(node_input: str) -> str:
    """Answer shipping-related customer support questions using Groq."""
    system_prompt = """You are a helpful shipping support representative for a shipping company.
Answer questions about shipping rates, tracking information, delivery times, and returns.
Be professional, accurate, and helpful.
If you don't have specific information, provide general guidance or offer to connect them with a specialist.
Keep responses concise and friendly."""

    messages = [{"role": "user", "content": node_input}]

    response = call_groq_model(
        messages=messages,
        system_prompt=system_prompt,
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        max_tokens=512,
    )

    return response


def decline_politely(node_input: str) -> str:
    """Politely decline to answer non-shipping questions."""
    return """I appreciate your question, but I'm specifically trained to help with shipping-related inquiries
such as rates, tracking, delivery times, and returns.

For other topics, please contact our general customer support team. How can I assist you with your shipping needs?"""


root_agent = Workflow(
    name="customer_support_agent",
    edges=[
        ("START", classify_query),
        (
            classify_query,
            {
                "shipping": shipping_faq_agent,
                "unrelated": decline_politely,
            },
        ),
    ],
    description="Customer support representative for shipping company that routes queries based on topic",
)

app = App(
    root_agent=root_agent,
    name="app",
)

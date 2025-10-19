import logging
import os
from typing import Optional, Any, Dict

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NotificationDecision(BaseModel):
    """Model for notification decision response."""
    should_notify: bool = Field(description="Whether this message should trigger a Slack notification")
    reasoning: str = Field(description="Brief explanation of the decision")


class LLMWithTokenCount(Runnable):
    """Runnable that calls LLM and returns both parsed result and token count."""

    def __init__(self, llm: ChatOpenAI, parser: JsonOutputParser):
        self.llm = llm
        self.parser = parser

    def invoke(self, input: Dict[str, Any], *args, **kwargs) -> tuple[NotificationDecision, Optional[int]]:
        # Synchronous version - call async version
        import asyncio
        return asyncio.run(self.ainvoke(input))

    async def ainvoke(self, input: Dict[str, Any], *args, **kwargs) -> tuple[NotificationDecision, Optional[int]]:
        # Call LLM directly to get AIMessage with usage_metadata
        ai_message = await self.llm.ainvoke(input)

        # Extract token count from usage_metadata
        token_count = None
        if hasattr(ai_message, 'usage_metadata') and ai_message.usage_metadata:
            token_count = ai_message.usage_metadata.get('total_tokens')

        # Use JsonOutputParser to parse content (handles markdown automatically)
        parsed_dict = await self.parser.ainvoke(ai_message)

        # Convert to NotificationDecision object
        result = NotificationDecision(**parsed_dict)

        return result, token_count


# Initialize LangChain components
openai_api_key = os.getenv("OPENAI_API_KEY")
llm = None

# Only initialize if API key is available
if openai_api_key:
    llm = ChatOpenAI(
        model="gpt-5-nano",
        temperature=0,
        openai_api_key=openai_api_key
    )

    notification_parser = JsonOutputParser(pydantic_object=NotificationDecision)

    # Create custom runnable that combines LLM call with token counting
    llm_with_tokens = LLMWithTokenCount(llm, notification_parser)

    notification_prompt = PromptTemplate(
        input_variables=["message"],
        template="""
You are a software development recruitment assistant. Analyze the following WhatsApp message and determine if it indicates someone is looking for software engineers with expertise in Python, AWS, React, GCP, Node.js, or TypeScript.

Return a JSON object with two fields:
- should_notify: boolean (true if this is a recruitment message for relevant tech stack, false otherwise)
- reasoning: brief explanation of your decision

Message: {message}

Consider these examples:
- "Looking for a React developer for our startup" → should_notify: true
- "Need Python backend engineer with AWS experience" → should_notify: true
- "Hiring fullstack developer Node.js and React" → should_notify: true
- "TypeScript frontend position available" → should_notify: true
- "GCP cloud engineer wanted" → should_notify: true
- "Just chatting about coffee" → should_notify: false
- "Selling my old laptop" → should_notify: false
- "Looking for a graphic designer" → should_notify: false

{format_instructions}
""",
        partial_variables={"format_instructions": notification_parser.get_format_instructions()},
    )

    notification_chain = notification_prompt | llm_with_tokens
else:
    # Set to None when no API key is available
    notification_chain = None


async def should_notify(message_text: str) -> tuple[bool, str, Optional[int]]:
    """
    Determine if a Slack notification should be sent based on message content.
    Uses LangChain with OpenAI to analyze if the message is about looking for
    software engineers with Python, AWS, React, GCP, Node.js, or TypeScript expertise.

    :param message_text: The text content of the WhatsApp message
    :return: Tuple of (should_notify: bool, reasoning: str, token_count: Optional[int])
    """
    try:
        if not message_text or not message_text.strip():
            return False, "Empty message", None

        # If no API key is available, skip analysis and return False
        if notification_chain is None:
            logger.warning("OpenAI API key not available, skipping message analysis")
            return False, "API key not available", None

        # Use the clean chain that handles both parsing and token counting
        decision, token_count = await notification_chain.ainvoke({"message": message_text.strip()})

        should_notify = decision.should_notify
        reasoning = decision.reasoning

        logger.info("Notification analysis for message: '%s...' -> %s (reasoning: %s, tokens: %s)",
                   message_text[:100], should_notify, reasoning, token_count)
        return should_notify, reasoning, token_count

    except Exception as e:
        logger.exception("Error analyzing message for notification: %s", e)
        # Default to not sending notification if analysis fails
        return False, f"Analysis failed: {str(e)}", None

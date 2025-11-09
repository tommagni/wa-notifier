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

    def invoke(self, input: Dict[str, Any], *args, **kwargs) -> tuple[NotificationDecision, Optional[int], Optional[int], Optional[int]]:
        # Synchronous version - call async version
        import asyncio
        return asyncio.run(self.ainvoke(input))

    async def ainvoke(self, input: Dict[str, Any], *args, **kwargs) -> tuple[NotificationDecision, Optional[int], Optional[int], Optional[int]]:
        # Call LLM directly to get AIMessage with usage_metadata
        ai_message = await self.llm.ainvoke(input)

        # Extract token counts from usage_metadata
        total_tokens = None
        input_tokens = None
        output_tokens = None
        if hasattr(ai_message, 'usage_metadata') and ai_message.usage_metadata:
            usage = ai_message.usage_metadata
            total_tokens = usage.get('total_tokens')
            input_tokens = usage.get('input_tokens')
            output_tokens = usage.get('output_tokens')

        # Use JsonOutputParser to parse content (handles markdown automatically)
        parsed_dict = await self.parser.ainvoke(ai_message)

        # Convert to NotificationDecision object
        result = NotificationDecision(**parsed_dict)

        return result, total_tokens, input_tokens, output_tokens


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
You are a software development agency lead notifications assistant. You monitor whatsapp messages and determine if they are relevant to the software development agency.

About the agency:
- Tech stack: Python, AWS, React, GCP, Node.js, TypeScript.
- Offering: Full stack / Backend / Frontend devs.

Analyze the below message (in quotes) and determine if it indicates someone is looking for:
- software engineer(/s) with expertise in the agency tech stack (partial match is enough).
- Recommendation for a software development agency (even if not mentioning tech stack).
- Recommendation to an offshore developer or offshore development team(even if not mentioning tech stack).

Return a JSON object with two fields:
- should_notify: boolean (true if this is a recruitment message for relevant tech stack, false otherwise)
- reasoning: brief explanation of your decision

Message to analyze: "{message}"

Clarifications:
- If the message is not about looking for a software engineer / recommendation message, return false.

Examples:
- "Looking for a React developer for our startup" → should_notify: true
- "Need Python backend engineer with AWS experience" → should_notify: true
- "Hiring fullstack developer Node.js and React" → should_notify: true
- "TypeScript frontend position available" → should_notify: true
- "GCP cloud engineer wanted" → should_notify: true
- "Just chatting about coffee" → should_notify: false
- "Selling my old laptop" → should_notify: false
- "Looking for a graphic designer" → should_notify: false
- "Looking for a co-founder for our startup with react&aws experience" → should_notify: false
- "Looking for an offshore developer for our startup" → should_notify: true
- "React, Typsecript" → should_notify: false (it's not looking for a software engineer / recommendation message)

{format_instructions}
""",
        partial_variables={"format_instructions": notification_parser.get_format_instructions()},
    )

    notification_chain = notification_prompt | llm_with_tokens
else:
    # Set to None when no API key is available
    notification_chain = None


async def should_notify(message_text: str) -> tuple[bool, str, Optional[int], Optional[int], Optional[int]]:
    """
    Determine if a Slack notification should be sent based on message content.
    Uses LangChain with OpenAI to analyze if the message is about looking for
    software engineers with Python, AWS, React, GCP, Node.js, or TypeScript expertise.

    :param message_text: The text content of the WhatsApp message
    :return: Tuple of (should_notify: bool, reasoning: str, total_tokens: Optional[int], input_tokens: Optional[int], output_tokens: Optional[int])
    """
    try:
        if not message_text or not message_text.strip():
            return False, "Empty message", None, None, None

        # If no API key is available, skip analysis and return False
        if notification_chain is None:
            logger.warning("OpenAI API key not available, skipping message analysis")
            return False, "API key not available", None, None, None

        # Use the clean chain that handles both parsing and token counting
        decision, total_tokens, input_tokens, output_tokens = await notification_chain.ainvoke({"message": message_text.strip()})

        should_notify = decision.should_notify
        reasoning = decision.reasoning

        logger.info("Notification analysis for message: '%s...' -> %s (reasoning: %s, total: %s, input: %s, output: %s)",
                   message_text[:100], should_notify, reasoning, total_tokens, input_tokens, output_tokens)
        return should_notify, reasoning, total_tokens, input_tokens, output_tokens

    except Exception as e:
        logger.exception("Error analyzing message for notification: %s", e)
        # Default to not sending notification if analysis fails
        return False, f"Analysis failed: {str(e)}", None, None, None

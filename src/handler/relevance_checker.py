import logging
import os

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NotificationDecision(BaseModel):
    """Model for notification decision response."""
    should_notify: bool = Field(description="Whether this message should trigger a Slack notification")
    reasoning: str = Field(description="Brief explanation of the decision")


# Initialize LangChain components
openai_api_key = os.getenv("OPENAI_API_KEY")

# Only initialize if API key is available
if openai_api_key:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        openai_api_key=openai_api_key
    )

    notification_parser = JsonOutputParser(pydantic_object=NotificationDecision)

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

    notification_chain = notification_prompt | llm | notification_parser
else:
    # Set to None when no API key is available
    notification_chain = None


async def should_notify(message_text: str) -> bool:
    """
    Determine if a Slack notification should be sent based on message content.
    Uses LangChain with OpenAI to analyze if the message is about looking for
    software engineers with Python, AWS, React, GCP, Node.js, or TypeScript expertise.

    :param message_text: The text content of the WhatsApp message
    :return: True if notification should be sent, False otherwise
    """
    try:
        if not message_text or not message_text.strip():
            return False

        # If no API key is available, skip analysis and return False
        if notification_chain is None:
            logger.warning("OpenAI API key not available, skipping message analysis")
            return False

        result: NotificationDecision = await notification_chain.ainvoke({"message": message_text.strip()})

        should_notify = result.get('should_notify')
        reasoning = result.get('reasoning')
        logger.info("Notification analysis for message: '%s...' -> %s (reasoning: %s)",
                   message_text[:100], should_notify, reasoning)
        return should_notify

    except Exception as e:
        logger.exception("Error analyzing message for notification: %s", e)
        # Default to not sending notification if analysis fails
        return False

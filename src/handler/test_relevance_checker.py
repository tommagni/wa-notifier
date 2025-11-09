import pytest
import os
from handler.relevance_checker import should_notify


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY environment variable not set"
)
class TestRelevanceChecker:
    """Integration tests for relevance_checker using real OpenAI API calls."""

    @pytest.mark.parametrize("message,expected", [
        # Positive cases - should notify
        # ("Looking for a React developer for our startup", True),
        # ("היי חברים,\nמחפש פרילנס BE Python מנוסה לPart time חודשי. משימות של חובות טכנים ולעיתים גם פיתוח של פיצ׳רים סגורים.\nניסיון בK8S, AWS, Python שליטה מלאה.\nלכניסה וDelivery מיידי.\n🙏🏻🙏🏻", True),
        # ("Need Python backend engineer with AWS experience", True),
        # ("Hiring fullstack developer Node.js and React", True),
        # ("TypeScript frontend position available", True),
        # ("GCP cloud engineer wanted", True),
        # ("Senior Python developer needed for our team", True),
        # ("React Native mobile developer position open", True),
        # ("Node.js backend engineer with AWS Lambda experience", True),
        # ("Looking for TypeScript expert for our frontend team", True),
        # ("GCP DevOps engineer needed urgently", True),

        # # Negative cases - should not notify
        # ("Just chatting about coffee", False),
        # ("Selling my old laptop", False),
        # ("Looking for a graphic designer", False),
        # ("Need a marketing specialist", False),
        # ("Hiring sales representatives", False),
        # ("Looking for data entry clerk", False),
        # ("Product manager position available", False),
        # ("UX designer wanted", False),
        # ("Content writer needed", False),
        # ("Customer support specialist position", False),
        # ("TypeScript", False),
    ])
    async def test_message_relevance(self, message, expected):
        """Test various messages to ensure relevance detection works correctly."""
        result = await should_notify(message)
        should_notify_bool = result[0]
        assert should_notify_bool == expected, f"Failed for message: '{message}'"

    # async def test_empty_message(self):
    #     """Test that empty messages don't trigger notifications."""
    #     result = await should_notify("")
    #     assert result[0] is False

    #     result = await should_notify("   ")
    #     assert result[0] is False

    #     result = await should_notify(None)
    #     assert result[0] is False

    # async def test_long_message(self):
    #     """Test that long messages are handled properly."""
    #     long_message = "We are looking for an experienced Python backend developer with strong AWS skills to join our growing team. The ideal candidate should have experience with Django, PostgreSQL, and cloud infrastructure on AWS. Knowledge of React would be a plus for full-stack capabilities. This is a remote position with competitive salary."
    #     result = await should_notify(long_message)
    #     assert result[0] is True

    # async def test_edge_cases(self):
    #     """Test edge cases and ambiguous messages."""
    #     # Messages that might be borderline
    #     ambiguous_cases = [
    #         ("Looking for developers", False),  # Too vague
    #         ("Need programmers for our project", False),  # No specific tech stack
    #         ("Hiring software engineers", False),  # Too generic
    #     ]

    #     for message, expected in ambiguous_cases:
    #         result = await should_notify(message)
    #         assert result[0] == expected, f"Failed for ambiguous message: '{message}'"

    # @pytest.mark.parametrize("tech_stack", [
    #     "Python",
    #     "AWS",
    #     "React",
    #     "GCP",
    #     "Node.js",
    #     "TypeScript",
    #     "python",
    #     "aws",
    #     "react",
    #     "gcp",
    #     "node.js",
    #     "typescript",
    # ])
    # async def test_technology_specific_messages(self, tech_stack):
    #     """Test that messages mentioning specific technologies are detected."""
    #     message = f"Looking for a developer with {tech_stack} experience"
    #     result = await should_notify(message)
    #     assert result[0] is True, f"Failed to detect {tech_stack} in message"

    # async def test_api_error_handling(self):
    #     """Test that API errors are handled gracefully."""
    #     # This should not raise an exception even if the API fails
    #     # The function should return False on error
    #     try:
    #         result = await should_notify("Test message")
    #         # Result should be boolean regardless of API success/failure
    #         assert isinstance(result[0], bool)
    #     except Exception as e:
    #         pytest.fail(f"should_notify raised an unexpected exception: {e}")

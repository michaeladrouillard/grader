import pytest
from src.github_handler import GitHubRepo
from src.llm_handler import LLMAssessor
from src.format_checker import FormatValidator
from src.markdown_generator import MarkdownReport

def test_format_validator():
    validator = FormatValidator()
    
    # test valid format
    valid_assessment = {
        "score": 85,
        "reason": "Well-organized code with clear structure",
        "confidence": 0.9
    }
    assert validator.is_valid(valid_assessment) == True
    
    # test invalid format
    invalid_assessment = {
        "score": 150,  # invalid score range
        "reason": "Test"
    }
    assert validator.is_valid(invalid_assessment) == False

def test_markdown_generator():
    generator = MarkdownReport()
    test_results = [
        {
            "item": {
                "title": "Test Item",
                "description": "Test Description"
            },
            "assessment": {
                "score": 80,
                "reason": "Test reason",
                "confidence": 0.9
            }
        }
    ]
    
    report = generator.generate(test_results)
    assert "Test Item" in report
    assert "80/100" in report


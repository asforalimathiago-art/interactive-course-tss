"""
Smoke tests for basic functionality.
"""


def test_imports():
    """Test that core modules can be imported."""
    import engine_reference
    import tss_crypto

    assert engine_reference is not None
    assert tss_crypto is not None


def test_engine_app_exists():
    """Test that FastAPI app is created."""
    from engine_reference import app

    assert app is not None
    assert app.title == "Course+TSS"


def test_question_bank_loaded():
    """Test that question bank is loaded."""
    from engine_reference import BANK

    assert isinstance(BANK, dict)
    assert len(BANK) > 0


def test_rules_loaded():
    """Test that rules are loaded."""
    from engine_reference import RULES

    assert isinstance(RULES, dict)

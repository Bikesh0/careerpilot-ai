from app.ai.suitability import SuitabilityEngine


def test_suitability_engine_is_importable_and_returns_its_contract():
    result = SuitabilityEngine().evaluate({}, {})

    assert result["overall_score"] == 0
    assert result["missing_skills"] == []
    assert result["reasoning"] == []

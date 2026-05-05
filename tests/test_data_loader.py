from llm_cost.data_loader import find_model, get_providers, load_models


def test_load_models_from_package_data():
    models = load_models()

    assert len(models) == 33
    assert find_model("gpt-5") is not None
    assert find_model("deepseek-v4-pro") is not None
    assert find_model("glm-5-1") is not None
    assert find_model("kimi-k2-6") is not None
    assert find_model("minimax-m2-7") is not None


def test_get_providers_groups_models():
    providers = get_providers()

    assert "OpenAI" in providers
    assert providers["OpenAI"]

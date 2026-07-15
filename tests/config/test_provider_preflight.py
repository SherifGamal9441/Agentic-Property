from config.pydantic.settings import Settings


def test_selected_provider_reports_only_missing_variable_names():
    settings = Settings(
        llm_provider="custom_openai_compatible_endpoint",
        custom_openai_model="",
        custom_openai_base_url="",
        _env_file=None,
    )

    errors = settings.provider_errors()

    assert errors == [
        "CUSTOM_OPENAI_MODEL is required for custom_openai_compatible_endpoint.",
        "CUSTOM_OPENAI_BASE_URL is required for custom_openai_compatible_endpoint.",
    ]
    assert all("key" not in error.casefold() for error in errors)

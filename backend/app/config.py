from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class _CsvEnvSource(EnvSettingsSource):
    _CSV_FIELDS = {"drive_folder_ids"}

    def prepare_field_value(self, field_name, field, value, value_is_complex):
        if field_name in self._CSV_FIELDS and isinstance(value, str):
            return [s.strip() for s in value.split(",") if s.strip()]
        return super().prepare_field_value(field_name, field, value, value_is_complex)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_client_id: str
    google_client_secret: str
    pinecone_api_key: str
    pinecone_index_name: str = "buddy-index"
    gemini_api_key: str
    drive_folder_ids: list[str]
    sync_on_startup: bool = True

    gemini_daily_requests: int = 1000
    gemini_daily_tokens: int = 500000
    pinecone_max_vectors: int = 80000

    supermemory_api_key: str = ""
    supermemory_container_tag: str = "buddy-default"

    usage_file_path: str = "data/usage.json"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            _CsvEnvSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )


settings = Settings()

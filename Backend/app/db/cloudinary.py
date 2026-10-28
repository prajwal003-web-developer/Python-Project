import cloudinary
from pydantic_settings import BaseSettings, SettingsConfigDict


class CloudinarySettings(BaseSettings):
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


cloudinary_settings = CloudinarySettings()

cloudinary.config(
    cloud_name=cloudinary_settings.CLOUDINARY_CLOUD_NAME,
    api_key=cloudinary_settings.CLOUDINARY_API_KEY,
    api_secret=cloudinary_settings.CLOUDINARY_API_SECRET,
    secure=True,
)
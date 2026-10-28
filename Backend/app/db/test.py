import cloudinary
import cloudinary.api

from app.db.cloudinary import cloudinary_settings

try:
    result = cloudinary.api.ping()
    print("Cloudinary connection successful!")
    print(result)
except Exception as e:
    print("Cloudinary connection failed:")
    print(type(e).__name__, str(e))
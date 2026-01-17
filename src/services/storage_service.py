"""File storage management service"""

from datetime import datetime, timedelta
from pathlib import Path

from fastapi import UploadFile

from src.config import get_settings

settings = get_settings()


class StorageService:
    """Manage file storage and cleanup"""

    @staticmethod
    async def save_file(file: UploadFile, directory: Path, filename: str) -> str:
        """
        Save uploaded file and return path

        Args:
            file: Uploaded file object
            directory: Target directory
            filename: Target filename

        Returns:
            File path as string
        """
        # Ensure directory exists
        directory.mkdir(parents=True, exist_ok=True)

        # Full file path
        file_path = directory / filename

        # Save file in chunks
        with open(file_path, "wb") as f:
            while chunk := await file.read(8192):  # 8KB chunks
                f.write(chunk)

        return str(file_path)

    @staticmethod
    def cleanup_old_files(directory: Path, max_age_hours: int = 24) -> int:
        """
        Remove old files to prevent storage overflow

        Args:
            directory: Directory to clean up
            max_age_hours: Maximum file age in hours

        Returns:
            Number of files deleted
        """
        if not directory.exists():
            return 0

        max_age = datetime.now() - timedelta(hours=max_age_hours)
        deleted_count = 0

        for file_path in directory.glob("*"):
            if file_path.is_file():
                # Get file modification time
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                # Delete if too old
                if mtime < max_age:
                    file_path.unlink()
                    deleted_count += 1

        return deleted_count

    @staticmethod
    def get_file_size(path: Path) -> int:
        """
        Get file size in bytes

        Args:
            path: File path

        Returns:
            File size in bytes
        """
        return path.stat().st_size if path.exists() else 0

    @staticmethod
    def delete_file(path: Path) -> bool:
        """
        Delete a file if it exists

        Args:
            path: File path

        Returns:
            True if file was deleted, False otherwise
        """
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False

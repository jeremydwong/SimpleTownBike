import os
import json
from datetime import datetime
import dropbox
from dropbox.exceptions import ApiError, AuthError
import logging

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self):
        try:
            self.dbx = dropbox.Dropbox(os.environ['DROPBOX_ACCESS_TOKEN'])
            self._ensure_base_directory()
        except (AuthError, KeyError) as e:
            logger.error(f"Dropbox authentication error: {str(e)}")
            self.dbx = None

    def _ensure_base_directory(self):
        """Ensure the base directory exists in Dropbox."""
        if not self.dbx:
            return False
        try:
            self.dbx.files_list_folder('/workouts')
        except ApiError as e:
            if e.error.is_path() and e.error.get_path().is_not_found():
                try:
                    self.dbx.files_create_folder_v2('/workouts')
                except ApiError as folder_error:
                    logger.error(f"Failed to create workouts folder: {str(folder_error)}")
                    return False
        return True

    def is_authenticated(self) -> bool:
        """Check if Dropbox client is properly authenticated."""
        return self.dbx is not None

    def save_workout_data(self, metrics: dict) -> bool:
        """
        Save workout metrics data to Dropbox.
        
        Args:
            metrics: Dictionary containing workout metrics data
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        if not self.is_authenticated():
            logger.error("Dropbox client is not authenticated")
            return False

        try:
            # Create a timestamp for the filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"/workouts/workout_{timestamp}.json"

            # Prepare workout data
            workout_data = {
                'timestamp': timestamp,
                'metrics': {}
            }

            # Process each metric
            for metric_name, metric_data in metrics.items():
                if metric_data['values'] and metric_data['timestamps']:
                    workout_data['metrics'][metric_name] = {
                        'values': metric_data['values'],
                        'timestamps': metric_data['timestamps']
                    }

            # Convert to JSON string
            json_data = json.dumps(workout_data, indent=2)

            # Upload to Dropbox
            self.dbx.files_upload(
                json_data.encode('utf-8'),
                filename,
                mode=dropbox.files.WriteMode.overwrite
            )

            logger.info(f"Successfully saved workout data to {filename}")
            return True

        except ApiError as e:
            logger.error(f"Dropbox API error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error saving workout data: {str(e)}")
            return False

    def list_workouts(self) -> list:
        """
        List all saved workout files.
        
        Returns:
            list: List of workout files information
        """
        if not self.is_authenticated():
            logger.error("Dropbox client is not authenticated")
            return []

        try:
            result = self.dbx.files_list_folder('/workouts')
            workouts = []
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    workouts.append({
                        'name': entry.name,
                        'path': entry.path_display,
                        'modified': entry.client_modified
                    })
            return sorted(workouts, key=lambda x: x['modified'], reverse=True)
        except ApiError as e:
            logger.error(f"Dropbox API error: {str(e)}")
            return []

    def get_workout(self, file_path: str) -> dict:
        """
        Retrieve a specific workout file.
        
        Args:
            file_path: Path to the workout file in Dropbox
            
        Returns:
            dict: Workout data or empty dict if error occurs
        """
        if not self.is_authenticated():
            logger.error("Dropbox client is not authenticated")
            return {}

        try:
            _, response = self.dbx.files_download(file_path)
            return json.loads(response.content)
        except ApiError as e:
            logger.error(f"Dropbox API error: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error retrieving workout data: {str(e)}")
            return {}

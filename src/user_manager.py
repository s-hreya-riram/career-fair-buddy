"""
User management for multi-user support
Handles user ID generation, data storage, and interactions
"""
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .config import Config
from .utils import format_file_size


class UserManager:
    """Manages user data and interactions"""
    
    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id or self.generate_user_id()
        self.user_data_file = Path(f"{Config.USER_DATA_PREFIX}{self.user_id}.json")
        self.user_data = self._load_user_data()
    
    @staticmethod
    def generate_user_id() -> str:
        """Generate a unique 8-character user ID"""
        return str(uuid.uuid4())[:8]
    
    def _load_user_data(self) -> Dict[str, Any]:
        """Load user interaction data from file"""
        try:
            if self.user_data_file.exists():
                with open(self.user_data_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load user data: {e}")
        return {}
    
    def _save_user_data(self) -> bool:
        """Save user interaction data to file"""
        try:
            with open(self.user_data_file, 'w') as f:
                json.dump(self.user_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error: Could not save user data: {e}")
            return False
    
    def get_interaction(self, booth_number: str) -> Dict[str, Any]:
        """Get user interaction data for a specific booth"""
        data = self.user_data.get(booth_number, {})
        # Ensure all fields are present with defaults
        return {
            'visited': data.get('visited', False),
            'resume_shared': data.get('resume_shared', False),
            'apply_online': data.get('apply_online', False),
            'interested': data.get('interested', False),
            'comments': data.get('comments', '')
        }
    
    def update_interaction(
        self, 
        booth_number: str, 
        visited: Optional[bool] = None,
        resume_shared: Optional[bool] = None,
        apply_online: Optional[bool] = None,
        interested: Optional[bool] = None,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update user interaction data for a specific booth"""
        if booth_number not in self.user_data:
            self.user_data[booth_number] = {
                'visited': False,
                'resume_shared': False,
                'apply_online': False,
                'interested': False,
                'comments': '',
                'last_updated': datetime.now().isoformat()
            }
        
        # Update only the provided fields
        if visited is not None:
            self.user_data[booth_number]['visited'] = visited
        if resume_shared is not None:
            self.user_data[booth_number]['resume_shared'] = resume_shared
        if apply_online is not None:
            self.user_data[booth_number]['apply_online'] = apply_online
        if interested is not None:
            self.user_data[booth_number]['interested'] = interested
        if comments is not None:
            self.user_data[booth_number]['comments'] = comments
        
        # Update timestamp
        self.user_data[booth_number]['last_updated'] = datetime.now().isoformat()
        
        self._save_user_data()
        return self.user_data[booth_number]
    
    def get_user_summary(self) -> Dict[str, Any]:
        """Get summary of user interactions"""
        total_booths = len(self.user_data)
        visited_count = sum(1 for data in self.user_data.values() if data.get('visited', False))
        interested_count = sum(1 for data in self.user_data.values() if data.get('interested', False))
        resume_shared_count = sum(1 for data in self.user_data.values() if data.get('resume_shared', False))
        apply_online_count = sum(1 for data in self.user_data.values() if data.get('apply_online', False))
        
        return {
            'user_id': self.user_id,
            'total_interactions': total_booths,
            'visited_booths': visited_count,
            'interested_booths': interested_count,
            'resumes_shared': resume_shared_count,
            'online_applications': apply_online_count,
            'data_file': str(self.user_data_file),
            'file_exists': self.user_data_file.exists()
        }
    
    def export_to_csv(self) -> str:
        """Export user data to CSV format"""
        if not self.user_data:
            return "booth_number,visited,resume_shared,apply_online,interested,comments,last_updated\n"
        
        csv_lines = ["booth_number,visited,resume_shared,apply_online,interested,comments,last_updated"]
        
        for booth_number, data in self.user_data.items():
            line = f"{booth_number},{data.get('visited', False)},{data.get('resume_shared', False)}," \
                   f"{data.get('apply_online', False)},{data.get('interested', False)}," \
                   f"\"{data.get('comments', '')}\",{data.get('last_updated', '')}"
            csv_lines.append(line)
        
        return "\n".join(csv_lines)
    
    def get_interested_booths(self) -> List[str]:
        """Get list of booth numbers marked as interested"""
        return [
            booth_number for booth_number, data in self.user_data.items()
            if data.get('interested', False)
        ]
    
    def get_visited_booths(self) -> List[str]:
        """Get list of booth numbers marked as visited"""
        return [
            booth_number for booth_number, data in self.user_data.items()
            if data.get('visited', False)
        ]
    
    @staticmethod
    def get_all_user_files() -> List[Path]:
        """Get all user data files"""
        user_files = []
        for file_path in Path('.').glob(f"{Config.USER_DATA_PREFIX}*.json"):
            user_files.append(file_path)
        return user_files
    
    @staticmethod
    def get_active_users(hours: int = 24) -> List[str]:
        """Get list of users active within the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        active_users = []
        
        for user_file in UserManager.get_all_user_files():
            try:
                # Check file modification time
                if datetime.fromtimestamp(user_file.stat().st_mtime) > cutoff_time:
                    # Extract user ID from filename
                    user_id = user_file.stem.replace(Config.USER_DATA_PREFIX, '')
                    active_users.append(user_id)
            except Exception:
                continue
        
        return active_users
    
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get system-wide user metrics"""
        user_files = UserManager.get_all_user_files()
        total_users = len(user_files)
        active_users = UserManager.get_active_users(Config.ACTIVITY_WINDOW_HOURS)
        
        # Calculate total storage
        total_storage = sum(
            file_path.stat().st_size 
            for file_path in user_files 
            if file_path.exists()
        )
        
        # Performance warnings
        warnings = []
        if total_users > Config.MAX_USERS_WARNING:
            warnings.append(f"High user count: {total_users} users (recommended max: {Config.MAX_USERS_WARNING})")
        
        storage_mb = total_storage / (1024 * 1024)
        if storage_mb > Config.MAX_STORAGE_WARNING_MB:
            warnings.append(f"High storage usage: {storage_mb:.1f}MB (recommended max: {Config.MAX_STORAGE_WARNING_MB}MB)")
        
        return {
            'total_users': total_users,
            'active_users_24h': len(active_users),
            'total_storage_bytes': total_storage,
            'total_storage_formatted': format_file_size(total_storage),
            'storage_mb': round(storage_mb, 1),
            'warnings': warnings,
            'performance_ok': len(warnings) == 0
        }
    
    def cleanup_old_data(self, days: int = 7) -> int:
        """Clean up user data older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        for user_file in self.get_all_user_files():
            try:
                if datetime.fromtimestamp(user_file.stat().st_mtime) < cutoff_time:
                    user_file.unlink()
                    cleaned_count += 1
            except Exception:
                continue
        
        return cleaned_count

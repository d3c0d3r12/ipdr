"""
Background Task Manager - Run IP Lookups in Background
Allows browser to close, screen to turn off, and resume capability
"""
import asyncio
import uuid
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """Manage background IP lookup tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
    
    def create_task(self, run_dir: Path, ips: List[str], resume: bool = False) -> str:
        """
        Create a new background task
        
        Args:
            run_dir: Directory for this investigation
            ips: List of IP addresses to lookup
            resume: Whether this is resuming a previous task
            
        Returns:
            task_id: Unique identifier for this task
        """
        task_id = str(uuid.uuid4())
        
        task_info = {
            'task_id': task_id,
            'run_dir': str(run_dir),
            'total_ips': len(ips),
            'completed_ips': 0,
            'status': 'pending',
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'started_at': None,
            'completed_at': None,
            'error': None,
            'resume': resume
        }
        
        self.tasks[task_id] = task_info
        
        logger.info(f"Task created: {task_id} ({len(ips)} IPs, resume={resume})")
        
        return task_id
    
    def update_task(self, task_id: str, **kwargs):
        """
        Update task information
        
        Args:
            task_id: Task identifier
            **kwargs: Fields to update
        """
        if task_id in self.tasks:
            self.tasks[task_id].update(kwargs)
            
            # Calculate progress percentage
            if 'completed_ips' in kwargs and 'total_ips' in self.tasks[task_id]:
                total = self.tasks[task_id]['total_ips']
                completed = kwargs['completed_ips']
                if total > 0:
                    self.tasks[task_id]['progress'] = round((completed / total) * 100, 2)
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """
        Get task information
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task information dictionary or None
        """
        return self.tasks.get(task_id)
    
    def mark_started(self, task_id: str):
        """Mark task as started"""
        self.update_task(
            task_id,
            status='running',
            started_at=datetime.now().isoformat()
        )
        logger.info(f"Task started: {task_id}")
    
    def mark_completed(self, task_id: str):
        """Mark task as completed"""
        self.update_task(
            task_id,
            status='completed',
            completed_at=datetime.now().isoformat(),
            progress=100
        )
        logger.info(f"Task completed: {task_id}")
    
    def mark_failed(self, task_id: str, error: str):
        """Mark task as failed"""
        self.update_task(
            task_id,
            status='failed',
            error=error,
            completed_at=datetime.now().isoformat()
        )
        logger.error(f"Task failed: {task_id} - {error}")
    
    def update_progress(self, task_id: str, completed: int):
        """Update task progress"""
        self.update_task(task_id, completed_ips=completed)
    
    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks"""
        return list(self.tasks.values())
    
    def get_active_tasks(self) -> List[Dict]:
        """Get all active (running or pending) tasks"""
        return [
            task for task in self.tasks.values()
            if task['status'] in ['pending', 'running']
        ]
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """
        Remove old completed tasks
        
        Args:
            max_age_hours: Maximum age in hours to keep tasks
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for task_id, task in self.tasks.items():
            if task['status'] in ['completed', 'failed']:
                completed_at = task.get('completed_at')
                if completed_at:
                    completed_time = datetime.fromisoformat(completed_at)
                    if completed_time < cutoff:
                        to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
            logger.info(f"Cleaned up old task: {task_id}")


# Global task manager instance
task_manager = BackgroundTaskManager()

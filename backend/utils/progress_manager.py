import csv
import json as _json
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

_RESULT_FIELDS = [
    'ip', 'occurrences', 'first_seen', 'last_seen', 'ip_type',
    'isp', 'organization', 'country', 'region', 'city',
    'latitude', 'longitude', 'timezone', 'postal_code', 'source', 'whois',
]


class ProgressManager:
    """Manage IP lookup progress with auto-save and resume capability"""

    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.progress_file = self.run_dir / 'progress.json'
        self.results_file = self.run_dir / 'ip_lookup_results.csv'
        self.temp_results_file = self.run_dir / 'ip_lookup_results_temp.csv'

    def save_progress(self, completed: int, total: int, current_ip: str = None):
        try:
            progress = {
                'completed': completed,
                'total': total,
                'percentage': round((completed / total) * 100, 2) if total > 0 else 0,
                'current_ip': current_ip,
                'last_updated': datetime.now().isoformat(),
                'status': 'in_progress' if completed < total else 'completed',
            }
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                _json.dump(progress, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving progress: {e}")

    def load_progress(self) -> Dict:
        try:
            if self.progress_file.exists():
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return _json.load(f)
        except Exception as e:
            logger.error(f"Error loading progress: {e}")
        return {'completed': 0, 'total': 0, 'percentage': 0, 'status': 'not_started'}

    def save_result(self, result: Dict):
        """Append a single result row."""
        self.save_results_batch([result])

    def save_results_batch(self, results: List[Dict]):
        """Append results to CSV using csv module — fast even for large batches."""
        if not results:
            return
        try:
            file_exists = self.results_file.exists()
            with open(self.results_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=_RESULT_FIELDS, extrasaction='ignore')
                if not file_exists:
                    writer.writeheader()
                for row in results:
                    flat = {}
                    for k in _RESULT_FIELDS:
                        v = row.get(k)
                        if isinstance(v, (dict, list)):
                            flat[k] = _json.dumps(v, ensure_ascii=False)
                        else:
                            flat[k] = v
                    writer.writerow(flat)
            logger.info(f"Batch saved: {len(results)} results")
        except Exception as e:
            logger.error(f"Error saving batch results: {e}")

    def get_results_count(self) -> int:
        """Fast row count — reads only line counts, no data loading."""
        if not self.results_file.exists():
            return 0
        try:
            with open(self.results_file, 'rb') as f:
                lines = sum(1 for _ in f)
            return max(0, lines - 1)  # subtract header row
        except Exception as e:
            logger.error(f"Error counting results: {e}")
            return 0

    def get_results_paginated(self, offset: int = 0, limit: int = 100) -> List[Dict]:
        """Read only the requested rows — does not load full file into memory."""
        if not self.results_file.exists():
            return []
        try:
            skip = list(range(1, offset + 1)) if offset > 0 else None
            df = pd.read_csv(
                self.results_file,
                encoding='utf-8',
                skiprows=skip,
                nrows=limit,
            )
            import math
            records = df.to_dict('records')
            cleaned = []
            for r in records:
                row = {}
                for k, v in r.items():
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        row[k] = None
                    else:
                        row[k] = v
                cleaned.append(row)
            return cleaned
        except Exception as e:
            logger.error(f"Error reading paginated results: {e}")
            return []

    def get_completed_ips(self) -> List[str]:
        try:
            if self.results_file.exists():
                df = pd.read_csv(self.results_file, encoding='utf-8', usecols=['ip'])
                if 'ip' in df.columns:
                    return df['ip'].dropna().tolist()
        except Exception as e:
            logger.error(f"Error reading completed IPs: {e}")
        return []

    def get_remaining_ips(self, all_ips: List[str]) -> List[str]:
        completed_ips = set(self.get_completed_ips())
        return [ip for ip in all_ips if ip not in completed_ips]

    def can_resume(self) -> bool:
        progress = self.load_progress()
        return (
            progress['status'] == 'in_progress'
            and progress['completed'] < progress['total']
            and progress['completed'] > 0
        )

    def get_results(self) -> List[Dict]:
        """Load all results — use only for exports (PDF/JSON), not for display."""
        try:
            if self.results_file.exists():
                df = pd.read_csv(self.results_file, encoding='utf-8')
                return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error reading results: {e}")
        return []

    def mark_complete(self):
        try:
            progress = self.load_progress()
            progress['status'] = 'completed'
            progress['completed'] = progress['total']
            progress['percentage'] = 100
            progress['last_updated'] = datetime.now().isoformat()
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                _json.dump(progress, f, indent=2)
        except Exception as e:
            logger.error(f"Error marking complete: {e}")

    def reset(self):
        try:
            if self.progress_file.exists():
                self.progress_file.unlink()
            if self.results_file.exists():
                self.results_file.unlink()
        except Exception as e:
            logger.error(f"Error resetting progress: {e}")

    def get_summary(self) -> Dict:
        progress = self.load_progress()
        return {
            'total_ips': progress.get('total', 0),
            'completed_ips': progress.get('completed', 0),
            'remaining_ips': progress.get('total', 0) - progress.get('completed', 0),
            'percentage': progress.get('percentage', 0),
            'status': progress.get('status', 'unknown'),
            'last_updated': progress.get('last_updated'),
            'can_resume': self.can_resume(),
            'results_count': self.get_results_count(),
        }

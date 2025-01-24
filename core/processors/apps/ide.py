from typing import Dict, List, Optional
from datetime import datetime
import psutil
from pathlib import Path
from clarity.schemas.apps import IDEActivity, IDEType, CodeFile
from clarity.utils.monitoring.metrics import ide_activity_counter
import structlog

logger = structlog.get_logger()

class IDEProcessor:
    """
    Processes IDE activity data including active projects,
    file operations, and coding patterns.
    """
    
    IDE_PROCESSES = {
        "code": IDEType.VSCODE,
        "pycharm": IDEType.PYCHARM,
        "intellij": IDEType.INTELLIJ,
        "android studio": IDEType.ANDROID_STUDIO,
        "sublime_text": IDEType.SUBLIME
    }
    
    def __init__(self):
        self.language_extensions = {
            "py": "Python",
            "js": "JavaScript",
            "ts": "TypeScript",
            "java": "Java",
            "cpp": "C++",
            "rs": "Rust",
            "go": "Go",
            "rb": "Ruby"
        }
        
        # Mapping of IDEs to their config/workspace paths
        self.ide_paths = {
            IDEType.VSCODE: "~/.config/Code/User/workspaceStorage",
            IDEType.PYCHARM: "~/.PyCharm*/system",
            IDEType.INTELLIJ: "~/.IntelliJIdea*/system",
            IDEType.SUBLIME: "~/.config/sublime-text/Local"
        }

    async def collect_activity(self) -> IDEActivity:
        """Collect current IDE activity data."""
        try:
            active_ides = self._get_active_ides()
            active_files = self._get_active_files()
            workspace_info = self._get_workspace_info()
            
            ide_activity_counter.inc(len(active_files))
            
            return IDEActivity(
                timestamp=datetime.utcnow(),
                active_ides=active_ides,
                active_files=active_files,
                workspace_info=workspace_info,
                language_stats=self._calculate_language_stats(active_files)
            )
            
        except Exception as e:
            logger.error("ide.collection_failed", error=str(e))
            raise

    def _get_active_ides(self) -> List[Dict]:
        """Identify active IDE processes."""
        active_ides = []
        
        for proc in psutil.process_iter(['name', 'pid', 'cpu_percent', 'memory_info']):
            try:
                proc_name = proc.info['name'].lower()
                for ide_name, ide_type in self.IDE_PROCESSES.items():
                    if ide_name in proc_name:
                        active_ides.append({
                            'type': ide_type,
                            'pid': proc.info['pid'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_mb': proc.info['memory_info'].rss / (1024 * 1024)
                        })
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return active_ides

    def _get_active_files(self) -> List[CodeFile]:
        """Get information about currently open files."""
        active_files = []
        
        for ide_type, path_pattern in self.ide_paths.items():
            try:
                path = Path(path_pattern).expanduser()
                if path.exists():
                    # Read workspace/project files
                    for workspace in path.glob("*/workspace.json"):
                        with open(workspace) as f:
                            data = f.read()
                            files = self._parse_workspace_files(data)
                            active_files.extend([
                                CodeFile(
                                    path=file,
                                    language=self._detect_language(file),
                                    ide_type=ide_type,
                                    last_modified=datetime.fromtimestamp(
                                        Path(file).stat().st_mtime
                                    )
                                )
                                for file in files
                            ])
            except Exception as e:
                logger.error(
                    "ide.file_detection_failed",
                    ide=ide_type.value,
                    error=str(e)
                )
        
        return active_files

    def _get_workspace_info(self) -> Dict:
        """Get information about current workspace/project."""
        workspace_info = {
            'project_count': 0,
            'total_files': 0,
            'languages': set()
        }
        
        for ide_type, path_pattern in self.ide_paths.items():
            try:
                path = Path(path_pattern).expanduser()
                if path.exists():
                    projects = list(path.glob("*/"))
                    workspace_info['project_count'] += len(projects)
                    
                    for project in projects:
                        files = list(project.rglob("*"))
                        workspace_info['total_files'] += len(files)
                        workspace_info['languages'].update(
                            self._detect_language(f) for f in files
                        )
            except Exception:
                continue
        
        workspace_info['languages'] = list(workspace_info['languages'] - {None})
        return workspace_info

    def _calculate_language_stats(self, files: List[CodeFile]) -> Dict[str, int]:
        """Calculate statistics about programming languages used."""
        language_counts = {}
        
        for file in files:
            if file.language:
                language_counts[file.language] = language_counts.get(file.language, 0) + 1
        
        return language_counts

    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lstrip('.')
        return self.language_extensions.get(ext)

    def _parse_workspace_files(self, workspace_data: str) -> List[str]:
        """Parse workspace configuration to find open files."""
        try:
            import json
            data = json.loads(workspace_data)
            files = []
            
            # Extract files from workspace data structure
            # Format varies by IDE, this is a simplified version
            if 'files' in data:
                files.extend(data['files'])
            elif 'recentFiles' in data:
                files.extend(data['recentFiles'])
            
            return files
        except Exception:
            return []

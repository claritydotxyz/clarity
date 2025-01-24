from typing import Dict, Optional
from datetime import datetime
import subprocess
import psutil
import structlog

logger = structlog.get_logger()

class TerminalProcessor:
    """Processes terminal/shell activity data."""
    
    def __init__(self):
        self.shell_commands = set()
        self.active_processes = {}

    async def collect_activity(self) -> Dict:
        """Collect current terminal activity data."""
        try:
            processes = self._get_terminal_processes()
            commands = self._get_recent_commands()
            
            return {
                "timestamp": datetime.utcnow(),
                "active_terminals": len(processes),
                "processes": processes,
                "recent_commands": commands,
                "shell_type": self._get_shell_type()
            }
            
        except Exception as e:
            logger.error("terminal.collection_failed", error=str(e))
            raise

    def _get_terminal_processes(self) -> List[Dict]:
        """Get information about running terminal processes."""
        terminals = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if self._is_terminal_process(proc.info):
                    terminals.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "command": " ".join(proc.info['cmdline'] or []),
                        "cpu_percent": proc.cpu_percent(),
                        "memory_percent": proc.memory_percent()
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return terminals

    def _get_recent_commands(self) -> List[str]:
        """Get recently executed shell commands."""
        try:
            history_file = self._get_history_file()
            if history_file and os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    return f.readlines()[-50:]  # Last 50 commands
        except Exception:
            return []
        return []

    def _get_shell_type(self) -> str:
        """Determine the current shell type."""
        shell = os.environ.get('SHELL', '')
        if 'bash' in shell:
            return 'bash'
        elif 'zsh' in shell:
            return 'zsh'
        elif 'fish' in shell:
            return 'fish'
        return 'unknown'

    @staticmethod
    def _is_terminal_process(proc_info: Dict) -> bool:
        """Check if a process is a terminal emulator."""
        terminal_names = {'gnome-terminal', 'konsole', 'xterm', 'terminal',
                         'iTerm', 'Terminal', 'cmd.exe', 'powershell'}
        return proc_info['name'] in terminal_names

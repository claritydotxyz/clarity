from typing import Dict, List, Optional
from datetime import datetime
import psutil
import browser_history
from clarity.schemas.apps import BrowserActivity, BrowserType, TabInfo
from clarity.utils.monitoring.metrics import browser_data_counter
import structlog

logger = structlog.get_logger()

class BrowserProcessor:
    """
    Processes browser activity data including active tabs,
    browsing history, and resource usage.
    """
    
    BROWSER_PROCESSES = {
        "chrome": BrowserType.CHROME,
        "firefox": BrowserType.FIREFOX,
        "msedge": BrowserType.EDGE,
        "safari": BrowserType.SAFARI,
        "brave": BrowserType.BRAVE
    }

    def __init__(self):
        self.productivity_domains = {
            "github.com": 0.9,
            "stackoverflow.com": 0.8,
            "docs.python.org": 0.9,
            "linkedin.com": 0.6,
            "mail.google.com": 0.7
        }
        self.distraction_domains = {
            "twitter.com": 0.2,
            "facebook.com": 0.2,
            "instagram.com": 0.1,
            "reddit.com": 0.3,
            "youtube.com": 0.4
        }

    async def collect_activity(self) -> BrowserActivity:
        """Collect current browser activity data."""
        try:
            active_browsers = self._get_active_browsers()
            active_tabs = await self._get_active_tabs()
            resource_usage = self._get_resource_usage(active_browsers)
            
            browser_data_counter.inc(len(active_tabs))
            
            return BrowserActivity(
                timestamp=datetime.utcnow(),
                active_browsers=active_browsers,
                active_tabs=active_tabs,
                resource_usage=resource_usage,
                productivity_score=self._calculate_productivity_score(active_tabs)
            )
            
        except Exception as e:
            logger.error("browser.collection_failed", error=str(e))
            raise

    def _get_active_browsers(self) -> List[Dict]:
        """Identify active browser processes."""
        active_browsers = []
        
        for proc in psutil.process_iter(['name', 'pid', 'cpu_percent', 'memory_info']):
            try:
                proc_name = proc.info['name'].lower()
                for browser_name, browser_type in self.BROWSER_PROCESSES.items():
                    if browser_name in proc_name:
                        active_browsers.append({
                            'type': browser_type,
                            'pid': proc.info['pid'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_mb': proc.info['memory_info'].rss / (1024 * 1024)
                        })
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return active_browsers

    async def _get_active_tabs(self) -> List[TabInfo]:
        """Get information about active browser tabs."""
        active_tabs = []
        
        try:
            browsers = browser_history.get_browsers()
            for browser in browsers:
                if browser.profile_support:
                    tabs = await browser.fetch_active_tabs()
                    active_tabs.extend([
                        TabInfo(
                            url=tab.url,
                            title=tab.title,
                            browser_type=self._identify_browser_type(browser.name),
                            domain=self._extract_domain(tab.url),
                            productivity_score=self._get_domain_score(tab.url)
                        )
                        for tab in tabs
                    ])
        except Exception as e:
            logger.error("browser.tab_fetch_failed", error=str(e))
        
        return active_tabs

    def _get_resource_usage(self, active_browsers: List[Dict]) -> Dict:
        """Calculate aggregate browser resource usage."""
        return {
            'total_cpu_percent': sum(b['cpu_percent'] for b in active_browsers),
            'total_memory_mb': sum(b['memory_mb'] for b in active_browsers),
            'browser_count': len(active_browsers)
        }

    def _calculate_productivity_score(self, tabs: List[TabInfo]) -> float:
        """Calculate overall productivity score based on active tabs."""
        if not tabs:
            return 0.0
            
        total_score = sum(tab.productivity_score for tab in tabs)
        return total_score / len(tabs)

    def _get_domain_score(self, url: str) -> float:
        """Get productivity score for a domain."""
        domain = self._extract_domain(url)
        
        if domain in self.productivity_domains:
            return self.productivity_domains[domain]
        elif domain in self.distraction_domains:
            return self.distraction_domains[domain]
        return 0.5  # Neutral score for unknown domains

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.lower()
        except:
            return ""

    @staticmethod
    def _identify_browser_type(browser_name: str) -> BrowserType:
        """Map browser name to BrowserType enum."""
        browser_map = {
            "Chrome": BrowserType.CHROME,
            "Firefox": BrowserType.FIREFOX,
            "Safari": BrowserType.SAFARI,
            "Edge": BrowserType.EDGE,
            "Brave": BrowserType.BRAVE
        }
        return browser_map.get(browser_name, BrowserType.OTHER)

"""
Real-time Date Service for HWAgent
Gets actual current date from web sources instead of relying on system date.
"""

import re
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from hwagent.core.constants import Constants


class RealDateService:
    """Service to get actual current date from web sources"""
    
    def __init__(self, api_key: str | None = None):
        """Initialize with optional API key for web search"""
        self.api_key = api_key
        self.cached_date: Optional[datetime] = None
        self.cache_timestamp: Optional[datetime] = None
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
        
    def get_current_date(self, force_refresh: bool = False) -> datetime:
        """Get actual current date, using cache if recent"""
        
        # Use cache if available and recent
        if (not force_refresh and 
            self.cached_date and 
            self.cache_timestamp and 
            datetime.now() - self.cache_timestamp < self.cache_duration):
            return self.cached_date
        
        # Try multiple methods to get current date
        current_date = self._get_date_from_web()
        
        if current_date:
            self.cached_date = current_date
            self.cache_timestamp = datetime.now()
            return current_date
        
        # Fallback to system date with warning
        print("⚠️ WARNING: Could not get real current date from web, using system date")
        return datetime.now()
    
    def _get_date_from_web(self) -> Optional[datetime]:
        """Get current date from web sources"""
        
        # Method 1: Try web search for "what is today's date"
        if self.api_key:
            try:
                search_date = self._search_for_current_date()
                if search_date:
                    return search_date
            except Exception as e:
                print(f"Web search for date failed: {e}")
        
        # Method 2: Try world clock APIs (free, no key needed)
        try:
            api_date = self._get_date_from_api()
            if api_date:
                return api_date
        except Exception as e:
            print(f"API date fetch failed: {e}")
        
        # Method 3: Try HTTP headers from major sites
        try:
            header_date = self._get_date_from_headers()
            if header_date:
                return header_date
        except Exception as e:
            print(f"Header date fetch failed: {e}")
        
        return None
    
    def _search_for_current_date(self) -> Optional[datetime]:
        """Use web search to find current date"""
        if not self.api_key:
            return None
            
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "query": "what is today's date current date today",
                "freshness": "oneWeek",
                "summary": True,
                "count": 3
            }
            
            response = requests.post(
                "https://api.langsearch.io/web/search",
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('data', {}).get('webPages', {}).get('value', [])
                
                for result in results:
                    content = f"{result.get('name', '')} {result.get('snippet', '')} {result.get('summary', '')}"
                    date_match = self._extract_date_from_text(content)
                    if date_match:
                        return date_match
        except Exception as e:
            print(f"Search date extraction failed: {e}")
        
        return None
    
    def _get_date_from_api(self) -> Optional[datetime]:
        """Get date from time API services"""
        
        # Try multiple free time APIs
        apis = [
            "http://worldtimeapi.org/api/timezone/UTC",
            "https://timeapi.io/api/Time/current/zone?timeZone=UTC",
            "http://worldclockapi.com/api/json/utc/now"
        ]
        
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Different APIs have different formats
                    if 'datetime' in data:  # worldtimeapi.org
                        date_str = data['datetime'][:19]  # Take only YYYY-MM-DDTHH:MM:SS
                        return datetime.fromisoformat(date_str)
                    elif 'dateTime' in data:  # timeapi.io
                        date_str = data['dateTime'][:19]
                        return datetime.fromisoformat(date_str)
                    elif 'currentDateTime' in data:  # worldclockapi.com
                        date_str = data['currentDateTime'][:19]
                        return datetime.fromisoformat(date_str)
                        
            except Exception:
                continue  # Try next API
                
        return None
    
    def _get_date_from_headers(self) -> Optional[datetime]:
        """Get date from HTTP response headers"""
        
        # Try major sites that should have accurate server dates
        sites = [
            "https://www.google.com",
            "https://www.github.com", 
            "https://www.stackoverflow.com"
        ]
        
        for site in sites:
            try:
                response = requests.head(site, timeout=5)
                date_header = response.headers.get('Date')
                if date_header:
                    # Parse HTTP date format: "Fri, 31 May 2025 20:41:35 GMT"
                    date_obj = datetime.strptime(date_header, '%a, %d %b %Y %H:%M:%S %Z')
                    return date_obj
            except Exception:
                continue  # Try next site
                
        return None
    
    def _extract_date_from_text(self, text: str) -> Optional[datetime]:
        """Extract date from text content"""
        
        # Common date patterns
        patterns = [
            # Format: "May 31, 2025" or "31 May 2025"
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',
            # Format: "2025-05-31"
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            # Format: "31/05/2025" or "05/31/2025"
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
        ]
        
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
            'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 
            'oct': 10, 'nov': 11, 'dec': 12
        }
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    if len(match) == 3:
                        # Check if first element is month name
                        if match[0] in months:
                            month = months[match[0]]
                            day = int(match[1])
                            year = int(match[2])
                        else:
                            # Assume it's numeric format
                            if '-' in text:  # YYYY-MM-DD
                                year, month, day = int(match[0]), int(match[1]), int(match[2])
                            else:  # MM/DD/YYYY or DD/MM/YYYY - assume MM/DD/YYYY for US sites
                                month, day, year = int(match[0]), int(match[1]), int(match[2])
                        
                        # Validate date
                        if 1 <= month <= 12 and 1 <= day <= 31 and year >= 2024:
                            return datetime(year, month, day)
                            
                except (ValueError, KeyError):
                    continue
        
        return None
    
    def get_date_info(self) -> Dict[str, str]:
        """Get comprehensive date information"""
        current_date = self.get_current_date()
        
        return {
            'current_date': current_date.strftime('%Y-%m-%d'),
            'current_year': str(current_date.year),
            'current_month': current_date.strftime('%B'),
            'current_month_year': current_date.strftime('%B %Y'),
            'current_iso': current_date.isoformat(),
            'current_day': current_date.strftime('%A'),
            'timestamp': current_date.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def is_date_current(self, year: int, month: Optional[int] = None) -> bool:
        """Check if given year/month is current"""
        current_date = self.get_current_date()
        
        if month is None:
            return year == current_date.year
        
        return year == current_date.year and month == current_date.month


# Global instance
_date_service: Optional[RealDateService] = None

def get_date_service(api_key: str | None = None) -> RealDateService:
    """Get or create global date service instance"""
    global _date_service
    
    if _date_service is None:
        _date_service = RealDateService(api_key)
    elif api_key and not _date_service.api_key:
        _date_service.api_key = api_key
        
    return _date_service

def get_real_current_date() -> datetime:
    """Quick function to get real current date"""
    return get_date_service().get_current_date()

def get_real_date_info() -> Dict[str, str]:
    """Quick function to get real date information"""
    return get_date_service().get_date_info() 
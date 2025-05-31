"""
Logical Analyzer for HWAgent
Provides intelligent analysis of search results and temporal context to help the agent
make better decisions about current vs historical information.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class TemporalInfo:
    """Information about temporal context of a result"""
    year: Optional[int] = None
    month: Optional[int] = None
    is_current: bool = False
    is_historical: bool = False
    is_transitional: bool = False  # Like elections, appointments, etc.
    confidence: float = 0.0  # 0-1 confidence in temporal classification
    indicators: List[str] = None
    
    def __post_init__(self):
        if self.indicators is None:
            self.indicators = []


class LogicalAnalyzer:
    """Analyzes search results for temporal context and logical consistency"""
    
    def __init__(self, current_date: datetime):
        self.current_date = current_date
        self.current_year = current_date.year
        self.current_month = current_date.month
        
        # Temporal keywords for analysis
        self.current_indicators = {
            'high': ['current', 'incumbent', 'serving', 'in office', 'as of', 'since', 'now'],
            'medium': ['latest', 'recent', 'new', 'updated', 'today'],
            'transition': ['elected', 'appointed', 'inaugurated', 'assumed office', 'took office']
        }
        
        self.historical_indicators = {
            'definitive': ['former', 'previous', 'ex-', 'until', 'ended', 'stepped down'],
            'temporal': ['was', 'served from', 'term ended', 'replaced by', 'succeeded by']
        }
        
        # Position types that commonly change
        self.changeable_positions = [
            'president', 'prime minister', 'chancellor', 'mayor', 'governor',
            'ceo', 'director', 'chairman', 'leader', 'head', 'minister',
            'speaker', 'chief', 'commander', 'secretary'
        ]
    
    def analyze_search_results(self, results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Analyze search results for temporal consistency and current information"""
        
        analysis = {
            'current_info': [],
            'historical_info': [],
            'conflicting_info': [],
            'temporal_analysis': {},
            'confidence_score': 0.0,
            'reasoning': [],
            'recommendations': []
        }
        
        # Analyze each result
        temporal_findings = []
        for i, result in enumerate(results):
            temporal_info = self._analyze_single_result(result, query)
            temporal_findings.append((i, temporal_info))
            
            if temporal_info.is_current:
                analysis['current_info'].append({
                    'index': i,
                    'result': result,
                    'temporal_info': temporal_info
                })
            elif temporal_info.is_historical:
                analysis['historical_info'].append({
                    'index': i,
                    'result': result,
                    'temporal_info': temporal_info
                })
        
        # Look for conflicts and inconsistencies
        conflicts = self._detect_conflicts(temporal_findings, query)
        analysis['conflicting_info'] = conflicts
        
        # Generate logical reasoning
        reasoning = self._generate_reasoning(temporal_findings, query)
        analysis['reasoning'] = reasoning
        
        # Calculate confidence
        analysis['confidence_score'] = self._calculate_confidence(temporal_findings)
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis, query)
        
        return analysis
    
    def _analyze_single_result(self, result: Dict[str, Any], query: str) -> TemporalInfo:
        """Analyze a single search result for temporal information"""
        
        content = f"{result.get('name', '')} {result.get('snippet', '')} {result.get('summary', '')}".lower()
        date_published = result.get('datePublished', '')
        
        temporal_info = TemporalInfo()
        
        # Check for current indicators
        current_score = 0
        historical_score = 0
        
        for level, indicators in self.current_indicators.items():
            for indicator in indicators:
                if indicator in content:
                    weight = {'high': 3, 'medium': 2, 'transition': 2}.get(level, 1)
                    current_score += weight
                    temporal_info.indicators.append(f"current:{indicator}")
        
        for level, indicators in self.historical_indicators.items():
            for indicator in indicators:
                if indicator in content:
                    weight = {'definitive': 3, 'temporal': 2}.get(level, 1)
                    historical_score += weight
                    temporal_info.indicators.append(f"historical:{indicator}")
        
        # Check publication date
        if date_published:
            pub_year = self._extract_year_from_date(date_published)
            if pub_year:
                temporal_info.year = pub_year
                if pub_year == self.current_year:
                    current_score += 2
                elif pub_year == self.current_year - 1:
                    current_score += 1
                elif pub_year < self.current_year - 1:
                    historical_score += 1
        
        # Check for year mentions in content
        year_mentions = re.findall(r'\b(20\d{2})\b', content)
        for year_str in year_mentions:
            year = int(year_str)
            if year == self.current_year:
                current_score += 1
            elif year < self.current_year:
                historical_score += 0.5
        
        # Determine classification
        if current_score > historical_score and current_score >= 2:
            temporal_info.is_current = True
            temporal_info.confidence = min(current_score / 5, 1.0)
        elif historical_score > current_score and historical_score >= 2:
            temporal_info.is_historical = True
            temporal_info.confidence = min(historical_score / 5, 1.0)
        else:
            temporal_info.confidence = 0.3  # Low confidence, unclear
        
        # Check for transitional events
        for indicator in self.current_indicators['transition']:
            if indicator in content:
                temporal_info.is_transitional = True
                break
        
        return temporal_info
    
    def _detect_conflicts(self, temporal_findings: List[Tuple[int, TemporalInfo]], query: str) -> List[Dict[str, Any]]:
        """Detect conflicts between different sources"""
        conflicts = []
        
        # Look for positions that might have changed
        query_lower = query.lower()
        is_position_query = any(pos in query_lower for pos in self.changeable_positions)
        
        if is_position_query:
            current_findings = [f for f in temporal_findings if f[1].is_current]
            historical_findings = [f for f in temporal_findings if f[1].is_historical]
            
            if current_findings and historical_findings:
                conflicts.append({
                    'type': 'current_vs_historical',
                    'description': 'Found both current and historical information for a position that may have changed',
                    'current_sources': len(current_findings),
                    'historical_sources': len(historical_findings),
                    'recommendation': 'Prioritize most recent sources and check for transition dates'
                })
        
        # Look for year conflicts
        years_mentioned = []
        for idx, temporal_info in temporal_findings:
            if temporal_info.year:
                years_mentioned.append(temporal_info.year)
        
        unique_years = set(years_mentioned)
        if len(unique_years) > 1 and max(unique_years) - min(unique_years) > 2:
            conflicts.append({
                'type': 'year_spread',
                'description': f'Information spans multiple years: {sorted(unique_years)}',
                'years': sorted(unique_years),
                'recommendation': 'Focus on most recent year information'
            })
        
        return conflicts
    
    def _generate_reasoning(self, temporal_findings: List[Tuple[int, TemporalInfo]], query: str) -> List[str]:
        """Generate logical reasoning about the temporal context"""
        reasoning = []
        
        current_count = sum(1 for _, info in temporal_findings if info.is_current)
        historical_count = sum(1 for _, info in temporal_findings if info.is_historical)
        high_confidence_count = sum(1 for _, info in temporal_findings if info.confidence > 0.7)
        
        reasoning.append(f"Found {len(temporal_findings)} total sources")
        reasoning.append(f"Current information sources: {current_count}")
        reasoning.append(f"Historical information sources: {historical_count}")
        reasoning.append(f"High confidence sources: {high_confidence_count}")
        
        if current_count > historical_count:
            reasoning.append("Majority of sources indicate current/recent information")
        elif historical_count > current_count:
            reasoning.append("Majority of sources appear to be historical")
        else:
            reasoning.append("Mixed current and historical information - requires careful analysis")
        
        # Position-specific reasoning
        query_lower = query.lower()
        if any(pos in query_lower for pos in self.changeable_positions):
            reasoning.append("Query involves a position that commonly changes over time")
            reasoning.append("Extra attention needed to distinguish current vs former office holders")
        
        return reasoning
    
    def _calculate_confidence(self, temporal_findings: List[Tuple[int, TemporalInfo]]) -> float:
        """Calculate overall confidence in temporal classification"""
        if not temporal_findings:
            return 0.0
        
        total_confidence = sum(info.confidence for _, info in temporal_findings)
        avg_confidence = total_confidence / len(temporal_findings)
        
        # Boost confidence if multiple sources agree
        current_count = sum(1 for _, info in temporal_findings if info.is_current)
        historical_count = sum(1 for _, info in temporal_findings if info.is_historical)
        
        if current_count >= 2 or historical_count >= 2:
            avg_confidence += 0.2
        
        return min(avg_confidence, 1.0)
    
    def _generate_recommendations(self, analysis: Dict[str, Any], query: str) -> List[str]:
        """Generate recommendations for handling the information"""
        recommendations = []
        
        if analysis['confidence_score'] > 0.8:
            recommendations.append("High confidence in temporal classification")
        elif analysis['confidence_score'] < 0.5:
            recommendations.append("Low confidence - consider additional search or verification")
        
        if analysis['current_info'] and analysis['historical_info']:
            recommendations.append("Both current and historical info found - prioritize recent sources")
            recommendations.append("Check for transition dates and succession information")
        
        if analysis['conflicting_info']:
            recommendations.append("Conflicts detected - cross-reference multiple sources")
        
        if not analysis['current_info'] and 'current' in query.lower():
            recommendations.append("No clear current information found - may need more specific search")
        
        return recommendations
    
    def _extract_year_from_date(self, date_str: str) -> Optional[int]:
        """Extract year from various date formats"""
        year_match = re.search(r'\b(20\d{2})\b', date_str)
        return int(year_match.group(1)) if year_match else None


def analyze_temporal_context(results: List[Dict[str, Any]], query: str, current_date: datetime) -> Dict[str, Any]:
    """Quick function to analyze temporal context of search results"""
    analyzer = LogicalAnalyzer(current_date)
    return analyzer.analyze_search_results(results, query) 
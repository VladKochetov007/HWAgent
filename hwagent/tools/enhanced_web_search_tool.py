"""
Enhanced Web Search Tool - improved search strategies for current information with content parsing.
Follows SOLID principles and uses core components.
"""

import re
import os
import json
import time
import random
import requests
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin

# HTML parsing imports
try:
    from bs4 import BeautifulSoup, NavigableString, Tag
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    BeautifulSoup = None

from hwagent.core.base_tool import BaseTool
from hwagent.core.models import ToolExecutionResult
from hwagent.core.exceptions import ValidationError
from hwagent.core.constants import Constants
from hwagent.core.date_service import get_date_service
from hwagent.core.logical_analyzer import analyze_temporal_context


class WebsiteContentParser:
    """Parses website content and extracts relevant text."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.timeout = 10
        self.max_content_length = 1024 * 1024  # 1MB limit
    
    def parse_website(self, url: str) -> Dict[str, Any]:
        """Parse website content and extract relevant information."""
        try:
            # Basic URL validation
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return {'error': 'Invalid URL format', 'content': '', 'title': ''}
            
            # Make request with timeout and size limit
            response = self.session.get(
                url, 
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return {'error': f'Unsupported content type: {content_type}', 'content': '', 'title': ''}
            
            # Check content length
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_content_length:
                return {'error': 'Content too large', 'content': '', 'title': ''}
            
            # Read content with size limit
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > self.max_content_length:
                    break
            
            # Parse HTML content
            if HAS_BS4:
                return self._parse_with_bs4(content.decode('utf-8', errors='ignore'))
            else:
                return self._parse_basic(content.decode('utf-8', errors='ignore'))
                
        except requests.exceptions.Timeout:
            return {'error': 'Request timeout', 'content': '', 'title': ''}
        except requests.exceptions.RequestException as e:
            return {'error': f'Request failed: {str(e)}', 'content': '', 'title': ''}
        except Exception as e:
            return {'error': f'Parsing failed: {str(e)}', 'content': '', 'title': ''}
    
    def _parse_with_bs4(self, html_content: str) -> Dict[str, Any]:
        """Parse HTML content using BeautifulSoup."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.decompose()
            
            # Extract title
            title = ''
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extract main content
            content_selectors = [
                'main', 'article', '[role="main"]', '.main-content', 
                '#main-content', '.content', '#content', '.post-content'
            ]
            
            main_content = None
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # If no main content found, use body
            if not main_content:
                main_content = soup.find('body')
            
            if not main_content:
                main_content = soup
            
            # Extract text content
            text_content = main_content.get_text()
            
            # Clean up text
            cleaned_content = self._clean_text(text_content)
            
            return {
                'title': title,
                'content': cleaned_content,
                'error': None
            }
            
        except Exception as e:
            return {'error': f'BeautifulSoup parsing failed: {str(e)}', 'content': '', 'title': ''}
    
    def _parse_basic(self, html_content: str) -> Dict[str, Any]:
        """Basic HTML parsing without BeautifulSoup."""
        try:
            # Extract title using regex
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else ''
            
            # Remove script and style content
            content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
            content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.IGNORECASE | re.DOTALL)
            
            # Remove HTML tags
            content = re.sub(r'<[^>]+>', ' ', content)
            
            # Clean up text
            cleaned_content = self._clean_text(content)
            
            return {
                'title': title,
                'content': cleaned_content,
                'error': None
            }
            
        except Exception as e:
            return {'error': f'Basic parsing failed: {str(e)}', 'content': '', 'title': ''}
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ''
        
        # Decode HTML entities
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove extra newlines
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Trim
        text = text.strip()
        
        # Limit length
        max_length = 5000
        if len(text) > max_length:
            text = text[:max_length] + '...'
        
        return text


class ContentSummarizer:
    """Creates contextual summaries of parsed content."""
    
    @staticmethod
    def create_contextual_summary(content: str, title: str, query: str, url: str) -> str:
        """Create a contextual summary based on the search query."""
        if not content.strip():
            return f"⚠️ No content extracted from {url}"
        
        # Split content into sentences for better processing
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Extract query keywords
        query_keywords = ContentSummarizer._extract_keywords(query.lower())
        
        # Score sentences based on relevance to query
        scored_sentences = []
        for sentence in sentences:
            score = ContentSummarizer._score_sentence(sentence.lower(), query_keywords)
            if score > 0:
                scored_sentences.append((sentence, score))
        
        # Sort by relevance score
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Select top sentences for summary
        summary_sentences = []
        total_length = 0
        max_summary_length = 800
        
        for sentence, score in scored_sentences:
            if total_length + len(sentence) <= max_summary_length:
                summary_sentences.append(sentence)
                total_length += len(sentence)
            else:
                break
        
        # If no relevant sentences found, take first few sentences
        if not summary_sentences and sentences:
            char_count = 0
            for sentence in sentences:
                if char_count + len(sentence) <= max_summary_length:
                    summary_sentences.append(sentence)
                    char_count += len(sentence)
                else:
                    break
        
        # Format summary
        if summary_sentences:
            summary = '. '.join(summary_sentences)
            if not summary.endswith('.'):
                summary += '.'
        else:
            summary = "No relevant content found."
        
        # Add title if available
        title_part = f"**{title}**\n" if title else ""
        
        return f"{title_part}{summary}"
    
    @staticmethod
    def _extract_keywords(query: str) -> List[str]:
        """Extract meaningful keywords from query."""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'could', 'can', 'may', 'might', 'what', 'how', 'when', 'where', 'why',
            'who', 'which', 'that', 'this', 'these', 'those'
        }
        
        # Split query into words and filter
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    @staticmethod
    def _score_sentence(sentence: str, keywords: List[str]) -> float:
        """Score sentence relevance based on keyword presence."""
        if not keywords:
            return 0.0
        
        score = 0.0
        sentence_words = set(re.findall(r'\b\w+\b', sentence.lower()))
        
        for keyword in keywords:
            if keyword in sentence_words:
                score += 1.0
            # Partial matches
            for word in sentence_words:
                if keyword in word or word in keyword:
                    score += 0.5
        
        # Normalize by sentence length
        sentence_length = len(sentence_words)
        if sentence_length > 0:
            score = score / sentence_length
        
        return score


class EnhancedWebSearchService:
    """Enhanced web search service with iterative search and proper date handling."""
    
    def __init__(self):
        self.api_url = "https://api.langsearch.io/web/search"
        self.api_key = self._get_api_key()
        # Initialize date service with the same API key
        self.date_service = get_date_service(self.api_key)
        # Initialize content parser
        self.content_parser = WebsiteContentParser()
        # Track search iterations for learning
        self.search_history = []
    
    def _get_api_key(self) -> str:
        """Get API key from environment."""
        api_key = os.getenv("LANGSEARCH_API_KEY")
        if not api_key:
            raise ValidationError(
                "LangSearch API key not found",
                "Please set LANGSEARCH_API_KEY environment variable"
            )
        return api_key
    
    def search_with_strategies(self, query: str, count: int = 10, freshness_level: str = "auto") -> Dict[str, Any]:
        """Perform enhanced search with adaptive strategies, iterative refinement and proper date handling."""
        print(f"🔍 Starting enhanced search for: '{query}'")
        
        # Determine freshness requirement automatically or use specified level
        detected_freshness = self._detect_freshness_requirement(query)
        final_freshness = freshness_level if freshness_level != "auto" else detected_freshness
        
        print(f"⚡ Detected freshness level: {final_freshness}")
        
        # Get REAL current date from web sources, not system date
        try:
            real_date_info = self.date_service.get_date_info()
            current_year = int(real_date_info['current_year'])
            current_month = real_date_info['current_month']
            current_date = real_date_info['current_date']
            current_month_year = real_date_info['current_month_year']
            
            print(f"🗓️ Using REAL current date: {current_date} ({current_month_year})")
            
        except Exception as e:
            print(f"⚠️ Failed to get real current date: {e}")
            # Fallback to system date as last resort
            system_date = datetime.now()
            current_year = system_date.year
            current_month = system_date.strftime('%B')
            current_date = system_date.strftime('%Y-%m-%d')
            current_month_year = f"{current_month} {current_year}"
            
            print(f"⚠️ Using system date as fallback: {current_date}")
        
        # Temporal context for all search operations
        temporal_context = {
            'current_date_str': current_date,
            'current_month_year': current_month_year,
            'current_year': current_year,
            'current_month': current_month
        }
        
        # Perform initial search
        initial_results, queries_used = self._perform_initial_search(
            query, final_freshness, temporal_context, count
        )
        
        # Analyze initial results and determine if iterative search is needed
        needs_iteration = self._analyze_results_quality(initial_results, query, final_freshness)
        
        if needs_iteration and len(initial_results) > 0:
            print("🔄 Initial results quality suggests iterative search needed...")
            # Perform iterative search with learned information
            refined_results, additional_queries = self._perform_iterative_search(
                query, initial_results, temporal_context, final_freshness, count
            )
            
            # Combine results intelligently
            final_results = self._merge_search_results(initial_results, refined_results, count)
            queries_used.extend(additional_queries)
        else:
            final_results = initial_results
        
        print(f"📊 Final results: {len(final_results)} sources found")
        
        # Parse website content for each result
        print(f"🔍 Parsing content from {len(final_results)} websites...")
        parsed_results = self._parse_search_results(final_results, query)
        
        # Store search information for future learning
        self._update_search_history(query, final_freshness, len(parsed_results))
        
        # Construct response in expected format
        return {
            'results': parsed_results,
            'queries_used': queries_used,
            'current_date_str': current_date,
            'current_month_year': current_month_year,
            'current_year': current_year,
            'current_month': current_month,
            'date_source': "real web sources" if real_date_info else "system date",
            'detected_freshness_level': detected_freshness,
            'logicalAnalysis': self._perform_logical_analysis(parsed_results, query, current_date) if parsed_results else {},
            'content_parsing_enabled': True,
            'iterative_search_used': needs_iteration
        }
    
    def _perform_initial_search(self, query: str, freshness_level: str, temporal_context: dict, count: int) -> tuple[list, list]:
        """Perform the initial search with universal date handling."""
        print("🎯 Performing initial search...")
        
        # Build enhanced query with current year - universal approach
        enhanced_query = self._build_enhanced_query(query, temporal_context)
        
        # Determine search parameters based on freshness level
        search_params = self._create_search_params(freshness_level)
        
        queries_used = [enhanced_query]
        
        try:
            print(f"🔍 Searching with query: '{enhanced_query}'")
            result = self._single_search(
                query=enhanced_query,
                count=count,
                search_params=search_params,
                summary=True
            )
            
            # Process search results
            data = result.get('data', {})
            web_pages = data.get('webPages', {})
            search_results = web_pages.get('value', [])
            
            if search_results:
                # Filter for current results based on freshness level
                filtered_results = self._filter_current_results(
                    search_results, temporal_context['current_year'], 
                    temporal_context['current_month'], freshness_level
                )
                return filtered_results if filtered_results else search_results, queries_used
            else:
                print("⚠️ No results from initial search")
                return [], queries_used
                
        except Exception as e:
            print(f"⚠️ Initial search failed: {e}")
            # Fallback to original query
            try:
                print(f"🔄 Fallback search with original query: '{query}'")
                result = self._single_search(
                    query=query,
                    count=count,
                    search_params=search_params,
                    summary=True
                )
                
                data = result.get('data', {})
                web_pages = data.get('webPages', {})
                search_results = web_pages.get('value', [])
                queries_used.append(query)
                
                return search_results, queries_used
                
            except Exception as fallback_error:
                print(f"⚠️ Fallback search also failed: {fallback_error}")
                return [], queries_used
    
    def _perform_iterative_search(self, query: str, initial_results: list, temporal_context: dict, 
                                 freshness_level: str, count: int) -> tuple[list, list]:
        """Perform iterative search with information learned from initial results."""
        print("🔄 Performing iterative search with learned information...")
        
        # Analyze initial results to extract key information
        learned_keywords = self._extract_learned_keywords(initial_results, query)
        content_gaps = self._identify_content_gaps(initial_results, query)
        
        # Build refined queries based on learned information with improved current data targeting
        refined_queries = self._build_refined_queries(
            query, learned_keywords, content_gaps, temporal_context, freshness_level
        )
        
        additional_results = []
        queries_used = []
        
        for refined_query in refined_queries[:2]:  # Limit to 2 additional searches
            print(f"🔍 Refined search: '{refined_query}'")
            try:
                search_params = self._create_search_params(freshness_level)
                result = self._single_search(
                    query=refined_query,
                    count=count // 2,  # Use fewer results per iteration
                    search_params=search_params,
                    summary=True
                )
                
                data = result.get('data', {})
                web_pages = data.get('webPages', {})
                search_results = web_pages.get('value', [])
                
                if search_results:
                    additional_results.extend(search_results)
                    queries_used.append(refined_query)
                    
            except Exception as e:
                print(f"⚠️ Refined search failed for '{refined_query}': {e}")
                continue
        
        print(f"✅ Iterative search completed: {len(additional_results)} additional results")
        return additional_results, queries_used
    
    def _is_event_query(self, query: str) -> bool:
        """Determine if query is asking about events that require specific date handling."""
        event_indicators = [
            'current', 'latest', 'recent', 'news', 'today', 'happening', 'now',
            'winner', 'president', 'leader', 'elected', 'appointed', 'champion',
            'announced', 'released', 'launched', 'update', 'breaking', 'live',
            # Competition and contest indicators
            'won', 'victory', 'final', 'result', 'score', 'outcome',
            # Event names that typically happen annually
            'eurovision', 'olympics', 'championship', 'cup', 'tournament', 
            'contest', 'festival', 'award', 'prize', 'nomination',
            # Sports terms
            'final', 'match', 'game', 'season'
        ]
        
        query_lower = query.lower()
        
        # Check for event indicators
        has_event_indicator = any(indicator in query_lower for indicator in event_indicators)
        
        # Check for question words that suggest current events
        question_indicators = [
            'who', 'what', 'when', 'where', 'which'
        ]
        has_question = any(q in query_lower for q in question_indicators)
        
        # If it's a question about events/competitions, treat as event query
        if has_question and has_event_indicator:
            return True
            
        return has_event_indicator
    
    def _build_enhanced_query(self, query: str, temporal_context: dict) -> str:
        """Build enhanced query - let LLM determine context naturally."""
        # Simply return the original query without automatic year addition
        # The temporal_context provides current date information for reference,
        # but we trust the LLM to formulate appropriate queries
        return query
    
    def _build_refined_queries(self, original_query: str, learned_keywords: list, 
                              content_gaps: list, temporal_context: dict, freshness_level: str) -> list:
        """Build refined queries based on learned information with improved current data targeting."""
        refined_queries = []
        current_year = temporal_context.get('current_year', 2024)
        
        # For high freshness queries, add specific current-targeting terms
        if freshness_level == 'high':
            # Add year-specific queries for events
            if any(event_term in original_query.lower() for event_term in ['eurovision', 'olympics', 'world cup', 'championship']):
                refined_queries.append(f"{original_query} {current_year}")
                refined_queries.append(f"{original_query} winner {current_year}")
                refined_queries.append(f"{original_query} results {current_year}")
            
            # Add freshness-enhancing terms
            refined_queries.append(f"{original_query} latest")
            refined_queries.append(f"{original_query} recent")
            refined_queries.append(f"{original_query} news {current_year}")
        
        # Add queries with learned keywords - no automatic year addition for other cases
        if learned_keywords:
            for keyword in learned_keywords[:2]:  # Top 2 keywords
                refined_query = f"{original_query} {keyword}"
                refined_queries.append(refined_query)
        
        # Add queries to fill content gaps - enhanced for current events
        if 'recent_updates' in content_gaps:
            gap_query = f"{original_query} latest updates {current_year}"
            refined_queries.append(gap_query)
        
        if 'official_sources' in content_gaps:
            official_query = f"{original_query} official results"
            refined_queries.append(official_query)
        
        # Add news-specific queries for events
        if any(event_term in original_query.lower() for event_term in ['winner', 'champion', 'president', 'leader']):
            refined_queries.append(f"{original_query} news")
            refined_queries.append(f"{original_query} announced")
        
        return refined_queries[:6]  # Limit to 6 refined queries
    
    def _merge_search_results(self, initial_results: list, additional_results: list, max_count: int) -> list:
        """Intelligently merge search results from multiple iterations."""
        # Remove duplicates by URL
        seen_urls = set()
        merged_results = []
        
        # Prioritize initial results (they're most directly relevant)
        for result in initial_results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged_results.append(result)
        
        # Add additional results that aren't duplicates
        for result in additional_results:
            url = result.get('url', '')
            if url and url not in seen_urls and len(merged_results) < max_count:
                seen_urls.add(url)
                merged_results.append(result)
        
        return merged_results[:max_count]
    
    def _parse_search_results(self, results: list, query: str) -> list:
        """Parse website content for search results."""
        parsed_results = []
        
        for i, result in enumerate(results):
            url = result.get('url', '')
            print(f"📄 Parsing {i+1}/{len(results)}: {url}")
            
            # Parse website content
            parsed_content = self.content_parser.parse_website(url)
            
            # Create contextual summary
            if parsed_content.get('content'):
                summary = ContentSummarizer.create_contextual_summary(
                    content=parsed_content['content'],
                    title=parsed_content.get('title', ''),
                    query=query,
                    url=url
                )
                result['content_summary'] = summary
                result['parsed_title'] = parsed_content.get('title', '')
                result['parsing_status'] = 'success'
            else:
                error_msg = parsed_content.get('error', 'Unknown parsing error')
                result['content_summary'] = f"⚠️ Could not parse content: {error_msg}"
                result['parsed_title'] = ''
                result['parsing_status'] = 'failed'
            
            parsed_results.append(result)
        
        return parsed_results
    
    def _update_search_history(self, query: str, freshness_level: str, result_count: int):
        """Update search history for learning purposes."""
        self.search_history.append({
            'query': query,
            'freshness_level': freshness_level,
            'result_count': result_count,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 10 searches
        if len(self.search_history) > 10:
            self.search_history = self.search_history[-10:]
    
    def _detect_freshness_requirement(self, query: str) -> str:
        """Automatically detect if query requires fresh information."""
        query_lower = query.lower()
        
        # High freshness indicators (very current info needed)
        high_freshness_keywords = [
            'current', 'latest', 'recent', 'today', 'now', 'this year', 'this month',
            'winner', 'president', 'leader', 'champion', 'elected', 'appointed',
            'news', 'breaking', 'update', 'status', 'situation', 'happening',
            'latest version', 'new release', 'just released', 'announced',
            # Added more event-specific terms
            'eurovision', 'olympics', 'world cup', 'championship', 'contest',
            'festival', 'award', 'prize', 'tournament', 'final', 'won', 'victory',
            'result', 'outcome', 'competition'
        ]
        
        # Medium freshness indicators (somewhat current info needed)
        medium_freshness_keywords = [
            'best practices', 'tutorial', 'guide', 'how to', 'compared',
            'review', 'analysis', 'trends', 'popular', 'recommended'
        ]
        
        # Low freshness indicators (general/historical info is fine)
        low_freshness_keywords = [
            'history', 'definition', 'explanation', 'theory', 'concept',
            'born', 'founded', 'created', 'invented', 'origin'
        ]
        
        # Check for high freshness first - be more aggressive for events
        if any(keyword in query_lower for keyword in high_freshness_keywords):
            return "high"
        
        # Check for low freshness
        if any(keyword in query_lower for keyword in low_freshness_keywords):
            return "low"
        
        # Check for medium freshness
        if any(keyword in query_lower for keyword in medium_freshness_keywords):
            return "medium"
        
        # For ambiguous queries, default to high freshness to get current info
        return "high"
    
    def _create_search_params(self, freshness_level: str) -> dict:
        """Create search parameters based on freshness level."""
        base_params = {
            'summary': True,
            'count': 15
        }
        
        if freshness_level == 'high':
            base_params.update({
                'freshness': 'Day',  # Most recent results
                'count': 20,
                'sortBy': 'Date'  # Sort by date for freshest results
            })
        elif freshness_level == 'medium':
            base_params.update({
                'freshness': 'Week',
                'count': 15
            })
        else:
            base_params.update({
                'freshness': 'Month',
                'count': 12
            })
        
        return base_params
    
    def _filter_current_results(self, results: List[Dict[str, Any]], current_year: int, 
                              current_month: str, freshness_level: str) -> List[Dict[str, Any]]:
        """Filter results based on temporal relevance with improved current data detection."""
        if not results:
            return []
        
        filtered = []
        current_year_str = str(current_year)
        previous_year_str = str(current_year - 1)
        
        # Create priority scoring for results
        scored_results = []
        
        for result in results:
            score = 0
            content_text = f"{result.get('name', '')} {result.get('snippet', '')}".lower()
            
            # Check date published - highest priority
            date_published = result.get('datePublished', '')
            if date_published:
                if current_year_str in date_published:
                    score += 100
                    # Bonus for recent months
                    if any(month in date_published.lower() for month in ['december', 'november', 'october']):
                        score += 50
                elif previous_year_str in date_published:
                    score += 20
            
            # Check content for current year mentions - high priority
            if current_year_str in content_text:
                score += 80
            
            # Check for current month mentions
            if current_month.lower() in content_text:
                score += 60
            
            # Check for freshness indicators in content
            freshness_terms = ['latest', 'recent', 'new', 'current', 'today', 'now', '2024']
            for term in freshness_terms:
                if term in content_text:
                    score += 30
                    break
            
            # For event queries, check for specific event indicators
            event_terms = ['winner', 'champion', 'won', 'victory', 'result', 'final']
            for term in event_terms:
                if term in content_text:
                    score += 40
                    break
            
            # URL quality indicators
            url = result.get('url', '').lower()
            if any(domain in url for domain in ['wikipedia', 'bbc', 'cnn', 'reuters', 'eurovision.tv']):
                score += 25
            
            scored_results.append((score, result))
        
        # Sort by score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # For high freshness, be very selective
        if freshness_level == 'high':
            # Only include results with decent scores
            filtered = [result for score, result in scored_results if score > 50]
            # If too few good results, include some lower-scored ones
            if len(filtered) < 3:
                filtered.extend([result for score, result in scored_results[:8] if score <= 50])
        else:
            # For medium/low freshness, be more inclusive
            filtered = [result for score, result in scored_results]
        
        return filtered[:15] if filtered else results[:10]
    
    def _single_search(self, query: str, count: int, search_params: dict | str, summary: bool) -> Dict[str, Any]:
        """Perform single search request with proper parameter handling."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Handle both dict and string search_params for backward compatibility
        if isinstance(search_params, dict):
            payload = {
                "query": query,
                "count": count,
                "summary": summary,
                **search_params  # Merge all search parameters
            }
        else:
            payload = {
                "query": query,
                "freshness": search_params,
                "summary": summary,
                "count": count
            }
        
        response = requests.post(
            self.api_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def _perform_logical_analysis(self, results: List[Dict[str, Any]], query: str, current_date_str: str) -> Dict[str, Any]:
        """Perform logical analysis of search results for temporal context"""
        try:
            # Convert date string back to datetime for analysis
            current_date = datetime.strptime(current_date_str, '%Y-%m-%d')
            
            # Perform temporal analysis
            analysis = analyze_temporal_context(results, query, current_date)
            
            # Add summary for easy consumption
            analysis['summary'] = {
                'has_current_info': len(analysis['current_info']) > 0,
                'has_historical_info': len(analysis['historical_info']) > 0,
                'has_conflicts': len(analysis['conflicting_info']) > 0,
                'confidence_level': 'high' if analysis['confidence_score'] > 0.7 else 'medium' if analysis['confidence_score'] > 0.4 else 'low',
                'primary_recommendation': analysis['recommendations'][0] if analysis['recommendations'] else 'No specific recommendations'
            }
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Logical analysis failed: {e}")
            return {'error': str(e), 'analysis_available': False}
    
    def _analyze_results_quality(self, results: list, query: str, freshness_level: str) -> bool:
        """Analyze if initial results warrant iterative search."""
        if not results:
            return True  # No results, definitely need more searching
        
        if len(results) < 3:
            return True  # Too few results, need more
        
        # Check if results are diverse enough
        domains = set()
        for result in results:
            url = result.get('url', '')
            if url:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    domains.add(domain)
                except:
                    pass
        
        if len(domains) < 2:
            return True  # Not enough diversity, need more sources
        
        # For high freshness queries, always do iterative search
        if freshness_level == 'high':
            return True
        
        return False  # Results seem adequate
    
    def _extract_learned_keywords(self, results: list, original_query: str) -> list:
        """Extract useful keywords from initial search results."""
        keywords = set()
        
        for result in results:
            # Extract from title
            title = result.get('name', '')
            if title:
                title_words = re.findall(r'\b\w+\b', title.lower())
                keywords.update([w for w in title_words if len(w) > 3])
            
            # Extract from snippet
            snippet = result.get('snippet', '')
            if snippet:
                snippet_words = re.findall(r'\b\w+\b', snippet.lower())
                keywords.update([w for w in snippet_words if len(w) > 3])
        
        # Filter out common words and words already in original query
        original_words = set(re.findall(r'\b\w+\b', original_query.lower()))
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        filtered_keywords = [k for k in keywords if k not in original_words and k not in stop_words]
        
        # Return top 5 most relevant keywords
        return filtered_keywords[:5]
    
    def _identify_content_gaps(self, results: list, query: str) -> list:
        """Identify what additional information might be needed."""
        gaps = []
        
        # Check for missing temporal information
        has_recent_info = any('2024' in str(result) or '2025' in str(result) for result in results)
        if not has_recent_info:
            gaps.append('recent_updates')
        
        # Check for missing official sources
        has_official_sources = any(
            any(domain in result.get('url', '') for domain in ['.gov', '.edu', '.org']) 
            for result in results
        )
        if not has_official_sources:
            gaps.append('official_sources')
        
        return gaps


class EnhancedSearchResultFormatter:
    """Enhanced formatter with temporal analysis and better formatting."""
    
    @staticmethod
    def format_enhanced_results(api_response: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Format enhanced search results with logical analysis and content summaries."""
        results = api_response.get('results', [])
        queries_used = api_response.get('queries_used', [])
        current_date_str = api_response.get('current_date_str', 'Unknown')
        current_month_year = api_response.get('current_month_year', 'Unknown')
        date_source = api_response.get('date_source', 'system date')
        detected_freshness = api_response.get('detected_freshness_level', 'medium')
        logical_analysis = api_response.get('logicalAnalysis', {})
        content_parsing_enabled = api_response.get('content_parsing_enabled', False)
        
        formatted_lines = []
        
        # Header with search info
        formatted_lines.append("# 🔍 Enhanced Web Search Results")
        formatted_lines.append("")
        
        # Real date verification section
        formatted_lines.append(f"🗓️ **REAL DATE VERIFICATION:**")
        formatted_lines.append(f"✅ Current Date: **{current_date_str}** ({current_month_year})")
        formatted_lines.append(f"📡 Date Source: {date_source}")
        if date_source != "system date":
            formatted_lines.append("✅ *Using REAL current date from web sources*")
        else:
            formatted_lines.append("⚠️ *Fallback to system date*")
        formatted_lines.append("")
        
        # Enhanced search analysis
        formatted_lines.append("🎯 **ENHANCED SEARCH ANALYSIS:**")
        formatted_lines.append(f"📊 Sources Found: **{len(results)}**")
        formatted_lines.append(f"📅 Date Source: {date_source}")
        formatted_lines.append(f"🔍 Queries Used: {', '.join(f'`{q}`' for q in queries_used)}")
        formatted_lines.append(f"⚡ Detected Freshness Level: **{detected_freshness}**")
        
        # Content parsing statistics
        if content_parsing_enabled:
            parsed_count = sum(1 for r in results if r.get('parsing_status') == 'success')
            failed_count = sum(1 for r in results if r.get('parsing_status') == 'failed')
            formatted_lines.append(f"📄 Content Parsing: **{parsed_count} successful**, {failed_count} failed")
            formatted_lines.append("✅ *Content summaries enabled*")
        else:
            formatted_lines.append("📄 Content Parsing: **Disabled**")
        
        formatted_lines.append("")
        
        # Logical analysis insights (if available)
        if logical_analysis:
            try:
                formatted_lines.append("🧠 **LOGICAL ANALYSIS:**")
                
                current_info_count = logical_analysis.get('current_info_count', 0)
                historical_info_count = logical_analysis.get('historical_info_count', 0)
                confidence_score = logical_analysis.get('confidence_score', 0.0)
                conflicts_detected = logical_analysis.get('conflicts_detected', 0)
                
                formatted_lines.append(f"📊 Current Info Sources: **{current_info_count}**")
                formatted_lines.append(f"📚 Historical Info Sources: **{historical_info_count}**")
                formatted_lines.append(f"🎯 Confidence Score: **{confidence_score:.2f}**")
                formatted_lines.append(f"⚠️ Conflicts Detected: **{conflicts_detected}**")
                
                # AI reasoning
                ai_reasoning = logical_analysis.get('ai_reasoning', '')
                if ai_reasoning:
                    formatted_lines.append(f"🤖 **AI Reasoning:** {ai_reasoning}")
                
                # Primary recommendation
                primary_recommendation = logical_analysis.get('primary_recommendation', '')
                if primary_recommendation:
                    formatted_lines.append(f"💡 **Primary Recommendation:** {primary_recommendation}")
                
                formatted_lines.append("")
                
                # Conflicts section (max 2 conflicts)
                conflicts = logical_analysis.get('conflicts', [])
                if conflicts:
                    formatted_lines.append("⚠️ **DETECTED CONFLICTS:**")
                    for i, conflict in enumerate(conflicts[:2], 1):  # Show max 2 conflicts
                        conflict_description = conflict.get('description', 'Unknown conflict')
                        conflict_recommendation = conflict.get('recommendation', 'No recommendation')
                        
                        formatted_lines.append(f"**Conflict {i}:** {conflict_description}")
                        formatted_lines.append(f"**Recommendation:** {conflict_recommendation}")
                        if i < len(conflicts[:2]):  # Add separator if not last
                            formatted_lines.append("")
                    
                    if len(conflicts) > 2:
                        formatted_lines.append(f"*... and {len(conflicts) - 2} more conflicts*")
                    
                    formatted_lines.append("")
                
            except Exception as e:
                formatted_lines.append(f"⚠️ **Logical Analysis Error:** {str(e)}")
                formatted_lines.append("")
        
        # Results section
        if results:
            formatted_lines.append("## 📋 Search Results")
            formatted_lines.append("")
            
            for i, result in enumerate(results, 1):
                result_lines = EnhancedSearchResultFormatter._format_single_result(result, i)
                formatted_lines.extend(result_lines)
                formatted_lines.append("")  # Empty line between results
        else:
            formatted_lines.append("## ❌ No Results Found")
            formatted_lines.append("")
            formatted_lines.append("No search results were found for your query. Try:")
            formatted_lines.append("- Using different keywords")
            formatted_lines.append("- Making your query more specific")
            formatted_lines.append("- Checking for spelling errors")
        
        # Combine all formatted lines
        formatted_text = "\n".join(formatted_lines)
        
        return formatted_text, {
            'result_count': len(results),
            'queries_used': queries_used,
            'current_date': current_date_str,
            'date_source': date_source,
            'detected_freshness': detected_freshness,
            'logical_analysis': logical_analysis,
            'content_parsing_enabled': content_parsing_enabled,
            'parsed_successfully': sum(1 for r in results if r.get('parsing_status') == 'success'),
            'parsing_failures': sum(1 for r in results if r.get('parsing_status') == 'failed')
        }
    
    @staticmethod
    def _format_single_result(result: Dict[str, Any], index: int) -> List[str]:
        """Format a single search result with enhanced information and content summary."""
        lines = []
        
        # Header with number and title
        title = result.get('name', 'No title')
        lines.append(f"**{index}. {title}**")
        
        # URL
        url = result.get('url', '')
        if url:
            lines.append(f"🔗 **URL:** {url}")
        
        # Snippet/description
        snippet = result.get('snippet', '')
        if snippet:
            lines.append(f"📝 **Description:** {snippet}")
        
        # Content summary from parsing
        content_summary = result.get('content_summary', '')
        parsing_status = result.get('parsing_status', 'unknown')
        
        if content_summary:
            lines.append(f"📄 **Content Summary:**")
            lines.append(content_summary)
            
            # Show parsing status
            if parsing_status == 'success':
                lines.append("✅ *Content successfully parsed and summarized*")
            elif parsing_status == 'failed':
                lines.append("❌ *Content parsing failed*")
        
        # Date information if available
        date_published = result.get('datePublished', '')
        if date_published:
            lines.append(f"📅 **Published:** {date_published}")
        
        # Additional metadata
        language = result.get('language', '')
        if language and language != 'en':
            lines.append(f"🌐 **Language:** {language}")
        
        return lines


class EnhancedWebSearchTool(BaseTool):
    """Enhanced web search tool with better strategies for current information."""
    
    def __init__(self, tmp_directory: str = Constants.DEFAULT_TMP_DIRECTORY):
        super().__init__(tmp_directory)
        self.search_service = EnhancedWebSearchService()
        self.formatter = EnhancedSearchResultFormatter()
    
    @property
    def name(self) -> str:
        return "enhanced_web_search"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return (
            "Enhanced web search tool with iterative refinement and intelligent content parsing. "
            "Automatically adds current date context to ALL queries for temporal relevance. "
            "Provides detailed search results with content summaries, temporal analysis, and "
            "smart freshness detection. Always includes current date information in results "
            "to help distinguish between current events and historical data. "
            "Supports event queries, technical searches, and general information retrieval."
        )
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """Returns the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Tool will enhance with current date, month, year, and temporal keywords for maximum currency based on detected or specified freshness level."
                },
                "count": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": Constants.MAX_SEARCH_COUNT,
                    "description": f"Number of search results to return (1-{Constants.MAX_SEARCH_COUNT}, default: 10)",
                    "default": 10
                },
                "freshness_level": {
                    "type": "string",
                    "enum": ["auto", "high", "medium", "low"],
                    "description": "Search freshness level: 'auto' (detect automatically), 'high' (latest/current info), 'medium' (recent info), 'low' (general info). Default: auto",
                    "default": "auto"
                }
            },
            "required": ["query"]
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """Validate search parameters with language guidance."""
        query = parameters.get('query', '').strip()
        count = parameters.get('count', 10)
        freshness_level = parameters.get('freshness_level', 'auto')
        
        if not query:
            return ToolExecutionResult.error(
                "Query parameter is required",
                "Provide a search query string"
            )
        
        if not isinstance(count, int) or count < 1 or count > 20:
            return ToolExecutionResult.error(
                "Count must be an integer between 1 and 20",
                "Use count between 1-20 for optimal performance"
            )
        
        if freshness_level not in ['auto', 'high', 'medium', 'low']:
            return ToolExecutionResult.error(
                "Invalid freshness_level",
                "Use 'auto', 'high', 'medium', or 'low'"
            )
        
        # Provide language guidance
        language_guidance = self._suggest_query_language(query)
        
        guidance_message = "✅ Search parameters validated"
        if language_guidance['suggested_language'] == 'english' and language_guidance['confidence'] == 'high':
            guidance_message += f"\n💡 Language tip: For international topics like this, English queries often provide better results."
        elif language_guidance['suggested_language'] == 'local' and language_guidance['confidence'] == 'high':
            guidance_message += f"\n💡 Language tip: For local/government topics like this, using local language is recommended."
        
        return ToolExecutionResult.success(guidance_message)
    
    def _execute_impl(self, **kwargs) -> str:
        """Execute the enhanced web search using iterative search strategies."""
        query = kwargs.get('query', '')
        count = kwargs.get('count', 10)
        freshness_level = kwargs.get('freshness_level', 'auto')
        
        try:
            # Use new iterative search system
            search_results = self.search_service.search_with_strategies(
                query=query,
                count=count,
                freshness_level=freshness_level
            )
            
            # Format results for return
            results = search_results.get('results', [])
            current_date = search_results.get('current_date_str', 'Unknown')
            current_year = search_results.get('current_year', 'Unknown')
            
            if not results:
                return (
                    f"📅 **CURRENT DATE CONTEXT: {current_date} (Year: {current_year})**\n"
                    f"🔍 No search results found for query: '{query}'\n\n"
                    f"ℹ️ **Note**: Search was performed on {current_date}. "
                    f"If you were looking for {current_year} events, they may not have occurred yet "
                    f"or may not be widely reported online.\n\n"
                    f"**🎯 Temporal Context:**\n"
                    f"• Current date: {current_date}\n"
                    f"• Current year: {current_year}\n"
                    f"• For events like Eurovision, Olympics, championships - check if they have occurred in {current_year}"
                )
            
            # Create comprehensive response with prominent date context
            response_lines = [
                f"📅 **CURRENT DATE CONTEXT: {current_date} (Year: {current_year})**",
                f"🔍 **Search Results for '{query}'**",
                f"📊 Found {len(results)} sources",
                f"⚡ Freshness level: {search_results.get('detected_freshness_level', 'auto')}",
                f"🔄 Iterative search: {'Yes' if search_results.get('iterative_search_used', False) else 'No'}",
                "",
                "ℹ️ **Note**: When evaluating results about events like Eurovision, Olympics, or competitions,",
                f"consider that the search was performed on {current_date}. Results about '{current_year}' events",
                "should be prioritized as most current, while older years represent historical data.",
                ""
            ]
            
            # Add results with enhanced formatting
            for i, result in enumerate(results, 1):
                url = result.get('url', '')
                title = result.get('name', 'Untitled')
                snippet = result.get('snippet', '')
                content_summary = result.get('content_summary', '')
                parsing_status = result.get('parsing_status', 'unknown')
                
                # Extract year from result for temporal awareness
                years_in_result = re.findall(r'\b(20\d{2})\b', f"{title} {snippet} {content_summary}")
                most_recent_year = max(years_in_result) if years_in_result else None
                
                response_lines.extend([
                    f"**{i}. {title}**",
                    f"🔗 {url}",
                    f"📄 {snippet}",
                ])
                
                # Add temporal relevance indicator
                if most_recent_year:
                    if most_recent_year == str(current_year):
                        response_lines.append(f"🕐 **CURRENT YEAR DATA ({most_recent_year})** - Most relevant for current events")
                    else:
                        years_difference = int(current_year) - int(most_recent_year) if current_year != 'Unknown' else 0
                        if years_difference > 0:
                            response_lines.append(f"📅 Historical data from {most_recent_year} ({years_difference} years ago)")
                
                # Add content summary if available
                if content_summary and parsing_status == 'success':
                    response_lines.append(f"💡 **Content Summary:** {content_summary}")
                elif parsing_status == 'failed':
                    response_lines.append(f"⚠️ Content parsing failed: {content_summary}")
                
                response_lines.append("")  # Empty line between results
            
            # Add search metadata
            queries_used = search_results.get('queries_used', [])
            if len(queries_used) > 1:
                response_lines.extend([
                    "**Search Queries Used:**",
                    *[f"• {query}" for query in queries_used],
                    ""
                ])
            
            # Add logical analysis if available
            logical_analysis = search_results.get('logicalAnalysis', {})
            if logical_analysis and not logical_analysis.get('error'):
                analysis_summary = logical_analysis.get('summary', {})
                if analysis_summary:
                    response_lines.extend([
                        "**🧠 Search Analysis:**",
                        f"• Current info available: {'Yes' if analysis_summary.get('has_current_info', False) else 'No'}",
                        f"• Historical info available: {'Yes' if analysis_summary.get('has_historical_info', False) else 'No'}",
                        f"• Confidence level: {analysis_summary.get('confidence_level', 'Unknown')}",
                        ""
                    ])
            
            # Add final temporal guidance for LLM
            response_lines.extend([
                "**🎯 Temporal Analysis Guide:**",
                f"• Search performed on: {current_date}",
                f"• Current year: {current_year}",
                f"• For events like Eurovision, Olympics, championships - prioritize {current_year} data",
                "• Older years represent historical winners/results",
                "• If no current year data found, the event may not have occurred yet in this year"
            ])
            
            return "\n".join(response_lines)
            
        except ValidationError as e:
            return f"⚠️ Search validation error: {e.message}\n💡 Suggestion: {e.suggestion}"
        except Exception as e:
            return f"⚠️ Search failed: {str(e)}\n💡 Please try rephrasing your query or check your internet connection."

    def _suggest_query_language(self, query: str) -> dict:
        """Suggest appropriate language for search query based on content."""
        query_lower = query.lower()
        
        # Local/Government indicators that should use local language
        local_indicators = [
            # Russian government and local entities
            'президент россии', 'правительство рф', 'госдума', 'совет федерации',
            'мэр москвы', 'мэр питера', 'губернатор', 'региональные власти',
            'российские выборы', 'местные выборы', 'муниципальные выборы',
            'сбербанк', 'роснефт', 'газпром', 'ростех', 'рособоронэкспорт',
            'русская литература', 'славянская культура', 'российская история',
            'местные новости', 'региональные новости'
        ]
        
        # International topics that should use English
        international_indicators = [
            # Events and competitions
            'eurovision', 'olympics', 'world cup', 'championship', 'nobel prize',
            # Technology and companies
            'apple', 'google', 'microsoft', 'tesla', 'amazon', 'facebook', 'meta',
            'iphone', 'android', 'ai news', 'artificial intelligence', 'machine learning',
            # Global topics
            'climate change', 'covid', 'ukraine', 'global warming', 'space exploration',
            'stock market', 'cryptocurrency', 'bitcoin'
        ]
        
        # Check for local indicators
        has_local = any(indicator in query_lower for indicator in local_indicators)
        
        # Check for international indicators  
        has_international = any(indicator in query_lower for indicator in international_indicators)
        
        if has_local:
            return {
                'suggested_language': 'local',
                'reason': 'Query contains local/government specific terms',
                'confidence': 'high'
            }
        elif has_international:
            return {
                'suggested_language': 'english',
                'reason': 'Query contains international topic terms',
                'confidence': 'high'
            }
        else:
            # For ambiguous cases, suggest English for better coverage
            return {
                'suggested_language': 'english',
                'reason': 'Default to English for better international coverage',
                'confidence': 'medium'
            }


def get_tool():
    """Get the enhanced web search tool instance."""
    return EnhancedWebSearchTool() 
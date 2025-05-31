# Search Behavior Fix - December 18, 2024

## Problem Identified
The Enhanced Web Search Tool was automatically adding years (like 2024) to search queries, even when users didn't specify a particular year. This caused the agent to search for outdated information instead of the most current data.

**Example of the problem:**
- User query: "Eurovision winner" 
- Agent was searching: "Eurovision winner 2024" or "Eurovision 2023 winner"
- Should search: "Eurovision winner" (to get most current results)

## Root Cause
The issue was in two methods within `hwagent/tools/enhanced_web_search_tool.py`:

1. **`_build_enhanced_query`** - Automatically appended current year to any query without a year
2. **`_build_refined_queries`** - Also added years to refined search queries

This conflicted with the prompt guidelines that instruct the agent to search for current data without adding specific years unless requested.

## Solution Implemented

### 1. Updated Query Enhancement Logic
```python
def _build_enhanced_query(self, query: str, temporal_context: dict) -> str:
    """Build enhanced query - let LLM determine context naturally."""
    # Simply return the original query without automatic year addition
    # The temporal_context provides current date information for reference,
    # but we trust the LLM to formulate appropriate queries
    return query
```

### 2. Updated Refined Query Building
```python
def _build_refined_queries(self, original_query: str, learned_keywords: list, 
                          content_gaps: list, temporal_context: dict, freshness_level: str) -> list:
    """Build refined queries based on learned information."""
    refined_queries = []
    
    # Add queries with learned keywords - no automatic year addition
    if learned_keywords:
        for keyword in learned_keywords[:2]:  # Top 2 keywords
            refined_query = f"{original_query} {keyword}"
            refined_queries.append(refined_query)
    
    # Add queries to fill content gaps - no automatic year addition
    if 'recent_updates' in content_gaps:
        gap_query = f"{original_query} latest updates"
        refined_queries.append(gap_query)
    
    if 'official_sources' in content_gaps:
        official_query = f"{original_query} official"
        refined_queries.append(official_query)
    
    return refined_queries
```

### 3. Enhanced Prompt Guidelines
Updated `hwagent/config/prompts.yaml` with comprehensive guidelines:

#### Critical Web Search Guidelines
- **DEFAULT BEHAVIOR**: SEARCH FOR MOST CURRENT DATA
- **DO NOT ADD SPECIFIC YEARS** unless user explicitly requests them
- **TRUST THE TOOL** - Enhanced web search automatically adds current date context

#### Usage Examples
```yaml
# CORRECT (for current events):
enhanced_web_search(query="Eurovision winner", count=5)
enhanced_web_search(query="World Cup champion", count=5) 
enhanced_web_search(query="current president USA", count=5)

# ONLY when user requests specific year:
enhanced_web_search(query="Eurovision 2023 winner", count=5)  # Only if user asked for 2023
```

#### Best Practices
1. DEFAULT: Search for MOST CURRENT information - DO NOT add years unless user specifies
2. Tool automatically adds current date context to all searches
3. Tool provides temporal analysis marking current vs historical data
4. Trust the tool's automatic date handling - don't add years manually
5. Only include specific years if user explicitly requests that year
6. For 'who won X', 'current Y', 'latest Z' - search without years

## Impact

### Before Fix
- Query: "Eurovision winner" → Search: "Eurovision winner 2024"
- Result: Potentially outdated or specific year data

### After Fix  
- Query: "Eurovision winner" → Search: "Eurovision winner"
- Result: Most current winner information from search engine's ranking

## Key Benefits

1. **Natural Context Determination**: LLM can analyze user intent without forced temporal constraints
2. **Current Data Priority**: Search engines return most relevant/current results by default
3. **User Intent Preservation**: Only add years when explicitly requested
4. **Flexible Search Strategy**: Tool provides temporal context without forcing it

## Verification
All changes have been tested and verified:
- ✅ Queries no longer automatically enhanced with years
- ✅ LLM can determine context naturally
- ✅ Temporal context remains available for reference
- ✅ System follows new prompt guidelines
- ✅ Prompt guidelines properly configured

## Files Modified
1. `hwagent/tools/enhanced_web_search_tool.py` - Core logic fixes
2. `hwagent/config/prompts.yaml` - Enhanced guidelines and examples

This fix ensures the agent searches for the most current information by default, while still allowing specific year searches when explicitly requested by users. 
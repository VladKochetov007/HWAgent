# Intelligent Freshness Detection Guide

## Overview
Enhanced Web Search Tool now includes intelligent freshness detection that automatically determines how current the information needs to be based on the query content.

## How It Works

### Automatic Detection
The system analyzes your query and automatically chooses the appropriate freshness level:

#### High Freshness (Latest Information Required)
- **Triggers**: "current", "latest", "recent", "today", "now", "this year", "news", "breaking", "winner", "president", etc.
- **Strategy**: Aggressive search with specific dates, current month/year, and real-time indicators
- **Example Queries**: 
  - "current US president" → Searches with 2025-01-15, January 2025, latest, now
  - "latest AI news" → Prioritizes very recent results

#### Medium Freshness (Recent Information Preferred)
- **Triggers**: "tutorial", "guide", "best practices", "how to", "review", "trends", "popular"
- **Strategy**: Moderate recency focus with current year emphasis
- **Example Queries**:
  - "Python tutorial" → Searches with 2025, latest, current, updated
  - "machine learning guide" → Focuses on recent but not necessarily today's info

#### Low Freshness (General Information Acceptable)
- **Triggers**: "history", "definition", "explanation", "theory", "born", "founded", "created"
- **Strategy**: General queries without heavy temporal restrictions
- **Example Queries**:
  - "history of computers" → No date restrictions, accepts older authoritative sources
  - "definition of AI" → Focuses on comprehensive explanations regardless of date

## Usage Examples

### Using Automatic Detection (Recommended)
```python
# System automatically detects freshness level
tool.execute(query="latest OpenAI developments")  # → High freshness
tool.execute(query="Python programming guide")    # → Medium freshness  
tool.execute(query="history of programming")      # → Low freshness
```

### Manual Override
```python
# Override automatic detection when needed
tool.execute(query="Python guide", freshness_level="high")     # Force latest info
tool.execute(query="current news", freshness_level="low")      # Accept older sources
```

## Parameters

- **freshness_level**: `"auto"` (default), `"high"`, `"medium"`, `"low"`
  - `"auto"`: Intelligent detection based on query content
  - `"high"`: Latest information (last week), aggressive date queries
  - `"medium"`: Recent information (last month), moderate currency
  - `"low"`: General information (last year), no date restrictions

## Benefits

1. **Intelligent Resource Usage**: Avoids unnecessary aggressive searching for historical queries
2. **Better Results**: Matches search strategy to information type needed
3. **Automatic Optimization**: No need to manually specify freshness for most queries
4. **Flexible Override**: Manual control when automatic detection isn't suitable

## Query Examples by Category

### High Freshness Queries
- "who is the current CEO of..."
- "latest stock prices"
- "today's weather"
- "recent election results"
- "breaking news about..."
- "current status of..."

### Medium Freshness Queries
- "best practices for React development"
- "tutorial on machine learning"
- "comparison of frameworks 2025"
- "guide to cloud computing"
- "popular tools for data science"

### Low Freshness Queries
- "history of the internet"
- "definition of quantum computing"
- "when was JavaScript created"
- "explanation of neural networks"
- "biography of Alan Turing"

The system handles edge cases intelligently and defaults to medium freshness for ambiguous queries. 
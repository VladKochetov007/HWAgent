# User Guide: Enhanced Memory and Search Features

## Quick Start

The HWAgent now has significantly improved memory and search capabilities. Here's how to use them effectively.

## 🧠 Memory Features

### Check What the Agent Remembers

```
memory(action="summary")
```

This shows:
- Current session summary
- Number of interactions
- Tools you've used recently
- Key topics discussed

### Search Your Conversation History

```
memory(action="search", query="LaTeX")
```

Find previous conversations about specific topics:
- Search for "LaTeX" to find previous document work
- Search for "Python" to find coding solutions
- Search for "error" to find troubleshooting sessions

### Get Insights About Your Patterns

```
memory(action="insights", days=7)
```

See patterns from the last week:
- Frequent task types
- Successful approaches
- Tool usage patterns
- Common topics

### View Memory Statistics

```
memory(action="stats")
```

Get overview of:
- Current session activity
- Historical data summary
- Memory system health

## 🔍 Enhanced Search Features

### Search for Current Information

The agent now automatically uses enhanced search strategies:

```
enhanced_web_search(query="Python 3.12 new features", count=5)
```

**What's improved:**
- Automatically tries multiple search strategies
- Prioritizes recent/current information
- Adds current year and "latest" keywords
- Analyzes results for temporal relevance

### Better Technical Searches

```
enhanced_web_search(query="React 18 best practices", count=3)
```

The enhanced search:
- Looks for 2024 content first
- Finds official documentation
- Prioritizes recent tutorials
- Filters out outdated information

## 💡 How Memory Helps You

### 1. Continuity Across Sessions
- Agent remembers your previous work
- Builds on successful solutions
- Avoids repeating failed approaches
- Maintains context between conversations

### 2. Personalized Responses
- Adapts to your preferred tools
- Remembers your working style
- References previous successful solutions
- Learns from your feedback

### 3. Efficient Problem Solving
- Checks memory before starting new tasks
- Reuses successful patterns
- Avoids known problematic approaches
- Builds incrementally on previous work

## 🚀 Best Practices

### For Memory Usage

1. **Let the agent build on previous work**
   - Reference previous solutions when asking for similar tasks
   - Mention if you want to modify previous approaches

2. **Use memory search for context**
   - Search memory before asking repeated questions
   - Check insights to understand your patterns

3. **Provide feedback on approaches**
   - Tell the agent when solutions work well
   - Mention when approaches should be avoided

### For Search Usage

1. **Be specific about currency needs**
   - Mention "latest" or "current" for recent information
   - Include version numbers for software/tools
   - Specify year when relevant

2. **Use enhanced search for technical topics**
   - Better for finding current best practices
   - More effective for recent developments
   - Prioritizes official documentation

## 📋 Common Use Cases

### LaTeX Document Creation
```
# Agent remembers your document preferences
unified_latex(operation="create", task_type="math", language="russian")

# Check previous LaTeX solutions
memory(action="search", query="LaTeX compilation")
```

### Programming Help
```
# Search for current best practices
enhanced_web_search(query="Python asyncio 2024 patterns")

# Check previous coding solutions
memory(action="search", query="Python error handling")
```

### Research Tasks
```
# Find recent developments
enhanced_web_search(query="machine learning advances 2024")

# Review previous research patterns
memory(action="insights", days=14)
```

## 🔧 Troubleshooting

### If Memory Seems Empty
- Memory builds up over time as you use the agent
- Each interaction is automatically saved
- Use `memory(action="stats")` to check system status

### If Search Results Seem Outdated
- Use `enhanced_web_search` instead of regular `web_search`
- Include "latest", "current", or "2024" in your queries
- Check that LANGSEARCH_API_KEY is properly configured

### If Agent Doesn't Reference Previous Work
- Memory context is automatically included in prompts
- Explicitly mention "like we did before" to trigger memory usage
- Use `memory(action="search")` to find relevant previous solutions

## 🎯 Tips for Maximum Benefit

1. **Be consistent with terminology**
   - Use similar terms for similar tasks
   - This helps memory pattern recognition

2. **Provide context in requests**
   - Mention if this builds on previous work
   - Reference successful approaches from memory

3. **Use memory tools proactively**
   - Check insights regularly to understand your patterns
   - Search memory before asking repeated questions

4. **Give feedback on results**
   - Tell the agent when approaches work well
   - This improves future memory-guided decisions

## 📊 Understanding Memory Output

### Session Summary Format
```
📋 Current Session Summary
💬 Summary: [Brief description of session]
📊 Entry Count: [Number of interactions]
🔧 Recent Tools Used: [List of tools]
🎯 Key Topics: [Main discussion topics]
```

### Search Results Format
```
🔍 Search Results for 'query'
📊 Found X matching entries

1. Pattern (HIGH relevance)
   [Relevant pattern or approach]

2. Tool Usage (MEDIUM relevance)
   [Tool usage information]
```

### Insights Format
```
💡 Memory Insights (Last X Days)
🔄 Frequent Patterns: [Common task patterns]
✅ Successful Approaches: [What worked well]
🔧 Tool Usage Patterns: [Most used tools]
```

---

**Remember**: The memory and search enhancements work automatically in the background. The agent now has much better continuity and can find more current information without any special configuration needed from you! 
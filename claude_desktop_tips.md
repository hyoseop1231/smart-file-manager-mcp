# Claude Desktop MCP Tools - Best Practices

## 🚀 Quick Tips for Smooth Operation

### 1. Use Search First
Instead of complex operations, start with search:
- ✅ "Find PDF files on Desktop"
- ✅ "Show recent documents"
- ✅ "Search for project files"

### 2. Dry Run for Organization
Always preview before organizing:
- ✅ "Show me how files would be organized (dry run)"
- ❌ "Organize all my files" (takes too long)

### 3. Use Simple Methods
For immediate results:
- ✅ `method: "extension"` - Fast, by file type
- ✅ `method: "date"` - Quick, by date
- ⚠️ `method: "content"` - Slow, uses AI

### 4. Work with Smaller Sets
- ✅ "Organize PDF files in Downloads"
- ❌ "Organize entire Desktop" (too many files)

## 📝 Example Commands for Claude Desktop

### Quick Search
```
"Find Python files modified today"
"Show me large video files"
"Search for documents with 'project' in name"
```

### Smart Organization
```
"Preview organizing Downloads folder by file type"
"Show how Desktop files would be organized"
"Organize images from last week"
```

### Status Checking
```
"What files were indexed in the last hour?"
"Show indexing statistics"
"Check system health"
```

## 🔧 Troubleshooting

### If operations seem to "skip":
1. They're actually running in background
2. Check Docker logs: `docker logs smart-file-manager`
3. Use the status check script: `python check_task_status.py <task_id>`

### For faster results:
1. Use `dryRun: true`
2. Use `use_llm: false`
3. Search instead of organize
4. Work with specific file types

## 🎯 Recommended Workflow

1. **Search first**: Find what needs organizing
2. **Preview**: Use dry run to see changes
3. **Organize small batches**: Work with specific folders/types
4. **Verify**: Check results after operation

## 💡 Pro Tips

1. **Create folders first**: Set up your organization structure
2. **Use existing folders**: Like your 01_Projects, 02_Areas
3. **Regular maintenance**: Run quick searches daily
4. **Monitor indexing**: Check if new files are indexed

Remember: The MCP tools are designed for interactive use. Long operations work better through the web UI or scripts!
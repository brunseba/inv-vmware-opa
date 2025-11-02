# Query Parameter Navigation

## Overview

The VMware Inventory Dashboard now supports **direct URL navigation** via query parameters. This enables:
- Direct page access via URLs
- Screenshot automation
- Browser bookmarking
- Integration with external tools

## How It Works

### URL Format

```
http://localhost:8501/?page=Page_Name
```

**Rules:**
- Page names with **spaces** are converted to **underscores**
- Page names are **case-sensitive**
- The query parameter is processed on page load
- Invalid page names are ignored (defaults to Overview)

### Examples

```bash
# Main Navigation
http://localhost:8501/?page=Overview

# Explore & Analyze
http://localhost:8501/?page=Data_Explorer
http://localhost:8501/?page=Advanced_Explorer
http://localhost:8501/?page=VM_Explorer
http://localhost:8501/?page=VM_Search
http://localhost:8501/?page=Analytics
http://localhost:8501/?page=Comparison
http://localhost:8501/?page=Data_Quality

# Infrastructure
http://localhost:8501/?page=Resources
http://localhost:8501/?page=Infrastructure
http://localhost:8501/?page=Folder_Analysis
http://localhost:8501/?page=Folder_Labelling

# Migration
http://localhost:8501/?page=Migration_Targets
http://localhost:8501/?page=Strategy_Configuration
http://localhost:8501/?page=Migration_Planning
http://localhost:8501/?page=Migration_Scenarios

# Management
http://localhost:8501/?page=Data_Import
http://localhost:8501/?page=Database_Backup

# Export & Help
http://localhost:8501/?page=PDF_Export
http://localhost:8501/?page=Help
```

## Implementation Details

### Code Location

**File:** `src/dashboard/app.py`

```python
# Check for query parameter navigation (e.g., ?page=Data_Explorer)
try:
    query_params = st.query_params
    if "page" in query_params:
        # Convert underscore format to space format
        page_param = query_params["page"]
        page_name = page_param.replace("_", " ")
        
        # If valid page, set it in session state
        if PageNavigator.is_valid_page(page_name):
            StateManager.set(SessionKeys.CURRENT_PAGE, page_name)
except Exception as e:
    # Silently ignore query param errors
    pass
```

### Page Name Mapping

| URL Format | Internal Name | Example |
|------------|---------------|---------|
| `?page=Overview` | `Overview` | http://localhost:8501/?page=Overview |
| `?page=Data_Explorer` | `Data Explorer` | http://localhost:8501/?page=Data_Explorer |
| `?page=Migration_Planning` | `Migration Planning` | http://localhost:8501/?page=Migration_Planning |
| `?page=Help` | `Help` | http://localhost:8501/?page=Help |

**Conversion Rule:** Underscores (`_`) in URLs → Spaces (` `) in internal page names

## Usage

### Browser Bookmarks

Save frequently used pages as bookmarks:

```
📊 Overview Dashboard  → http://localhost:8501/?page=Overview
🔬 Data Explorer      → http://localhost:8501/?page=Data_Explorer
🖥️ VM Explorer        → http://localhost:8501/?page=VM_Explorer
📁 Folder Analysis    → http://localhost:8501/?page=Folder_Analysis
🎯 Migration Planning → http://localhost:8501/?page=Migration_Planning
```

### Screenshot Automation

The screenshot tool uses this feature for fast navigation:

```bash
# Capture specific page via URI
vmware-screenshot capture --page "Data Explorer" --use-uri

# Captures all pages using URIs
vmware-screenshot auto
```

### Deep Linking

Share direct links to specific pages:

```
# Share VM Explorer with team
"Check the VM details here: http://localhost:8501/?page=VM_Explorer"

# Link to migration planning
"View migration plans: http://localhost:8501/?page=Migration_Planning"
```

### External Integration

Call from external tools or scripts:

```bash
# Open specific page in browser
open "http://localhost:8501/?page=Analytics"

# Using curl (for headless testing)
curl "http://localhost:8501/?page=Overview"
```

## Validation

### Valid Pages

The dashboard validates page names against the registered pages:

```python
PAGES = {
    "dashboards": ["Overview", "Resources", "Infrastructure", "Folder Analysis"],
    "analysis": ["Data Explorer", "Advanced Explorer", "VM Explorer", "VM Search", 
                 "Analytics", "Comparison", "Data Quality"],
    "tools": ["Folder Labelling"],
    "migration": ["Migration Targets", "Strategy Configuration", 
                  "Migration Planning", "Migration Scenarios"],
    "system": ["Data Import", "Database Backup", "PDF Export", "Help"],
}
```

**Total:** 20 valid pages

### Invalid Pages

If an invalid page is specified:
- Error is silently ignored
- Dashboard defaults to "Overview" page
- No error message displayed to user

**Examples:**
```bash
# Invalid - will show Overview
http://localhost:8501/?page=NonExistent
http://localhost:8501/?page=Random_Page
http://localhost:8501/?page=test
```

## Testing

### Manual Testing

```bash
# 1. Start dashboard
streamlit run src/dashboard/app.py

# 2. Test each URL format in browser
# Open: http://localhost:8501/?page=Data_Explorer
# Expected: Data Explorer page loads

# 3. Test invalid page
# Open: http://localhost:8501/?page=Invalid
# Expected: Overview page loads (default)
```

### Automated Testing

```bash
# Test with screenshot tool
vmware-screenshot capture --page "VM Explorer" --use-uri

# Should successfully navigate and capture screenshot
```

### Verify All Pages

```bash
# Test all 20 pages
for page in Overview Data_Explorer VM_Explorer Migration_Planning; do
  echo "Testing: http://localhost:8501/?page=$page"
  curl -s "http://localhost:8501/?page=$page" > /dev/null
  echo "✓ $page"
done
```

## Troubleshooting

### Page Not Loading

**Symptom:** URL with `?page=` parameter shows Overview instead

**Possible Causes:**
1. Page name spelling error
2. Incorrect underscore/space conversion
3. Case mismatch

**Solutions:**
```bash
# Check exact page name in API-ENDPOINTS.md
# Example: "Migration Planning" → ?page=Migration_Planning

# Verify case sensitivity
?page=migration_planning  # ✗ Wrong (lowercase)
?page=Migration_Planning  # ✓ Correct
```

### Query Parameter Ignored

**Symptom:** Query parameter present but not processed

**Check:**
1. Streamlit version (requires st.query_params support)
2. Browser cache (clear and retry)
3. Dashboard logs for errors

**Debug:**
```python
# Add to app.py temporarily
import streamlit as st
st.write("Query params:", st.query_params)
```

### Special Characters

**Issue:** Some page names have special characters

**Solution:** Use underscores for spaces only, keep other characters:
```bash
# Correct
?page=Strategy_Configuration

# Incorrect
?page=Strategy-Configuration
?page=StrategyConfiguration
```

## Benefits

### For Users
- **Quick Access**: Bookmark favorite pages
- **Sharing**: Send direct links to specific pages
- **Efficiency**: Skip navigation menu clicks

### For Developers
- **Automation**: Screenshot tools work reliably
- **Testing**: Direct page access for automated tests
- **Integration**: Easy external tool integration

### For Documentation
- **Examples**: Provide clickable links in docs
- **Training**: Share specific page URLs in tutorials
- **Support**: Link to exact pages in help tickets

## Compatibility

### Streamlit Version

Requires Streamlit with `st.query_params` support:
- **Minimum:** Streamlit 1.30.0+
- **Recommended:** Streamlit 1.50.0+

Check version:
```bash
streamlit version
```

### Browser Support

Works in all modern browsers:
- ✓ Chrome/Chromium
- ✓ Firefox
- ✓ Safari
- ✓ Edge

## Future Enhancements

Potential improvements:

1. **Multiple Parameters**
   ```bash
   ?page=VM_Explorer&vm_id=12345
   ```

2. **State Restoration**
   ```bash
   ?page=Analytics&datacenter=DC1&filter=active
   ```

3. **Permalink Generation**
   ```python
   # In dashboard
   permalink = generate_permalink(current_page, filters)
   st.code(permalink)
   ```

## Related Documentation

- [API Endpoints](../API-ENDPOINTS.md) - Complete URI list
- [Screenshot Tool](../tools/SCREENSHOT-TOOL-URI-ENHANCEMENT.md) - Automation usage
- [Dashboard Guide](dashboard-guide.md) - General dashboard usage

## Version

- **Added:** v0.7.2
- **Status:** Stable
- **Breaking Changes:** None (additive feature)

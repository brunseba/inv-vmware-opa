# User Guide

Complete documentation for using the VMware Inventory OPA system.

## Quick Links

- **[Visual Guide](visual-guide.md)** - 📸 Complete visual tour with all 20 dashboard screenshots
- **[Dashboard Guide](dashboard.md)** - 📊 Detailed dashboard feature documentation
- **[CLI Commands](cli-commands.md)** - ⚡ Command-line interface reference
- **[PDF Export](pdf-export.md)** - 📄 Report generation guide
- **[Backup & Restore](backup-restore.md)** - 💾 Database management

---

## Getting Started

### New Users

1. **[Visual Guide](visual-guide.md)** - Start here! Browse all dashboard pages with screenshots
2. **[CLI Commands](cli-commands.md)** - Learn basic commands for data import
3. **[Dashboard Guide](dashboard.md)** - Deep dive into dashboard features

### Quick Start Flow

```bash
# 1. Import data
vmware-inv load inventory.xlsx --clear

# 2. View statistics
vmware-inv stats

# 3. Launch dashboard
vmware-dashboard

# 4. Browse pages (see Visual Guide for screenshots)
```

---

## Guide Overview

### 📸 Visual Guide (NEW)
**[visual-guide.md](visual-guide.md)**

Complete visual tour of all 20 dashboard pages:
- Screenshots for every page
- Feature descriptions
- Usage examples
- Tips and best practices
- Direct URL access for each page

**Perfect For:**
- Visual learners
- Quick reference
- Understanding dashboard layout
- Training new users

**Pages Covered:**
- 7 Exploration pages (Data Explorer, Analytics, VM Search, etc.)
- 4 Infrastructure pages (Resources, Folder Analysis, etc.)
- 4 Migration pages (Planning, Targets, Scenarios)
- 2 Management pages (Data Import, Database Backup)
- 2 Export & Help pages

---

### 📊 Dashboard Guide
**[dashboard.md](dashboard.md)**

Detailed documentation for dashboard features:
- Page-by-page feature descriptions
- Configuration options
- Performance tips
- Integration examples

**Perfect For:**
- Understanding feature details
- Advanced configuration
- Performance optimization
- Integration planning

---

### ⚡ CLI Commands
**[cli-commands.md](cli-commands.md)**

Command-line interface reference:
- All CLI commands with examples
- Data import/export
- Label management
- Anonymization (BETA)
- Database operations

**Perfect For:**
- Automation scripts
- Batch operations
- Programmatic access
- CI/CD integration

---

### 📄 PDF Export
**[pdf-export.md](pdf-export.md)**

Professional report generation:
- Report types (Standard, Extended, Summary)
- Configuration options
- Content sections
- Best practices

**Perfect For:**
- Executive reports
- Stakeholder presentations
- Documentation
- Compliance reporting

---

### 💾 Backup & Restore
**[backup-restore.md](backup-restore.md)**

Database management:
- Backup strategies
- Restore procedures
- Scheduled backups
- Disaster recovery

**Perfect For:**
- Data protection
- Version control
- Disaster recovery
- Change management

---

## By Use Case

### 📊 Daily Operations
1. [Visual Guide](visual-guide.md) - Overview page for health checks
2. [Dashboard Guide](dashboard.md) - Explore & Analyze pages
3. [CLI Commands](cli-commands.md) - Data updates

### 🔍 Deep Analysis
1. [Visual Guide](visual-guide.md) - Data Explorer, Analytics pages
2. [Dashboard Guide](dashboard.md) - Advanced features
3. [CLI Commands](cli-commands.md) - Custom queries

### 🚀 Migration Planning
1. [Visual Guide](visual-guide.md) - Migration pages (Targets, Planning, Scenarios)
2. [Dashboard Guide](dashboard.md) - Labelling system
3. [PDF Export](pdf-export.md) - Migration reports

### 📈 Executive Reporting
1. [Visual Guide](visual-guide.md) - Overview, Resources pages
2. [PDF Export](pdf-export.md) - Generate professional reports
3. [Dashboard Guide](dashboard.md) - Comparison views

### 🔧 System Administration
1. [CLI Commands](cli-commands.md) - Automation scripts
2. [Backup & Restore](backup-restore.md) - Data protection
3. [Dashboard Guide](dashboard.md) - Data Import, Database Backup pages

---

## Learning Path

### Beginner (Day 1)
```
1. Visual Guide - Browse overview and screenshots
2. Import first dataset using CLI
3. Explore Overview page in dashboard
4. Try VM Explorer page
```

### Intermediate (Week 1)
```
1. Review all pages in Visual Guide
2. Learn CLI commands for automation
3. Set up regular data imports
4. Generate first PDF report
5. Create database backups
```

### Advanced (Month 1)
```
1. Master all dashboard pages
2. Automate data pipeline with CLI
3. Use labelling system for organization
4. Plan migrations using migration pages
5. Set up scheduled reports and backups
```

---

## Navigation Tips

### Dashboard Navigation

**Sidebar Menu:**
- Click page names to navigate
- Categories are collapsible
- Current page is highlighted

**Direct URLs:**
- Bookmark: `http://localhost:8501/?page=Page_Name`
- Example: `http://localhost:8501/?page=Data_Explorer`

**See [Visual Guide](visual-guide.md) for all page URLs**

---

## Features by Category

### Data Exploration (7 pages)
- **Data Explorer** - Drag & drop analytics
- **Advanced Explorer** - SQL queries
- **VM Explorer** - Detailed VM inspection
- **VM Search** - Advanced search
- **Analytics** - Resource patterns
- **Comparison** - Side-by-side analysis
- **Data Quality** - Completeness checks

### Infrastructure (4 pages)
- **Resources** - Resource metrics
- **Infrastructure** - Topology view
- **Folder Analysis** - Folder-level analytics
- **Folder Labelling** - Label management

### Migration (4 pages)
- **Migration Targets** - Define targets
- **Strategy Configuration** - Configure strategies
- **Migration Planning** - Schedule migrations
- **Migration Scenarios** - Compare approaches

### Management (2 pages)
- **Data Import** - Excel import
- **Database Backup** - Backup/restore

### Export & Help (2 pages)
- **PDF Export** - Generate reports
- **Help** - Documentation

---

## Quick Reference

### Common Tasks

| Task | Guide | Page/Command |
|------|-------|--------------|
| Import data | [CLI Commands](cli-commands.md) | `vmware-inv load` |
| View dashboard | [Visual Guide](visual-guide.md) | All pages with screenshots |
| Search VMs | [Visual Guide](visual-guide.md) | VM Explorer, VM Search |
| Generate report | [PDF Export](pdf-export.md) | PDF Export page |
| Backup database | [Backup & Restore](backup-restore.md) | Database Backup page |
| Plan migration | [Visual Guide](visual-guide.md) | Migration pages |
| Analyze resources | [Visual Guide](visual-guide.md) | Resources, Analytics |
| Label VMs | [Dashboard Guide](dashboard.md) | Folder Labelling |

---

## Support

### Documentation
- [Visual Guide](visual-guide.md) - Screenshots and walkthroughs
- [Dashboard Guide](dashboard.md) - Detailed features
- [CLI Commands](cli-commands.md) - Command reference
- [FAQ](../faq.md) - Common questions
- [Troubleshooting](../troubleshooting.md) - Problem resolution

### Getting Help
1. Check relevant guide above
2. Search documentation
3. Review error messages
4. Check GitHub issues
5. Contact support

---

## What's New

### v0.7.2
- **Visual Guide** with all 20 screenshots
- Query parameter navigation
- Enhanced screenshot automation
- Complete page documentation

### v0.7.0
- Anonymization features (BETA)
- Enhanced folder analysis
- Improved labelling system
- PyGWalker integration

---

## Next Steps

- Browse [Visual Guide](visual-guide.md) to see all dashboard pages
- Read [Dashboard Guide](dashboard.md) for feature details
- Review [CLI Commands](cli-commands.md) for automation
- Check [PDF Export](pdf-export.md) for reporting needs

---

*For the best experience, start with the [Visual Guide](visual-guide.md) to see screenshots of all 20 dashboard pages!*

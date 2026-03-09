# Dashboard Simplification - March 2026

## Changes Made

### Removed Sections
The following three sections have been removed from the Streamlit dashboard to simplify navigation and focus on core renewal workflow features:

1. **🔍 Critique Agent** (formerly at line 646-723)
   - 9-point quality checklist UI
   - Live message testing interface
   - Pass/Regenerate/Block metrics display
   
2. **🔔 Human Queue** (formerly at line 724-771)
   - Human specialist queue management
   - Escalation case viewer
   - Specialist routing logic display

3. **💰 Financial Business Case** (formerly at line 772-859)
   - Cost savings breakdown
   - Revenue uplift projections
   - Implementation roadmap
   - Risk management tables

### Retained Functionality
- **Core critique and escalation logic remains functional** in the backend
- The "Run Journeys" demo page still calls `evaluate()` and `escalate()` functions
- Business metrics are still displayed in the Dashboard Overview page
- Journey tracking provides visibility into customer progress

### Navigation After Simplification
The dashboard now has 6 focused pages:

1. **📊 Dashboard Overview** - High-level KPIs and pipeline summary
2. **🔄 Customer Journey Tracker** - Stage-by-stage customer progress visualization
3. **▶️ Run Journeys (Demo)** - Live simulation of renewal workflows
4. **👥 Policyholder Pipeline** - Detailed customer listing by stage
5. **📋 Success Metrics Scorecard** - FY25 baseline vs FY26 targets
6. **🔭 Audit Log** - IRDAI compliance and observability

### Technical Details
- **Lines removed**: 217 lines (lines 643-859)
- **File size**: Reduced from 902 to 685 lines
- **Imports retained**: `evaluate`, `CritiqueVerdict`, `record_critique`, `escalate` (used by Run Journeys page)
- **Imports removed**: `get_queue`, `get_queue_stats`, `critique_summary`

### Rationale
The removed sections contained detailed operational views that are:
- More relevant for AI ops teams than business stakeholders
- Already captured in backend logic and audit logs
- Not essential for understanding the renewal pipeline flow

The simplified dashboard now focuses on:
- Customer journey visibility (new Journey Tracker page)
- Business outcomes (persistency, conversion metrics)
- Compliance and auditability (Audit Log)

### How to Restore
If you need to restore the removed sections, they can be found in git history:
```bash
git log --all --full-history -- dashboard.py
git show <commit-hash>:dashboard.py > dashboard_backup.py
```

## Current Status
✅ Dashboard running at http://0.0.0.0:8501  
✅ All 6 pages functional  
✅ No import errors  
✅ Backend critique and escalation logic intact

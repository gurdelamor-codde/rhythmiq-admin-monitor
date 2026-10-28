# RhythmIQ Admin Monitor

Admin-only phone-number monitoring dashboard.

This version is designed to let one admin:
- add phone numbers manually
- review the current team roster
- record communication activity events
- view simple behavioral state predictions
- monitor a basic leaderboard

No invite-code flow.
No messaging app tokens.
No external services required.

## Quick start (Windows)

From the repo root, run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\run_windows.ps1
```

Then open:
- API docs: http://localhost:8000/docs
- Frontend: http://localhost:5173

Login:
- admin@rhythmiq.io / admin123

## Notes

- This is a local monitoring app intended for admin use only.
- Phone numbers are stored directly as contacts.
- SQLite is used by default for simple local deployment.

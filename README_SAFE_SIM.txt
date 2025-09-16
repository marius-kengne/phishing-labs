SAFE SIMULATION - README
Files generated:
- safetest_send.py : send training emails (clearly identified)
- safetest_landing.py : optional Flask app to host landing page and log clicks
- targets.csv : example CSV with targets to edit
- safetest_log.csv / clicks.csv : created after runs to store logs

Important safety & legal notes:
- Only run this in an isolated lab environment with explicit consent from participants.
- Do NOT reuse templates that mimic real banks, gov services, or third-party brands without authorization.
- Do not collect real credentials. Use this only for education and awareness.
- If you will run multiple tests, keep logs private and share aggregated/anonymized results only.

Quick start:
1. Edit safetest_send.py CONFIG section (SMTP settings, LANDING_BASE)
2. Edit targets.csv and set consent=yes for test accounts
3. (Optional) run: python3 safetest_landing.py on your lab server to host the landing page
4. Run: python3 safetest_send.py
5. Inspect safetest_log.csv and clicks.csv for results

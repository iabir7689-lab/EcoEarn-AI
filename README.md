# ♻️ EcoEarn AI — Proper Streamlit Build

Bangladesh-focused AI waste-to-income prototype.

## Working modules
- Individual registration/login
- Secure password hashing
- Citizen and Collector roles
- Session-based access control
- Bangla + English UI
- Upload + live camera
- AI waste classification hook
- AI-generated image screening hook
- Duplicate-image protection
- Pickup requests
- Collector accept → assigned collector → complete workflow
- Atomic collection credit to prevent double payment
- Wallet + transaction ledger
- EcoPoints + leaderboard
- Waste market rates
- Profile + password change
- Restricted admin dashboard
- Waste statistics + map

## Fixes over earlier build
The registration/database error is handled by schema initialization and migration. The collector workflow now prevents another collector from taking an accepted job and prevents double-credit on completion.

## Streamlit Cloud
Deploy `app.py` from GitHub. Add optional secrets in App Settings → Secrets:

```toml
HF_TOKEN = "hf_xxx"
AI_DETECTOR_MODEL = "dima806/ai-generated-image-detection"
# Optional custom classifier:
# WASTE_MODEL = "your-model-id"
```

## Important production architecture
SQLite is fine for a prototype, but Streamlit Cloud local storage is not a durable production database. For a real public launch with persistent accounts, migrate users/jobs/wallets to Supabase/PostgreSQL and add OTP, GPS/time verification, collector QR/ID verification, audit logs and official bKash/Nagad/Rocket APIs.

Never put API keys or passwords in GitHub.

# EcoEarn AI v2
Python + Streamlit prototype for Bangladesh.

## New in v2
- Separate registration and login
- Individual account with hashed password
- Citizen / Collector roles
- Session-based authentication
- Persistent SQLite users, jobs, scans and transactions
- Bangla + English
- Working navigation and forms
- Camera/upload waste scan
- AI waste classification when HF_TOKEN is configured
- AI-generated image screening when HF_TOKEN is configured
- Conservative uncertainty handling
- Collector accept/complete workflow
- Wallet and EcoPoints
- Admin dashboard

## Streamlit Secrets
Optional:
```toml
HF_TOKEN = "hf_xxx"
AI_DETECTOR_MODEL = "dima806/ai-generated-image-detection"
```
Never commit secrets to GitHub.

## Run
pip install -r requirements.txt
streamlit run app.py

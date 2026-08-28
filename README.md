# ♻️ EcoEarn AI — Bangladesh

**Don't Throw It. Earn From It.**

A Python + Streamlit prototype for an AI-powered waste-to-income and circular-economy platform.

## Included features

- Citizen dashboard
- Waste photo upload + camera capture
- AI waste classification
- AI-generated-image/authenticity screening
- Indicative waste price estimation
- Pickup request workflow
- Collector dashboard
- Wallet + transaction ledger
- EcoPoints and green levels
- Admin/government environmental dashboard
- Waste activity chart + map
- Bangla 🇧🇩 + English 🇬🇧 UI
- SQLite local prototype database
- Anti-fraud gate for suspicious images

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## GitHub → Streamlit Cloud

1. Create a GitHub repository.
2. Upload `app.py`, `requirements.txt`, `.streamlit/config.toml`, and `README.md`.
3. Open Streamlit Community Cloud.
4. Deploy the repository and choose `app.py` as the main file.
5. Optional but recommended: open the app's **Settings → Secrets** and add:

```toml
HF_TOKEN = "hf_your_token"
AI_DETECTOR_MODEL = "dima806/ai-generated-image-detection"
```

The token must never be committed to GitHub.

## AI authenticity note

AI-image detection is probabilistic. The app intentionally treats uncertain results as **uncertain** rather than falsely claiming that an image is real. For a production deployment, combine the detector with:

- live camera capture
- one-time QR/OTP at collection
- collector verification
- duplicate/perceptual-hash checks
- server-side audit logs
- rate limits and abuse monitoring

## Production roadmap

- Real bKash/Nagad/Rocket merchant/payment integration
- Real collector geolocation and route optimization
- Verified recycler accounts
- Dynamic market prices from verified buyers
- Government API integration
- Bengali voice assistant
- Stronger multi-model waste detection
- Dedicated anti-fraud image-forensics service
- Cloud PostgreSQL instead of SQLite

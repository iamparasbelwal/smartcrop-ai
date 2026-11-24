# SmartCrop.AI

SmartCrop.AI is a Streamlit + Python demo for HIMOVATION 2026: a clean-label plant-based formulation co-pilot. It computes nutrition and cost from the local ingredient database in Python; outputs are starting points and need lab validation.

## Open in Antigravity / VS Code

1. Extract this zip.
2. Open the extracted folder in Antigravity (File > Open Folder).
3. Create a virtual environment and install dependencies:

```bash
# Windows (PowerShell)
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` if you need environment variables (Gemini integration is currently deferred; the app runs without it).

5. Run the app:

```bash
# Windows
.\.venv\Scripts\python.exe -m streamlit run app.py
# or double-click run.bat after creating .venv
```

```bash
# macOS / Linux
.venv/bin/python -m streamlit run app.py
```

The app opens at http://localhost:8501.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Lab admin | paras@smartcrop.ai | Admin@123 |
| Lab worker | shivam@smartcrop.ai | Worker@123 |
| Lab worker | shreyshi@smartcrop.ai | Worker@123 |

## Notes

- Demo/local authentication only - not production auth.
- Nutrition and cost are computed in Python from `data/ingredients.csv`; the what-if chat uses local rules (no AI model connected yet).
- Every output is labelled as a starting point that needs lab validation.
- To reset demo data, delete the `data/` folder and reload the app; it will reseed.

# G-Labs Studio

A standalone Windows desktop workspace for authorized G-Labs Webhook API and Workflow JSON automation.

## Included
- Studio desktop UI
- Webhook client for image/video/Grok/Meta/OpenAI/upscale endpoints
- Workflow JSON load/save/validation based on the supplied Workflow JSON Specification
- Local bridge
- Windows GitHub Actions build
- Sample workflow

## Security boundary
This implementation does not collect browser cookies, session/auth tokens, CAPTCHA tokens, or bypass access controls. Configure authorized Webhook API credentials locally.

## Build
`pip install -r requirements`
`pyinstaller --onefile --windowed desktop/main.py`

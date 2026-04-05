#!/bin/bash
pip install -r requirements.txt
python -m playwright install chromium --with-deps 2>/dev/null || python -m playwright install chromium
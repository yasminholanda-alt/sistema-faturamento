name: Manter app Streamlit acordado

on:
  schedule:
    - cron: "0 */4 * * *"
  workflow_dispatch:

jobs:
  keep-alive:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Instalar Playwright
        run: |
          pip install playwright
          playwright install --with-deps chromium

      - name: Visitar o app
        env:
          STREAMLIT_APP_URL: ${{ secrets.STREAMLIT_APP_URL }}
        run: python keep_alive.py

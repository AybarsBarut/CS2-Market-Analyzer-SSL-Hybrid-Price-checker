cs2 market analyzer

this is a simple script to pull cs2 item price history from the steam community market and apply some popular trading indicators (ut bot and ssl hybrid) to see how the prices are moving.

credits:
the technical analysis logic in this script is adapted into python from open-source indicators originally published on tradingview:
- UT Bot Alerts by QuantNomad
- SSL Hybrid by Mihkel00

requirements:
pip install streamlit pandas numpy requests pandas_ta plotly

running it:
streamlit run cs2_price_analysis.py
it should open automatically, but if it doesn't, just go to http://localhost:8501 in your browser.

troubleshooting:
steam limits how often you can ask for prices. if you get a 429 error or no data shows up, you hit the limit. 
to get around this, go to advanced settings in the app and paste your steamLoginSecure cookie from your browser. 
you can find it in your browser's dev tools under application -> storage -> cookies.

disclaimer:
i don't care if you lose money on cs2 skins or get your steam account banned. use at your own risk. this is not financial advice, just pulling some numbers and drawing lines.

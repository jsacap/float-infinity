import pandas as pd
import requests
import pandas_ta as ta
import numpy as np
import defs


def get_fx_data():
    fx_jpy_pairs = ['USD_JPY']
    jpy_dataframes = {}

    # Initialize a session
    session = requests.Session()

    for instrument in fx_jpy_pairs:
        url = f'{defs.OANDA_URL}/instruments/{instrument}/candles'

        params = {
            'count': 60,
            'granularity': 'H1',
            'price': "M",
        }

        response = session.get(url, params=params, headers=defs.SECURE_HEADER)

        if response.status_code == 200:
            data = response.json()

            my_data = []
            for candle in data['candles']:
                # Skip incomplete candles
                if not candle['complete']:
                    continue

                ohlc_data = {
                    'time': candle['time'],
                    'open': float(candle['mid']['o']),
                    'high': float(candle['mid']['h']),
                    'low': float(candle['mid']['l']),
                    'close': float(candle['mid']['c']),
                    'volume': candle['volume']
                }
                my_data.append(ohlc_data)

            jpy_df = pd.DataFrame(my_data)
            jpy_df['time'] = pd.to_datetime(jpy_df['time'])
            jpy_df.set_index('time', inplace=True)
            jpy_dataframes[instrument] = jpy_df

        else:
            print(f"Failed to fetch data for {
                  instrument}: {response.status_code}")
    return jpy_dataframes['USD_JPY']

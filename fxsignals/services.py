# Base
from django.conf import settings
import os

# Data manipulation
import requests
import pandas as pd
import pandas_ta as ta
import numpy as np

# Secure
import defs

# Charting
import seaborn as sns
import matplotlib.pyplot as plt


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


def trend_signals():
    fx_pairs = ['AUD_JPY', 'NZD_JPY', 'EUR_JPY', 'GBP_JPY', 'USD_JPY', 'AUD_USD', 'AUD_CAD',
                'NZD_USD', 'EUR_USD', 'GBP_USD', 'USD_CAD', 'XAU_USD', 'BTC_USD', 'WTICO_USD']
    timeframes = ['H1', 'H4', 'D']
    session = requests.Session()
    fx_dataframes = {}
    trend_df_columns = ['Asset'] + [f'MOMO_{timeframe}' for timeframe in timeframes] + [
        f'PATI_{timeframe}' for timeframe in timeframes]

    trend_data_list = []
    total_bytes = 0

    for instrument in fx_pairs:
        trend_data = {'Asset': instrument}
        for timeframe in timeframes:
            url = f'{defs.OANDA_URL}/instruments/{instrument}/candles'
            params = {'count': 60, 'granularity': timeframe, 'price': "M"}
            response = session.get(
                url, params=params, headers=defs.SECURE_HEADER)

            if response.status_code == 200:
                size_in_bytes = len(response.content)
                total_bytes += size_in_bytes
                data = response.json()
                my_data = [{'time': candle['time'], 'open': float(candle['mid']['o']), 'high': float(candle['mid']['h']), 'low': float(
                    candle['mid']['l']), 'close': float(candle['mid']['c']), 'volume': candle['volume']} for candle in data['candles'] if candle['complete']]
                precision = 3 if 'JPY' in instrument else 5
                df = pd.DataFrame(my_data)
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
                df['SMA_FAST'] = ta.sma(
                    df['close'], length=20).round(precision)
                df['SMA_SLOW'] = ta.sma(
                    df['close'], length=50).round(precision)
                df['MOMO'] = np.where(
                    df['SMA_FAST'] > df['SMA_SLOW'], 'Uptrend', 'Downtrend')
                df['RSI'] = ta.rsi(df['close'], length=14)
                fx_dataframes[(instrument, timeframe)] = df

                # Initialize variables for trend tracing logic
                df['Candle'] = np.select([df['close'] > df['open'], df['close'] < df['open']], [
                                         'Bull', 'Bear'], default='Doji')
                df['Trend'] = 'Neutral'
                df.at[df.index[0], 'Trend'] = 'Neutral'

                higher_high = None
                lower_low = None

                bullish_pullback_count = 0
                bearish_pullback_count = 0
                bullish_pullback = False
                bearish_pullback = False

                swing_high = None
                swing_low = None

                uptrend_lowest_pullback = None
                downtrend_highest_pullback = None

                previous_high = df['high'].iloc[0]
                previous_low = df['low'].iloc[0]

                current_trend = 'Neutral'
                df.iloc[0, df.columns.get_loc('Trend')] = current_trend

                df['Price_Status'] = None
                price_status = None

                # Iterating logic starts
                for i, row in df.iloc[1:].iterrows():
                    # Insert trend tracing logic here and update df['Trend'] accordingly
                    current_high = row['high']
                    current_low = row['low']
                    candle_type = row['Candle']
                    current_close = row['close']

                    # clear_output()
                    # Trend rotation
                    if current_trend == "Neutral":
                        if swing_low is None and swing_high is None:
                            swing_high = current_high
                            swing_low = current_low
                            higher_high = current_high
                            lower_low = current_low

                    if current_close > swing_high and current_close > higher_high:
                        current_trend = 'Uptrend'
                        bullish_pullback_count = 0
                        bullish_pullback = False
                        bearish_pullback_count = 0
                        bearish_pullback = False
                        if uptrend_lowest_pullback is not None:
                            swing_low = uptrend_lowest_pullback
                    elif current_close < swing_low and current_low < lower_low:
                        current_trend = 'Downtrend'
                        bearish_pullback_count = 0
                        bearish_pullback = False
                        bullish_pullback_count = 0
                        bullish_pullback = False
                        if downtrend_highest_pullback is not None:
                            swing_high = downtrend_highest_pullback
                    # Finding the range in the beginning of the dataset

                    df.at[i, 'Trend'] = current_trend

                    if bullish_pullback or bearish_pullback:
                        price_status = 'Consolidation'
                    else:
                        price_status = 'Extension'

                    df.at[i, 'Price_Status'] = price_status
                    # ================================================================================================== #

                    if current_trend == 'Uptrend':
                        if current_high > previous_high and current_low > swing_high and not bullish_pullback:
                            if higher_high is not None:
                                higher_high = max(higher_high, current_high)
                            else:
                                higher_high = current_high
                        if current_close < higher_high and candle_type == 'Bear':
                            bullish_pullback_count += 1
                        if bullish_pullback_count >= 2:
                            bullish_pullback = True
                            swing_high = higher_high

                        if bullish_pullback and current_close > swing_low:
                            if current_low < previous_low:
                                uptrend_lowest_pullback = current_low

                    elif current_trend == 'Downtrend':
                        if current_low < previous_low and current_low < swing_low and not bearish_pullback:
                            if lower_low is not None:
                                lower_low = min(lower_low, current_low)
                            else:
                                lower_low = current_low
                        if current_close > lower_low and candle_type == 'Bull':
                            bearish_pullback_count += 1
                        if bearish_pullback_count >= 2:
                            bearish_pullback = True
                            swing_low = lower_low

                        if bearish_pullback and current_close < swing_high:
                            if current_high > previous_high:
                                downtrend_highest_pullback = current_high
                                higher_high = current_high

                    df.at[i, 'Swing_high'] = swing_high
                    df.at[i, 'Swing_low'] = swing_low
                    previous_low = current_low
                    previous_high = current_high

                    # =================================================================================================================================

                # Extract the final 'Trend' value and update trend_data
                final_trend = df['Trend'].iloc[-1]
                column_name = f'PATI_{timeframe}'
                trend_data[column_name] = final_trend
                trend_data[f'MOMO_{timeframe}'] = df['MOMO'].iloc[-1]
            else:
                print(f"Failed to fetch data for {instrument} with granularity {
                      timeframe}: {response.status_code}")
                column_name = f'PATI_{timeframe}'
                trend_data[column_name] = 'Error'

        trend_data_list.append(trend_data)

    trend_df = pd.DataFrame(trend_data_list, columns=trend_df_columns)
    trend_df.set_index('Asset', inplace=True)

    total_kb = total_bytes / 1024
    total_mb = round((total_kb / 1024), 2)

    trend_df['Uptrend_Count'] = trend_df.apply(
        lambda row: (row == 'Uptrend').sum(), axis=1)
    trend_df['Downtrend_Count'] = trend_df.apply(
        lambda row: (row == 'Downtrend').sum(), axis=1)
    trend_df = trend_df.sort_index()

    return trend_df


def trend_heat_map(trend_df):
    image_path = os.path.join(
        settings.MEDIA_ROOT, 'images', 'latest_trend_heatmap.png')
    # Ensure the directory exists
    os.makedirs(os.path.dirname(image_path), exist_ok=True)

    trend_numeric = trend_df.replace(
        {'Uptrend': 1, 'Downtrend': -1, 'Neutral': 0})
    trend_signals = trend_numeric[[
        'MOMO_H1', 'MOMO_H4', 'MOMO_D', 'PATI_H1', 'PATI_H4', 'PATI_D']]

    plt.figure(figsize=(10, 8))
    sns.heatmap(trend_signals, cmap='RdYlGn', annot=True, fmt="d")
    plt.title('Trend Strength Heatmap')

    plt.savefig(image_path)
    plt.close()

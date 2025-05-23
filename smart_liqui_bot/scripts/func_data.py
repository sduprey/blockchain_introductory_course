#!/usr/bin/env python
# coding: utf-8

import requests
import json
import talib
from datetime import timezone
from datetime import timedelta
from datetime import datetime
from scipy import stats
import pandas as pd
import numpy as np
from numpy.lib.stride_tricks import as_strided as stride
import time
import math

def send_slack_message(message,incoming_web_hook=None):
    payload = '{"text":"%s"}'% message
    response = requests.post(incoming_web_hook, data=payload)
    print(response.text)

def from_inv_adj_price_to_tick(invertedPoolPrice, decimal0, decimal1, tickBasis):
    poolPrice = 1. / invertedPoolPrice
    poolPriceAdjusted = poolPrice * (math.pow(10, decimal1 - decimal0))
    tickDouble = math.log(poolPriceAdjusted) / math.log(tickBasis);
    return int(tickDouble);


def getLowerNearestTick(tick, tickSpacing):
    lower = tick - (tick % tickSpacing);
    return lower

def getUpperNearestTick(tick, tickSpacing):
    lower = tick - (tick % tickSpacing);
    upper = lower + tickSpacing;
    return upper;

def get_surrounding_ticks(current_inverted_pool_price, perc_distance):
    decimal0 = 6;
    decimal1 = 18;
    tickBasis = 1.0001;
    tickSpacing = 10;

    upper_inverted_pool_price = current_inverted_pool_price * (1. + perc_distance);
    lower_inverted_pool_price = current_inverted_pool_price * (1. - perc_distance);

    current_tick = from_inv_adj_price_to_tick(current_inverted_pool_price, decimal0, decimal1, tickBasis);
    lower_tick = from_inv_adj_price_to_tick(upper_inverted_pool_price, decimal0, decimal1, tickBasis);
    upper_tick = from_inv_adj_price_to_tick(lower_inverted_pool_price, decimal0, decimal1, tickBasis);

    nearest_upper_tick = getUpperNearestTick(upper_tick, tickSpacing);
    nearest_lower_tick = getLowerNearestTick(lower_tick, tickSpacing);

    return nearest_lower_tick, nearest_upper_tick

def roll(df, w):
    v = df.values
    d0, d1 = v.shape
    s0, s1 = v.strides
    restricted_length = d0 - (w - 1)
    a = stride(v, (restricted_length, w, d1), (s0, s0, s1))
    rolled_df = pd.concat({
        row: pd.DataFrame(values, columns=df.columns)
        for row, values in zip(df.index[-restricted_length:], a)
    })
    return rolled_df.groupby(level=0)

def compute_slope(slope_df):
    y = slope_df.values
    slope = stats.linregress(np.arange(len(y)), y).slope
    return slope

def compute_ranked_slope_continuous(short, center, epsi, lagging_df):
    lagging_df['rolling_slope_rank'] = lagging_df['rolling_slope'].rank(pct=True)
    if short:
        lagging_df['rolling_slope_rank'] = 2 * (lagging_df['rolling_slope_rank'] - center)
        lagging_df['rolling_slope_rank'] = lagging_df['rolling_slope_rank'].clip(-1, 1)
    gen_sig = lagging_df['rolling_slope_rank'].iloc[-1]
    return max(epsi - abs(gen_sig),0)

def compute_ranked_slope_continuous_asymetric(short, center, epsi, lagging_df):
    lagging_df['rolling_slope_rank'] = lagging_df['rolling_slope'].rank(pct=True)
    if short:
        lagging_df['rolling_slope_rank'] = 2 * (lagging_df['rolling_slope_rank'] - center)
        lagging_df['rolling_slope_rank'] = lagging_df['rolling_slope_rank'].clip(-1, 1)
    gen_sig = lagging_df['rolling_slope_rank'].iloc[-1]
    if lagging_df.index[-1][0]>=pd.to_datetime('2023-02-09 18:00:00'):
        timestamp_to_investigate = lagging_df.index[-1][0]
        print(f'to investigate {timestamp_to_investigate}')
    if gen_sig > epsi:
        return 0
    if gen_sig < 0:
        return 0
    return epsi - gen_sig


def compute_smart_liquidity_stages_with_earlycut(data_df = None, short = True, lookback_window=20, pente_window=25, center=0.5, epsilon=0.4, symmetric = False, early_cut = True, confidence_threshold = None):
    print(f'computing{lookback_window}_{pente_window}_{epsilon}')
    data_df['rolling_slope'] = data_df['close'].rolling(window=pente_window).apply(compute_slope)
    import functools
    if symmetric:
        go = functools.partial(compute_ranked_slope_continuous, short, center, epsilon)
    else:
        go = functools.partial(compute_ranked_slope_continuous_asymetric, short, center, epsilon)
    signal_df = roll(data_df, lookback_window).apply(go)
    signal_df = signal_df.to_frame()
    signal_df.columns = ['signal_gen']
    if early_cut:
        print('cutting signal as soon as it decreases')
        signal_df['previous_signal_gen'] = signal_df['signal_gen'].shift()
        signal_df['early_cut'] = signal_df['signal_gen']<signal_df['previous_signal_gen']
        signal_df['early_cut'] = ~signal_df['early_cut']
        signal_df['early_cut'] = signal_df['early_cut'].astype(float)
        signal_df['signal_gen_earlycut'] = signal_df['early_cut']*signal_df['signal_gen']
    else :
        signal_df['signal_gen_earlycut'] = signal_df['signal_gen']

    signal_df['confi'] = signal_df['signal_gen_earlycut'] >= confidence_threshold
    signal_df['confi'] = signal_df['confi'].astype(float)
    signal_df['signal_gen_earlycut_confi'] = signal_df['confi'] * signal_df['signal_gen_earlycut']

    signal_df['signal_gen_discrete'] =  signal_df['signal_gen_earlycut_confi']>0.
    signal_df['signal_gen_discrete'] =  signal_df['signal_gen_discrete'].astype(float)

    ##### computing the entering/outing signal
    counter = 0
    previous_signal_gen = np.nan
    we_enter = np.zeros(len(signal_df))
    we_out = np.zeros(len(signal_df))
    ###########
    ########### positive signal, out as soon as it decreases
    ###########
    signal_df['raw_signal_gen'] = signal_df['signal_gen_discrete']
    for i, row in signal_df.iterrows():
        if counter == 0:
            previous_signal_gen = row['raw_signal_gen']
            counter = counter + 1
            continue
        signal_gen = row['raw_signal_gen']
        if signal_gen != previous_signal_gen:
            if previous_signal_gen == 0:
                we_enter[counter] = 1
            if previous_signal_gen == 1:
                we_out[counter] = 1


        counter = counter + 1
        previous_signal_gen = signal_gen
    signal_df['we_enter'] = we_enter
    signal_df['we_out'] = we_out

    signal_df['signal'] = signal_df['signal_gen'].shift()
    data_df = pd.merge(data_df, signal_df, right_index=True, left_index=True)
    def curate_signals(row):
        if abs(row['close']) <= 1e-3:
            return np.nan
        else:
            return row['signal']

    data_df['signal'] = data_df.apply(curate_signals, axis=1)
    data_df = data_df.dropna()

    data_df['short_term_signal'] = data_df['signal']
    return data_df.copy()

def request_hour_data_paquet(url, me_ts, ssj):
    hours_url_request=url.format(ssj, me_ts)
#    print(hours_url_request)
    r = requests.get(hours_url_request)
    dataframe = None
    try:
        dataframe = pd.DataFrame(json.loads(r.text)['Data'])
    except Exception as e:
        print('no data')
    return dataframe

def fetch_crypto_hourly_data(ssj=None, local_root_directory=None, hourly_return_pkl_filename_suffix='_hourly_returns.pkl',refetch_all=True, daily_crypto_starting_day='2012-01-01', daily_crypto_ending_day=None, ssj_against='USDT', exchange = None, save_to_disk = False, api_key = None):
    dates_stub = daily_crypto_starting_day.strftime('%d_%b_%Y') + '_' + daily_crypto_ending_day.strftime('%d_%b_%Y')
    pickle_saving_path = local_root_directory + ssj + '_' + dates_stub + hourly_return_pkl_filename_suffix
    if refetch_all:
        year = datetime.now().year
        month = datetime.now().month
        day = datetime.now().day
        hour = datetime.utcnow().hour
        ts = datetime(year, month, day, tzinfo=timezone.utc).timestamp() + hour * 3600
        ts1 = ts - 2001 * 3600
        ts2 = ts1 - 2001 * 3600
        ts3 = ts2 - 2001 * 3600
        ts4 = ts3 - 2001 * 3600
        ts5 = ts4 - 2001 * 3600
        ts6 = ts5 - 2001 * 3600
        ts7 = ts6 - 2001 * 3600
        ts8 = ts7 - 2001 * 3600
        ts9 = ts8 - 2001 * 3600
        ts10 = ts9 - 2001 * 3600
        ts11 = ts10 - 2001 * 3600
        ts12 = ts11 - 2001 * 3600
        ts13 = ts12 - 2001 * 3600
        ts14 = ts13 - 2001 * 3600
        ts15 = ts14 - 2001 * 3600
        ts16 = ts15 - 2001 * 3600
        ts17 = ts16 - 2001 * 3600
        ts18 = ts17 - 2001 * 3600

        print('Loading data')
        if exchange is None:
            hours_url_request = 'https://min-api.cryptocompare.com/data/v2/histohour?fsym={}&tsym=' + ssj_against + '&toTs={}&limit=2000&api_key=0e292073c9cfe20444c5a44061329892d6e66fa1bba39290251cba517c6af446'
        else :
            hours_url_request = 'https://min-api.cryptocompare.com/data/v2/histohour?fsym={}&tsym=' + ssj_against + '&e=' + exchange + '&toTs={}&limit=2000&api_key=9978e840dc8ff425b3ca402f1ca4d49fb85edfddaaa4ed0e68fb097e4e402cf9'

        dataframe = None
        for me_timestamp in [ts18, ts17, ts16, ts15, ts14, ts13, ts12, ts11, ts10, ts9, ts8, ts7, ts6, ts5, ts4, ts3, ts2, ts1, ts]:
            print('waiting')
            time.sleep(1)
            df = request_hour_data_paquet(hours_url_request, me_timestamp, ssj)
            if df is not None:
                if dataframe is not None:
                    dataframe = dataframe.append(df, ignore_index=True)
                else:
                    dataframe = df.copy()

        dataframe['TimeTo'] = pd.to_datetime(dataframe['TimeTo'], unit='s')
        dataframe['TimeFrom'] = pd.to_datetime(dataframe['TimeFrom'], unit='s')
        data_df = pd.DataFrame.from_records(dataframe['Data'])
        data_df.index = dataframe.index

        dataframe = pd.merge(dataframe, data_df, left_index=True, right_index=True)

        dataframe = dataframe.sort_values(by=['time'])
        dataframe['timestamp'] = dataframe['time'].copy()
        dataframe['time'] = pd.to_datetime(dataframe['time'], unit='s')
        dataframe = dataframe.rename(columns={"time": "date"}, errors="raise")
        dataframe = dataframe.set_index(dataframe['date'])

        dataframe = dataframe.drop(columns=['date','volumefrom', 'conversionType', 'conversionSymbol' ])

        dataframe = dataframe.rename(columns ={'volumeto':'volume'})

        print('size fetched')
        print(dataframe.shape)
        dataframe = dataframe[dataframe.index >= daily_crypto_starting_day]
        print('size filtered after '+str(daily_crypto_starting_day))
        print(dataframe.shape)
        if save_to_disk:
            dataframe.to_pickle(pickle_saving_path)
    else:
        dataframe = pd.read_pickle(pickle_saving_path)
    return dataframe


def get_last_price(ssj = 'ETH', ssj_against = 'USDT'):
    r = requests.get(f'https://min-api.cryptocompare.com/data/price?fsym={ssj}&tsyms={ssj_against}')
    return json.loads(r.text)[ssj_against]


class AdvancedDataSignalAgent:
    def __init__(self):
        self.frequence = 'hourly'
        self.freqly_pkl_file_name_suffix = '_ ' + self.frequence + '_returns.pkl'
        self.ssj = 'ETH'
        self.ssj_against = 'USDT'
        self.lookback_window = 20
        self.pente_window = 25
        self.center = 0.5
        self.epsilon = 1.
        self.early_cut = False
        self.symmetric = True
        self.confidence_threshold = 0.15
        self.perc_dist = 0.07
        self.fees_multiplier = 1.4
        self.lagging_histo = 3
        self.slack_hook = '****'


    def get_initial_hourly_candles_histo(self, historical_number_of_days = 4):
        self.running_date = datetime.now()
        self.starting_date = self.running_date + timedelta(days=-historical_number_of_days)
        self.ssj = 'ETH'
        self.data_df = fetch_crypto_hourly_data(ssj=self.ssj, local_root_directory='None',
                                                            hourly_return_pkl_filename_suffix='_hourly_returns.pkl',
                                                            refetch_all=True,
                                                            daily_crypto_starting_day=self.starting_date,
                                                            daily_crypto_ending_day=self.running_date)

    def update_hourly_candles(self):
        self.running_date = datetime.now()
        self.starting_date = self.running_date + timedelta(hours=-3)
        self.update_data_df = fetch_crypto_hourly_data(ssj=self.ssj, local_root_directory='None',
                                                            hourly_return_pkl_filename_suffix='_hourly_returns.pkl',
                                                            refetch_all=True,
                                                            daily_crypto_starting_day=self.starting_date,
                                                            daily_crypto_ending_day=self.running_date)
        updated_df = pd.concat([self.data_df.copy(), self.update_data_df.copy()])
        #updated_df = updated_df.drop_duplicates()
        updated_df = updated_df.sort_index()
        updated_df = updated_df.reset_index()
        updated_df = updated_df.groupby('date').last()
        updated_df = updated_df.sort_index()
        self.data_df = updated_df.copy()
        print(f'new updated hourly candles {self.data_df.tail()}')


    def compute_signal(self,):
        data_df = compute_smart_liquidity_stages_with_earlycut(data_df=self.data_df.copy(),
                                                               lookback_window=self.lookback_window,
                                                               pente_window=self.pente_window, center=self.center,
                                                               epsilon=self.epsilon, symmetric=self.symmetric,
                                                               early_cut=self.early_cut,
                                                               confidence_threshold=self.confidence_threshold)

        signal_data_df = data_df[
            ['timestamp', 'rolling_slope', 'close', 'signal_gen', 'raw_signal_gen', 'we_enter', 'we_out']].copy()

        previous_signal = signal_data_df['signal_gen'].iloc[-2]
        generated_signal = signal_data_df['signal_gen'].iloc[-1]
        close = signal_data_df['close'].iloc[-1]

        raw_previous_signal = signal_data_df['raw_signal_gen'].iloc[-2]
        raw_generated_signal = signal_data_df['raw_signal_gen'].iloc[-1]

        lower_tick, upper_tick = get_surrounding_ticks(close, self.perc_dist)

        signal_update_dictionary = {
            'timestamp': str(datetime.now()),
            'previous_signal': raw_previous_signal,
            'generated_signal': raw_generated_signal,
            'previous_conf': previous_signal,
            'generated_conf': generated_signal,
            'close': close,
            'lower_tick': lower_tick,
            'upper_tick': upper_tick
        }
        payload_message = json.dumps(signal_update_dictionary)
        payload_message = payload_message.replace('"', '')
        payload_message = 'Production smart liquidity signal update payload : ' + payload_message
        send_slack_message(payload_message, incoming_web_hook=self.slack_hook)
        print(payload_message)
        return lower_tick, upper_tick, raw_previous_signal, raw_generated_signal


class SimpleDataSignalAgent:
    def __init__(self, perc_dist=0.4,  bound_trigger=0.1, price_reference = None):
        self.frequence = 'hourly'
        self.freqly_pkl_file_name_suffix = '_ ' + self.frequence + '_returns.pkl'
        self.ssj = 'ETH'
        self.ssj_against = 'USDT'
        self.perc_dist = perc_dist
        self.price_reference = price_reference
        self.bound_trigger = bound_trigger
        self.fees_multiplier = 1.4
        self.lagging_histo = 3
        self.slack_hook = '*****'


    def get_initial_hourly_candles_histo(self, historical_number_of_days = 4):
        self.running_date = datetime.now()
        self.starting_date = self.running_date + timedelta(days=-historical_number_of_days)
        self.ssj = 'ETH'
        self.data_df = fetch_crypto_hourly_data(ssj=self.ssj, local_root_directory='None',
                                                            hourly_return_pkl_filename_suffix='_hourly_returns.pkl',
                                                            refetch_all=True,
                                                            daily_crypto_starting_day=self.starting_date,
                                                            daily_crypto_ending_day=self.running_date)

    def update_hourly_candles(self):
        self.running_date = datetime.now()
        self.starting_date = self.running_date + timedelta(hours=-3)
        self.update_data_df = fetch_crypto_hourly_data(ssj=self.ssj, local_root_directory='None',
                                                            hourly_return_pkl_filename_suffix='_hourly_returns.pkl',
                                                            refetch_all=True,
                                                            daily_crypto_starting_day=self.starting_date,
                                                            daily_crypto_ending_day=self.running_date)
        updated_df = pd.concat([self.data_df.copy(), self.update_data_df.copy()])
        #updated_df = updated_df.drop_duplicates()
        updated_df = updated_df.sort_index()
        updated_df = updated_df.reset_index()
        updated_df = updated_df.groupby('date').last()
        updated_df = updated_df.sort_index()
        self.data_df = updated_df.copy()
        print(f'new updated hourly candles {self.data_df.tail()}')


    def compute_signal(self,):
        # data_df = compute_smart_liquidity_stages_with_earlycut(data_df=self.data_df.copy(),
        #                                                        lookback_window=self.lookback_window,
        #                                                        pente_window=self.pente_window, center=self.center,
        #                                                        epsilon=self.epsilon, symmetric=self.symmetric,
        #                                                        early_cut=self.early_cut,
        #                                                        confidence_threshold=self.confidence_threshold)
        #
        # signal_data_df = data_df[
        #     ['timestamp', 'rolling_slope', 'close', 'signal_gen', 'raw_signal_gen', 'we_enter', 'we_out']].copy()
        #

        current_price = get_last_price(ssj= self.ssj)
        actual_upper_bound = self.price_reference * (1 + self.perc_dist)
        actual_lower_bound = self.price_reference * (1 - self.perc_dist)
        rebalance = False
        if current_price >= actual_upper_bound * (1. - self.bound_trigger) or current_price <= actual_lower_bound * (
                1. + self.bound_trigger):
            self.price_reference = current_price
            print('we rebalance')
            rebalance = True

        # signal_data_df = self.data_df.copy()
        # signal_data_df['raw_signal_gen'] = 1.
        # signal_data_df['signal_gen'] = 1.
        #
        # close = signal_data_df['close'].iloc[-1]
        # raw_previous_signal = signal_data_df['raw_signal_gen'].iloc[-2]
        # raw_generated_signal = signal_data_df['raw_signal_gen'].iloc[-1]
        # previous_signal = signal_data_df['signal_gen'].iloc[-2]
        # generated_signal = signal_data_df['signal_gen'].iloc[-1]

        lower_tick, upper_tick = get_surrounding_ticks(current_price, self.perc_dist)

        signal_update_dictionary = {
            'timestamp': str(datetime.now()),
            'rebalance': rebalance,
            'close': current_price,
            'lower_tick': lower_tick,
            'upper_tick': upper_tick
        }
        payload_message = json.dumps(signal_update_dictionary)
        payload_message = payload_message.replace('"', '')
        payload_message = 'Production smart liquidity signal update payload : ' + payload_message
        send_slack_message(payload_message, incoming_web_hook=self.slack_hook)
        print(payload_message)
        return lower_tick, upper_tick, rebalance

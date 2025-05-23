#!/usr/bin/env python
# coding: utf-8

import schedule
import time
from datetime import datetime
from func_data import AdvancedDataSignalAgent, SimpleDataSignalAgent, get_last_price
from func_blockchain import BlockchainAgent, MetricsAgent

def run_advanced_bot(data_signal_agent = None, desequilibrium_threshold = 0.1):
    time_of_update = datetime.now()
    print(f'data, signal and position updating {time_of_update}')
    data_signal_agent.update_hourly_candles()
    lower_tick, upper_tick, raw_previous_signal, raw_generated_signal = data_signal_agent.compute_signal()
    print(f'lower_tick {lower_tick}')
    print(f'upper_tick {upper_tick}')
    print(f'raw_previous_signal {raw_previous_signal}')
    print(f'raw_generated_signal {raw_generated_signal}')
    metrics_agent = MetricsAgent()
    amount0, amount1, fee0, fee1, leftOver0, leftOver1 = metrics_agent.output_metrics()
    underlying_price = get_last_price()
    desequilibrium = abs(float(amount1)*float(underlying_price)-float(amount0))/max(float(amount1)*float(underlying_price),float(amount0))
    reequilibrate = None
    if desequilibrium >= desequilibrium_threshold:
        reequilibrate = True
    else:
        reequilibrate = False
    blockchain_agent = BlockchainAgent()
    blockchain_agent.manage_liquidity(raw_generated_signal = raw_generated_signal, raw_previous_signal = raw_previous_signal, lower_tick = lower_tick, upper_tick = upper_tick, reequilibrate=reequilibrate)
    metrics_agent.output_metrics()

def run_light_bot(data_signal_agent = None, desequilibrium_threshold = 0.1):
    time_of_update = datetime.now()
    print(f'data, signal and position updating {time_of_update}')
    data_signal_agent.update_hourly_candles()
    lower_tick, upper_tick, rebalance = data_signal_agent.compute_signal()
    print(f'lower_tick {lower_tick}')
    print(f'upper_tick {upper_tick}')
    print(f'rebalance {rebalance}')
    metrics_agent = MetricsAgent()
    amount0, amount1, fee0, fee1, leftOver0, leftOver1 = metrics_agent.output_metrics()
    underlying_price = get_last_price()
    desequilibrium = abs(float(amount1)*float(underlying_price)-float(amount0))/max(float(amount1)*float(underlying_price),float(amount0))
    print(f'desequilibrium {desequilibrium}')

    if rebalance:
        blockchain_agent = BlockchainAgent()
        blockchain_agent.rebalance_liquidity(lower_tick = lower_tick, upper_tick = upper_tick)
        metrics_agent.output_metrics()

if __name__ == '__main__':
    #algorithm_type = 'advanced'
    algorithm_type = 'simple'
    if algorithm_type == 'simple':
        price_reference = 2666.
        data_signal_agent = SimpleDataSignalAgent(price_reference = 1900.)
        data_signal_agent.get_initial_hourly_candles_histo()
        ###### to debug
        #run_light_bot(data_signal_agent=data_signal_agent)
        #raise Exception('mozer foker')
        #####
        schedule.every().hour.at("03:00").do(lambda: run_light_bot(data_signal_agent=data_signal_agent))
        while True:
            schedule.run_pending()
            time.sleep(40)
    else :
        data_signal_agent = AdvancedDataSignalAgent()
        data_signal_agent.get_initial_hourly_candles_histo()
        ###### to debug
        #run_light_bot(data_signal_agent=data_signal_agent)
        #raise Exception('mozer foker')
        #####
        schedule.every().hour.at("03:00").do(lambda : run_advanced_bot(data_signal_agent=data_signal_agent))
        while True:
            schedule.run_pending()
            time.sleep(40)




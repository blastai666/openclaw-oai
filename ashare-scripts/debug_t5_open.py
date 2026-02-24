#!/usr/bin/env python3
"""
调试T+5开盘价回测问题
"""

import os
import pandas as pd
from datetime import datetime

def debug_t5_open():
    """调试T+5开盘价回测"""
    data_path = "/Users/blastai/.openclaw/workspace-0011ai/ashare/backtest_data"
    csv_files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    
    # 选择第一只股票
    test_stock = csv_files[0]
    stock_code = test_stock.replace('.csv', '')
    file_path = os.path.join(data_path, test_stock)
    
    print(f"调试股票: {stock_code}")
    
    df = pd.read_csv(file_path)
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.sort_values('日期')
    
    print(f"数据范围: {df['日期'].min()} 到 {df['日期'].max()}")
    print(f"数据列: {list(df.columns)}")
    
    # 检查最近的交易日
    recent_dates = df['日期'].tail(10).tolist()
    print(f"\n最近10个交易日:")
    for date in recent_dates:
        print(f"  {date.strftime('%Y-%m-%d')}")
    
    # 测试一个具体的交易日
    test_date = recent_dates[-6]  # 选择倒数第6天，确保有T+5数据
    print(f"\n测试买入日期: {test_date.strftime('%Y-%m-%d')}")
    
    # 检查买入日数据
    buy_data = df[df['日期'] == test_date]
    if not buy_data.empty:
        buy_close = buy_data.iloc[0]['收盘']
        print(f"买入价格 (收盘): {buy_close}")
        
        # 找T+5日
        future_dates = df[df['日期'] > test_date]['日期'].tolist()
        if len(future_dates) >= 5:
            sell_date = future_dates[4]
            print(f"T+5卖出日期: {sell_date.strftime('%Y-%m-%d')}")
            
            sell_data = df[df['日期'] == sell_date]
            if not sell_data.empty:
                sell_open = sell_data.iloc[0]['开盘']
                print(f"卖出价格 (开盘): {sell_open}")
                
                return_rate = (sell_open - buy_close) / buy_close
                print(f"收益率: {return_rate:.3%}")
            else:
                print("T+5日无数据")
        else:
            print(f"后续交易日不足: {len(future_dates)} 天")
    else:
        print("买入日无数据")

if __name__ == "__main__":
    debug_t5_open()
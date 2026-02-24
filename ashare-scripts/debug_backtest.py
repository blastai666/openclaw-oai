#!/usr/bin/env python3
"""
调试版回测 - 输出详细日志找出问题
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def debug_backtest():
    """调试回测问题"""
    data_path = "/Users/blastai/.openclaw/workspace-0011ai/ashare/backtest_data"
    csv_files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    
    # 选择第一只股票进行调试
    test_stock = csv_files[0]
    stock_code = test_stock.replace('.csv', '')
    file_path = os.path.join(data_path, test_stock)
    
    print(f"调试股票: {stock_code}")
    
    df = pd.read_csv(file_path)
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.sort_values('日期')
    
    print(f"数据范围: {df['日期'].min()} 到 {df['日期'].max()}")
    print(f"数据行数: {len(df)}")
    
    # 测试最近的日期
    recent_date = datetime(2026, 2, 20)  # 最近的交易日
    print(f"\n测试日期: {recent_date}")
    
    # 检查该日期是否有数据
    date_mask = df['日期'] == recent_date
    print(f"该日期有数据: {date_mask.any()}")
    
    if date_mask.any():
        # 计算评分
        recent_data = df[df['日期'] <= recent_date].tail(60)
        print(f"近期数据行数: {len(recent_data)}")
        
        if len(recent_data) >= 20:
            current_price = recent_data.iloc[-1]['收盘']
            ma20 = recent_data['收盘'].rolling(20).mean().iloc[-1]
            ma60 = recent_data['收盘'].rolling(60).mean().iloc[-1]
            
            print(f"当前价格: {current_price}")
            print(f"MA20: {ma20}")
            print(f"MA60: {ma60}")
            
            # 计算各策略评分
            price_to_ma60 = current_price / ma60
            value_score = max(0, min(1, 0.8 - (price_to_ma60 - 1) * 2))
            print(f"价值策略评分: {value_score}")
            
            momentum_60d = (current_price - ma60) / ma60
            momentum_20d = (current_price - ma20) / ma20 if ma20 > 0 else 0
            industry_score = max(0, min(1, momentum_60d * 3 + momentum_20d * 2 + 0.5))
            print(f"产业策略评分: {industry_score}")
            
            # 检查T+5数据
            future_data = df[df['日期'] > recent_date].head(10)
            print(f"T+5后续数据行数: {len(future_data)}")
            if len(future_data) >= 5:
                sell_price = future_data.iloc[4]['收盘']
                buy_price = df[date_mask].iloc[0]['收盘']
                return_rate = (sell_price - buy_price) / buy_price
                print(f"T+5收益率: {return_rate:.3%}")
            else:
                print("T+5数据不足")
        else:
            print("近期数据不足20天")
    else:
        print("该日期无数据")

if __name__ == "__main__":
    debug_backtest()
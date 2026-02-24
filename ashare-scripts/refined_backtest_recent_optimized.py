#!/usr/bin/env python3
"""
优化版最近三个月回测 - 减少数据量提高速度
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

class OptimizedRecentBacktest:
    """优化版近期回测类"""
    
    def __init__(self, data_path: str = "/Users/blastai/.openclaw/workspace-0011ai/ashare/backtest_data"):
        self.data_path = data_path
        self.strategies = ['value', 'industry', 'emotion', 'trend', 'quant']
        self.stock_data = {}
        self.load_sample_data()
    
    def load_sample_data(self):
        """只加载50只代表性股票"""
        print(f"Loading sample data from {self.data_path}...")
        csv_files = [f for f in os.listdir(self.data_path) if f.endswith('.csv')]
        
        # 选择50只流动性好的股票（简化：前50个）
        selected_files = csv_files[:50]
        
        for i, csv_file in enumerate(selected_files):
            stock_code = csv_file.replace('.csv', '')
            file_path = os.path.join(self.data_path, csv_file)
            
            try:
                df = pd.read_csv(file_path)
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.sort_values('日期')
                self.stock_data[stock_code] = df
                
            except Exception as e:
                continue
        
        print(f"Successfully loaded {len(self.stock_data)} sample stocks")
    
    def calculate_simple_refined_scores(self, stock_df: pd.DataFrame, date: datetime) -> Dict[str, float]:
        """简化版精细化评分"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(60)
            if len(recent_data) < 20:
                return {s: 0.0 for s in self.strategies}
            
            current_price = recent_data.iloc[-1]['收盘']
            ma20 = recent_data['收盘'].rolling(20).mean().iloc[-1]
            ma60 = recent_data['收盘'].rolling(60).mean().iloc[-1]
            
            # 模拟精细化逻辑的简化版本
            # 价值策略：低估值+稳定
            value_score = max(0, min(1, 0.7 - (current_price / ma60 - 1)))
            
            # 产业策略：景气度向上
            industry_score = max(0, min(1, (current_price / ma60 - 1) * 2 + 0.5))
            
            # 情绪策略：量价配合
            volume_ratio = recent_data['成交量'].iloc[-1] / recent_data['成交量'].mean()
            price_momentum = (current_price / recent_data.iloc[-5]['收盘'] - 1) if len(recent_data) >= 5 else 0
            emotion_score = max(0, min(1, (volume_ratio + price_momentum) * 0.4))
            
            # 趋势策略：强势趋势
            trend_score = max(0, min(1, (current_price / ma20 - 1) * 3 + 0.5))
            
            # 量化策略：波动率收缩
            recent_vol = recent_data['收盘'].pct_change().tail(10).std()
            historical_vol = recent_data['收盘'].pct_change().tail(30).std()
            vol_contraction = max(0, min(1, (historical_vol - recent_vol) / historical_vol)) if historical_vol > 0 else 0
            quant_score = vol_contraction
            
            return {
                'value': value_score,
                'industry': industry_score,
                'emotion': emotion_score,
                'trend': trend_score,
                'quant': quant_score
            }
        except:
            return {s: 0.0 for s in self.strategies}
    
    def select_top3_by_strategy(self, date: datetime) -> Dict[str, List[str]]:
        """按策略选出TOP3股票"""
        all_scores = {strategy: [] for strategy in self.strategies}
        
        for stock_code, stock_df in self.stock_data.items():
            if stock_df['日期'].max() < date:
                continue
                
            scores = self.calculate_simple_refined_scores(stock_df, date)
            for strategy, score in scores.items():
                if score > 0.3:  # 只考虑有潜力的股票
                    all_scores[strategy].append((stock_code, score))
        
        top3_by_strategy = {}
        for strategy in self.strategies:
            if all_scores[strategy]:
                sorted_stocks = sorted(all_scores[strategy], key=lambda x: x[1], reverse=True)
                top3_by_strategy[strategy] = [stock[0] for stock in sorted_stocks[:3]]
            else:
                top3_by_strategy[strategy] = []
        
        return top3_by_strategy
    
    def backtest_t_plus_5(self, stock_code: str, buy_date: datetime) -> Tuple[float, bool]:
        """T+5日收益回测"""
        if stock_code not in self.stock_data:
            return 0.0, False
            
        stock_df = self.stock_data[stock_code]
        buy_mask = stock_df['日期'] == buy_date
        
        if not buy_mask.any():
            return 0.0, False
        
        buy_price = stock_df[buy_mask].iloc[0]['收盘']
        future_data = stock_df[stock_df['日期'] > buy_date].head(8)  # 最多看8天
        
        if future_data.empty:
            return 0.0, False
        
        # 第5个交易日
        sell_price = future_data.iloc[min(4, len(future_data)-1)]['收盘']
        return_rate = (sell_price - buy_price) / buy_price
        is_profit = return_rate > 0
        
        return return_rate, is_profit
    
    def execute_recent_backtest(self, months: int = 3) -> Dict:
        """执行最近N个月的回测"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*30)
        
        print(f"执行最近{months}个月回测 (样本测试): {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        
        backtest_results = {strategy: {'trades': [], 'win_rate': 0, 'avg_return': 0} 
                           for strategy in self.strategies}
        
        # 只测试每周一个交易日以加速
        current_date = start_date
        test_dates = []
        
        while current_date <= end_date:
            if current_date.weekday() == 0:  # 只测试周一
                test_dates.append(current_date)
            current_date += timedelta(days=1)
        
        print(f"将测试 {len(test_dates)} 个交易日...")
        
        for i, test_date in enumerate(test_dates):
            try:
                top3_by_strategy = self.select_top3_by_strategy(test_date)
                
                for strategy, stocks in top3_by_strategy.items():
                    for stock in stocks:
                        return_rate, is_profit = self.backtest_t_plus_5(stock, test_date)
                        if return_rate != 0.0:
                            backtest_results[strategy]['trades'].append({
                                'date': test_date.strftime('%Y-%m-%d'),
                                'stock': stock,
                                'return': return_rate,
                                'profit': is_profit
                            })
                
                if (i + 1) % 10 == 0:
                    print(f"已处理 {i + 1}/{len(test_dates)} 个交易日...")
                    
            except Exception as e:
                continue
        
        # 计算结果
        for strategy in self.strategies:
            trades = backtest_results[strategy]['trades']
            if trades:
                profits = [trade['profit'] for trade in trades]
                returns = [trade['return'] for trade in trades]
                backtest_results[strategy]['win_rate'] = sum(profits) / len(profits)
                backtest_results[strategy]['avg_return'] = sum(returns) / len(returns)
        
        return backtest_results

def main():
    """主函数"""
    print("=== 优化版最近三个月回测（样本测试） ===")
    
    backtester = OptimizedRecentBacktest()
    results = backtester.execute_recent_backtest(months=3)
    
    print("\n=== 样本回测结果（最近3个月） ===")
    for strategy, stats in results.items():
        if stats['trades']:
            print(f"{strategy}: 胜率={stats['win_rate']:.3f}, 平均收益={stats['avg_return']:.3%}, 交易次数={len(stats['trades'])}")
        else:
            print(f"{strategy}: 无有效交易")
    
    # 保存结果
    output_path = "/Users/blastai/.openclaw/workspace-0011ai/ashare/refined_recent_sample_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n样本回测结果已保存到: {output_path}")

if __name__ == "__main__":
    main()
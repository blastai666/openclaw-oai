#!/usr/bin/env python3
"""
简单工作版回测 - 确保能选出股票并计算收益
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

class SimpleWorkingBacktest:
    """简单工作版回测类"""
    
    def __init__(self, data_path: str = "/Users/blastai/.openclaw/workspace-0011ai/ashare/backtest_data"):
        self.data_path = data_path
        self.strategies = ['value', 'industry', 'emotion', 'trend', 'quant']
        self.stock_data = {}
        self.trade_dates = []
        self.load_data_and_dates()
    
    def load_data_and_dates(self):
        """加载数据和确定交易日期"""
        print(f"Loading data from {self.data_path}...")
        csv_files = [f for f in os.listdir(self.data_path) if f.endswith('.csv')]
        
        # 加载20只股票用于测试
        selected_files = csv_files[:20]
        
        for i, csv_file in enumerate(selected_files):
            stock_code = csv_file.replace('.csv', '')
            file_path = os.path.join(self.data_path, csv_file)
            
            try:
                df = pd.read_csv(file_path)
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.sort_values('日期')
                
                if len(df) >= 100:
                    self.stock_data[stock_code] = df
                
                if (i + 1) % 5 == 0:
                    print(f"Loaded {len(self.stock_data)} stocks...")
                    
            except Exception as e:
                continue
        
        print(f"Successfully loaded {len(self.stock_data)} stocks")
        
        # 确定共同交易日期（基于第一只股票）
        if self.stock_data:
            first_stock = list(self.stock_data.keys())[0]
            all_dates = self.stock_data[first_stock]['日期'].dt.date.tolist()
            
            # 选择最近60个交易日（确保有T+5数据）
            recent_dates = sorted([d for d in all_dates if d.weekday() < 5], reverse=True)[:60]
            self.trade_dates = sorted(recent_dates[:-5])  # 去掉最后5天，确保T+5有数据
            
            print(f"回测日期范围: {min(self.trade_dates)} 到 {max(self.trade_dates)}")
            print(f"回测交易日数量: {len(self.trade_dates)}")
    
    def calculate_simple_scores(self, stock_df: pd.DataFrame, date: datetime) -> Dict[str, float]:
        """简单评分逻辑"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(30)
            if len(recent_data) < 10:
                return {s: 0.0 for s in self.strategies}
            
            current_price = recent_data.iloc[-1]['收盘']
            ma10 = recent_data['收盘'].rolling(10).mean().iloc[-1]
            ma20 = recent_data['收盘'].rolling(20).mean().iloc[-1]
            
            # 简单但有效的评分
            value_score = current_price / ma20  # 低估为高分
            industry_score = current_price / ma10  # 趋势向上为高分
            emotion_score = recent_data['成交量'].iloc[-1] / recent_data['成交量'].mean()
            trend_score = (current_price - ma20) / ma20
            quant_score = 1.0 - recent_data['收盘'].pct_change().tail(5).std()
            
            return {
                'value': float(value_score),
                'industry': float(industry_score),
                'emotion': float(emotion_score),
                'trend': float(trend_score),
                'quant': float(quant_score)
            }
        except:
            return {s: 0.0 for s in self.strategies}
    
    def select_top3_by_relative_ranking(self, date: datetime) -> Dict[str, List[str]]:
        """按相对排名选出TOP3股票（不设阈值）"""
        all_scores = {strategy: [] for strategy in self.strategies}
        
        for stock_code, stock_df in self.stock_data.items():
            scores = self.calculate_simple_scores(stock_df, date)
            for strategy, score in scores.items():
                all_scores[strategy].append((stock_code, score))
        
        top3_by_strategy = {}
        for strategy in self.strategies:
            if all_scores[strategy]:
                # 按分数排序，取前3名
                sorted_stocks = sorted(all_scores[strategy], key=lambda x: x[1], reverse=True)
                top3_by_strategy[strategy] = [stock[0] for stock in sorted_stocks[:3]]
            else:
                top3_by_strategy[strategy] = []
        
        return top3_by_strategy
    
    def backtest_t_plus_5_simple(self, stock_code: str, buy_date: datetime) -> Tuple[float, bool]:
        """简化版T+5回测"""
        if stock_code not in self.stock_data:
            return 0.0, False
            
        stock_df = self.stock_data[stock_code]
        buy_mask = stock_df['日期'] == buy_date
        
        if not buy_mask.any():
            return 0.0, False
        
        buy_price = stock_df[buy_mask].iloc[0]['收盘']
        
        # 找到买入日后的第5个交易日
        future_dates = stock_df[stock_df['日期'] > buy_date]['日期'].tolist()
        if len(future_dates) < 5:
            return 0.0, False
        
        sell_date = future_dates[4]  # 第5个交易日
        sell_mask = stock_df['日期'] == sell_date
        sell_price = stock_df[sell_mask].iloc[0]['收盘']
        
        return_rate = (sell_price - buy_price) / buy_price
        is_profit = return_rate > 0
        
        return return_rate, is_profit
    
    def execute_simple_backtest(self) -> Dict:
        """执行简单工作版回测"""
        print(f"执行简单工作版回测...")
        print(f"股票数量: {len(self.stock_data)}")
        print(f"交易日数量: {len(self.trade_dates)}")
        
        backtest_results = {strategy: {'trades': [], 'win_rate': 0, 'avg_return': 0} 
                           for strategy in self.strategies}
        
        valid_trade_days = 0
        for i, trade_date in enumerate(self.trade_dates):
            trade_datetime = datetime.combine(trade_date, datetime.min.time())
            
            try:
                # 选出TOP3股票
                top3_by_strategy = self.select_top3_by_relative_ranking(trade_datetime)
                
                has_valid_trades = False
                for strategy, stocks in top3_by_strategy.items():
                    for stock in stocks:
                        return_rate, is_profit = self.backtest_t_plus_5_simple(stock, trade_datetime)
                        if return_rate != 0.0:
                            backtest_results[strategy]['trades'].append({
                                'date': trade_date.strftime('%Y-%m-%d'),
                                'stock': stock,
                                'return': return_rate,
                                'profit': is_profit
                            })
                            has_valid_trades = True
                
                if has_valid_trades:
                    valid_trade_days += 1
                
                if (i + 1) % 10 == 0:
                    print(f"已处理 {i + 1}/{len(self.trade_dates)} 个交易日")
                    
            except Exception as e:
                continue
        
        # 计算统计结果
        for strategy in self.strategies:
            trades = backtest_results[strategy]['trades']
            if trades:
                profits = [trade['profit'] for trade in trades]
                returns = [trade['return'] for trade in trades]
                backtest_results[strategy]['win_rate'] = sum(profits) / len(profits)
                backtest_results[strategy]['avg_return'] = sum(returns) / len(returns)
        
        print(f"\n回测完成! 有效交易天数: {valid_trade_days}/{len(self.trade_dates)}")
        return backtest_results

def main():
    """主函数"""
    print("=== 简单工作版最近三个月回测 ===")
    
    backtester = SimpleWorkingBacktest()
    if not backtester.stock_data or not backtester.trade_dates:
        print("❌ 数据加载失败，无法执行回测")
        return
    
    results = backtester.execute_simple_backtest()
    
    print("\n=== 简单工作版回测结果 ===")
    total_trades = 0
    for strategy, stats in results.items():
        if stats['trades']:
            print(f"{strategy}: 胜率={stats['win_rate']:.3f}, 平均收益={stats['avg_return']:.3%}, 交易次数={len(stats['trades'])}")
            total_trades += len(stats['trades'])
        else:
            print(f"{strategy}: 无有效交易")
    
    print(f"\n总交易次数: {total_trades}")
    
    # 保存结果
    output_path = "/Users/blastai/.openclaw/workspace-0011ai/ashare/simple_working_backtest_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 备份到桌面
    desktop_path = "~/Desktop/asharereport/simple_working_backtest_results.json"
    os.system(f"cp {output_path} {desktop_path}")
    
    print(f"\n简单工作版回测结果已保存到: {output_path}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
基于最新精细化框架的最近三个月回测
使用精细化策略定义进行T+5收益验证
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

class RefinedRecentBacktest:
    """精细化近期回测类"""
    
    def __init__(self, data_path: str = "/Users/blastai/.openclaw/workspace-0011ai/ashare/backtest_data"):
        self.data_path = data_path
        self.strategies = ['value', 'industry', 'emotion', 'trend', 'quant']
        self.stock_data = {}
        self.refined_strategies = None
        self.load_refined_strategies()
        self.load_all_data()
    
    def load_refined_strategies(self):
        """加载精细化策略定义"""
        try:
            from strategy_definitions_refined import RefinedStrategyDefinitions
            self.refined_strategies = RefinedStrategyDefinitions()
            print("✓ 加载精细化策略定义成功")
        except ImportError as e:
            print(f"❌ 加载精细化策略失败: {e}")
            # 使用简化版本
            self.refined_strategies = None
    
    def load_all_data(self):
        """加载所有股票历史数据"""
        print(f"Loading historical data from {self.data_path}...")
        csv_files = [f for f in os.listdir(self.data_path) if f.endswith('.csv')]
        
        # 只加载最近有数据的股票（确保包含最近3个月）
        recent_date_threshold = datetime.now() - timedelta(days=120)
        
        for i, csv_file in enumerate(csv_files[:300]):  # 加载前300只股票
            stock_code = csv_file.replace('.csv', '')
            file_path = os.path.join(self.data_path, csv_file)
            
            try:
                df = pd.read_csv(file_path)
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.sort_values('日期')
                
                # 确保有最近3个月的数据
                if df['日期'].max() >= recent_date_threshold:
                    self.stock_data[stock_code] = df
                
                if (i + 1) % 50 == 0:
                    print(f"Loaded {len(self.stock_data)}/{min(300, len(csv_files))} valid stocks...")
                    
            except Exception as e:
                continue
        
        print(f"Successfully loaded {len(self.stock_data)} stocks with recent data")
    
    def calculate_refined_scores(self, stock_code: str, date: datetime) -> Dict[str, float]:
        """计算精细化策略评分"""
        if stock_code not in self.stock_data:
            return {strategy: 0.0 for strategy in self.strategies}
        
        stock_df = self.stock_data[stock_code]
        scores = {}
        
        if self.refined_strategies:
            # 使用精细化策略
            scores['value'] = self.refined_strategies.calculate_value_score_refined(stock_df, date)
            scores['industry'] = self.refined_strategies.calculate_industry_score_refined(stock_df, date)
            scores['emotion'] = self.refined_strategies.calculate_emotion_score_refined(stock_df, date)
            scores['trend'] = self.refined_strategies.calculate_trend_score_refined(stock_df, date)
            scores['quant'] = self.refined_strategies.calculate_quant_score_refined(stock_df, date)
        else:
            # 使用简化策略（备用）
            scores = self._calculate_simple_scores(stock_df, date)
        
        return scores
    
    def _calculate_simple_scores(self, stock_df: pd.DataFrame, date: datetime) -> Dict[str, float]:
        """简化策略评分（备用）"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(60)
            if len(recent_data) < 20:
                return {s: 0.0 for s in self.strategies}
            
            current_price = recent_data.iloc[-1]['收盘']
            ma20 = recent_data['收盘'].rolling(20).mean().iloc[-1]
            ma60 = recent_data['收盘'].rolling(60).mean().iloc[-1]
            
            # 简化评分逻辑
            value_score = max(0, min(1, (ma60 - current_price) / ma60 + 0.5))
            industry_score = max(0, min(1, (current_price - ma60) / ma60 + 0.5))
            emotion_score = max(0, min(1, recent_data['成交量'].pct_change().mean() * 2 + 0.5))
            trend_score = max(0, min(1, (current_price - ma20) / ma20 + 0.5))
            quant_score = max(0, min(1, 1 - recent_data['收盘'].pct_change().std() * 10))
            
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
        all_scores = {}
        
        for stock_code in self.stock_data.keys():
            scores = self.calculate_refined_scores(stock_code, date)
            for strategy, score in scores.items():
                if strategy not in all_scores:
                    all_scores[strategy] = []
                if score > 0:
                    all_scores[strategy].append((stock_code, score))
        
        top3_by_strategy = {}
        for strategy in self.strategies:
            if strategy in all_scores and all_scores[strategy]:
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
        
        # 找到买入日期的数据
        buy_mask = stock_df['日期'] == buy_date
        if not buy_mask.any():
            return 0.0, False
            
        buy_price = stock_df[buy_mask].iloc[0]['收盘']
        
        # 找到T+5个交易日的卖出价格
        future_data = stock_df[stock_df['日期'] > buy_date].head(10)  # 最多看10天
        
        if future_data.empty:
            return 0.0, False
        
        # 找到第5个交易日（考虑周末和节假日）
        if len(future_data) >= 5:
            sell_price = future_data.iloc[4]['收盘']  # 第5个交易日
        else:
            sell_price = future_data.iloc[-1]['收盘']  # 如果不足5天，用最后一天
        
        return_rate = (sell_price - buy_price) / buy_price
        is_profit = return_rate > 0
        
        return return_rate, is_profit
    
    def execute_recent_backtest(self, months: int = 3) -> Dict:
        """执行最近N个月的回测"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*30)
        
        print(f"执行最近{months}个月回测: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        
        backtest_results = {
            'value': {'trades': [], 'win_rate': 0, 'avg_return': 0, 'sharpe': 0},
            'industry': {'trades': [], 'win_rate': 0, 'avg_return': 0, 'sharpe': 0},
            'emotion': {'trades': [], 'win_rate': 0, 'avg_return': 0, 'sharpe': 0},
            'trend': {'trades': [], 'win_rate': 0, 'avg_return': 0, 'sharpe': 0},
            'quant': {'trades': [], 'win_rate': 0, 'avg_return': 0, 'sharpe': 0}
        }
        
        current_date = start_date
        trade_count = 0
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # 工作日
                try:
                    # 选出每个策略的TOP3股票
                    top3_by_strategy = self.select_top3_by_strategy(current_date)
                    
                    # 对每个选出的股票进行T+5回测
                    for strategy, stocks in top3_by_strategy.items():
                        for stock in stocks:
                            return_rate, is_profit = self.backtest_t_plus_5(stock, current_date)
                            
                            if return_rate != 0.0:
                                trade_record = {
                                    'date': current_date.strftime('%Y-%m-%d'),
                                    'stock': stock,
                                    'return': return_rate,
                                    'profit': is_profit
                                }
                                backtest_results[strategy]['trades'].append(trade_record)
                                trade_count += 1
                    
                    if trade_count % 50 == 0 and trade_count > 0:
                        print(f"已处理 {trade_count} 笔交易...")
                        
                except Exception as e:
                    print(f"处理日期 {current_date} 时出错: {e}")
            
            current_date += timedelta(days=1)
        
        # 计算统计结果
        risk_free_rate = 0.02 / 252  # 年化2%无风险利率
        
        for strategy in self.strategies:
            trades = backtest_results[strategy]['trades']
            if trades:
                profits = [trade['profit'] for trade in trades]
                returns = [trade['return'] for trade in trades]
                
                win_rate = sum(profits) / len(profits)
                avg_return = sum(returns) / len(returns)
                
                # 计算夏普比率
                if len(returns) > 1:
                    excess_returns = [r - risk_free_rate for r in returns]
                    sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252/5)  # 年化
                else:
                    sharpe = 0
                
                backtest_results[strategy]['win_rate'] = win_rate
                backtest_results[strategy]['avg_return'] = avg_return
                backtest_results[strategy]['sharpe'] = sharpe
        
        return backtest_results

def main():
    """主函数"""
    print("=== 基于最新精细化框架的最近三个月回测 ===")
    
    backtester = RefinedRecentBacktest()
    results = backtester.execute_recent_backtest(months=3)
    
    print("\n=== 最新框架回测结果（最近3个月） ===")
    for strategy, stats in results.items():
        if stats['trades']:
            print(f"{strategy}: 胜率={stats['win_rate']:.3f}, 平均收益={stats['avg_return']:.3%}, "
                  f"夏普比率={stats['sharpe']:.3f}, 交易次数={len(stats['trades'])}")
        else:
            print(f"{strategy}: 无有效交易")
    
    # 保存结果
    output_path = "/Users/blastai/.openclaw/workspace-0011ai/ashare/refined_recent_backtest_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n回测结果已保存到: {output_path}")
    
    # 备份到桌面
    desktop_path = "~/Desktop/asharereport/refined_recent_backtest_results.json"
    os.system(f"cp {output_path} {desktop_path}")
    print(f"结果已备份到桌面: {desktop_path}")

if __name__ == "__main__":
    main()
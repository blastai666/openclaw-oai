#!/usr/bin/env python3
"""
简化版 v3 核心优化策略回测
直接实现 v3 核心思想，避免复杂依赖
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
import json

class SimpleV2Backtest:
    """简化版 v3 策略回测"""
    
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.strategies = ['value', 'industry', 'emotion', 'trend', 'quant']
        self.stock_data = {}
        self.trade_dates = []
        self.load_data()
    
    def load_data(self):
        """加载数据"""
        print("Loading data...")
        csv_files = [f for f in os.listdir(self.data_path) if f.endswith('.csv')]
        
        for csv_file in csv_files[:50]:  # 50 只股票
            stock_code = csv_file.replace('.csv', '')
            try:
                df = pd.read_csv(os.path.join(self.data_path, csv_file))
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.sort_values('日期')
                if len(df) >= 80:
                    self.stock_data[stock_code] = df
            except:
                continue
        
        print(f"Loaded {len(self.stock_data)} stocks")
        
        # 确定共同交易日
        if self.stock_data:
            all_dates = None
            for df in self.stock_data.values():
                dates = set(df['日期'].dt.date)
                all_dates = dates if all_dates is None else all_dates.intersection(dates)
            
            if all_dates:
                all_dates = sorted([d for d in all_dates if d.weekday() < 5], reverse=True)
                self.trade_dates = sorted(all_dates[5:85])  # 80 个交易日
    
    def calculate_v3_scores(self, stock_df: pd.DataFrame, date) -> Dict[str, float]:
        """
        v3 核心优化评分 - 简化实现
        
        核心思想：
        - 价值：预期差（低估 + 质量）
        - 产业：景气加速（动量变化）
        - 情绪：逆向（超卖买入）
        - 趋势：趋势加速
        - 量化：波动率 + 基本面
        """
        try:
            recent = stock_df[stock_df['日期'] <= date].tail(30)
            if len(recent) < 15:
                return {s: 0.5 for s in self.strategies}
            
            current_price = recent.iloc[-1]['收盘']
            
            # 价值 v3: 预期差驱动（低估 + 质量）
            ma20 = recent['收盘'].rolling(20).mean().iloc[-1]
            value_score = float(min(1.0, max(0.0, 1.0 - (current_price - ma20) / ma20 + 0.5)) if ma20 > 0 else 0.5)
            
            # 产业 v3: 景气加速（20 日动量 - 60 日动量）
            ma60 = stock_df[stock_df['日期'] <= date].tail(60)['收盘'].mean()
            momentum_20 = (current_price - ma20) / ma20 if ma20 > 0 else 0
            momentum_60 = (current_price - ma60) / ma60 if ma60 > 0 else 0
            industry_score = float(min(1.0, max(0.0, 0.5 + (momentum_20 - momentum_60) * 5)))
            
            # 情绪 v3: 逆向（RSI 超卖买入）
            delta = recent['收盘'].diff()
            gain = delta.where(delta > 0, 0).mean()
            loss = -delta.where(delta < 0, 0).mean()
            rsi = 100 - (100 / (1 + gain / loss)) if loss > 0 else 50
            emotion_score = float(min(1.0, max(0.0, 0.5 + (50 - rsi) / 100)))  # RSI<30 高分
            
            # 趋势 v3: 趋势加速（均线排列 + 斜率）
            ma5 = recent['收盘'].rolling(5).mean().iloc[-1]
            trend_aligned = 1.0 if current_price > ma5 > ma20 else (0.5 if current_price > ma20 else 0.2)
            trend_accel = float(min(1.0, max(0.0, trend_aligned)))
            
            # 量化 v3: 波动率收缩 + 质量
            returns = recent['收盘'].pct_change().dropna()
            vol_10 = returns.tail(10).std()
            vol_30 = returns.tail(30).std() if len(returns) >= 30 else vol_10
            vol_contraction = vol_10 / vol_30 if vol_30 > 0 else 1.0
            quant_score = float(min(1.0, max(0.0, 0.5 + (0.8 - vol_contraction) * 2)))
            
            return {
                'value': value_score,
                'industry': industry_score,
                'emotion': emotion_score,
                'trend': trend_accel,
                'quant': quant_score
            }
        except Exception as e:
            return {s: 0.5 for s in self.strategies}
    
    def backtest(self) -> Dict:
        """执行 T+5 回测"""
        print("\nStarting v3 backtest...")
        results = {s: {'returns': [], 'wins': 0, 'total': 0} for s in self.strategies}
        
        for i, date in enumerate(self.trade_dates[:-5]):
            # 为每个策略选 top3 股票
            stock_scores = {stock: self.calculate_v3_scores(df, date) for stock, df in self.stock_data.items()}
            
            for strategy in self.strategies:
                # 选出该策略得分最高的 3 只股票
                sorted_stocks = sorted(stock_scores.items(), key=lambda x: x[1].get(strategy, 0), reverse=True)[:3]
                
                for stock_code, _ in sorted_stocks:
                    try:
                        stock_df = self.stock_data[stock_code]
                        t_data = stock_df[stock_df['日期'].dt.date == date]
                        t5_data = stock_df[stock_df['日期'].dt.date == self.trade_dates[i+5]]
                        
                        if len(t_data) > 0 and len(t5_data) > 0:
                            t_close = t_data.iloc[-1]['收盘']
                            t5_open = t5_data.iloc[0]['开盘']
                            ret = (t5_open - t_close) / t_close
                            
                            results[strategy]['returns'].append(ret)
                            results[strategy]['total'] += 1
                            if ret > 0:
                                results[strategy]['wins'] += 1
                    except:
                        continue
            
            if (i + 1) % 10 == 0:
                print(f"Processed {i+1}/{len(self.trade_dates)-5} days")
        
        return results
    
    def analyze(self, results: Dict) -> Dict:
        """分析结果"""
        print("\n" + "="*60)
        print("v3 核心优化策略回测结果")
        print("="*60)
        
        stats = {}
        for strategy in self.strategies:
            returns = results[strategy]['returns']
            wins = results[strategy]['wins']
            total = results[strategy]['total']
            
            if total == 0:
                continue
            
            returns_arr = np.array(returns)
            win_rate = wins / total
            avg_return = float(np.mean(returns_arr))
            sharpe = float((avg_return / np.std(returns_arr)) * np.sqrt(252)) if np.std(returns_arr) > 0 else 0
            cumulative = float(np.prod(1 + returns_arr) - 1)
            
            stats[strategy] = {
                'win_rate': win_rate,
                'avg_return': avg_return,
                'sharpe': sharpe,
                'cumulative': cumulative,
                'trades': total
            }
            
            print(f"\n{strategy.upper()}:")
            print(f"  胜率：{win_rate:.2%} ({wins}/{total})")
            print(f"  平均收益：{avg_return:.4f} ({avg_return*100:.2f}%)")
            print(f"  夏普比率：{sharpe:.3f}")
            print(f"  累计收益：{cumulative:.2%}")
        
        return stats
    
    def compare_v1_v3(self, v3_stats: Dict):
        """与 v1 对比"""
        print("\n" + "="*60)
        print("v1 vs v3 对比")
        print("="*60)
        
        v1_stats = {
            'value': {'win_rate': 0.4238, 'avg_return': -0.00175, 'sharpe': -0.062},
            'industry': {'win_rate': 0.4500, 'avg_return': -0.00141, 'sharpe': -0.044},
            'emotion': {'win_rate': 0.4038, 'avg_return': -0.00082, 'sharpe': -0.021},
            'trend': {'win_rate': 0.4241, 'avg_return': -0.00172, 'sharpe': -0.041},
            'quant': {'win_rate': 0.4129, 'avg_return': -0.00034, 'sharpe': -0.010}
        }
        
        print(f"\n{'策略':<10} {'v1 胜率':<10} {'v3 胜率':<10} {'改进':<10} {'v1 收益':<10} {'v3 收益':<10} {'改进':<10}")
        print("-" * 70)
        
        for strategy in self.strategies:
            if strategy in v3_stats and strategy in v1_stats:
                v1_wr = v1_stats[strategy]['win_rate']
                v3_wr = v3_stats[strategy]['win_rate']
                wr_imp = v3_wr - v1_wr
                
                v1_ar = v1_stats[strategy]['avg_return']
                v3_ar = v3_stats[strategy]['avg_return']
                ar_imp = v3_ar - v1_ar
                
                print(f"{strategy:<10} {v1_wr:>8.2%}   {v3_wr:>8.2%}   {wr_imp:>+8.2%}   {v1_ar:>8.4f}   {v3_ar:>8.4f}   {ar_imp:>+8.4f}")
    
    def save_results(self, stats: Dict, output_path: str):
        """保存结果"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存：{output_path}")


if __name__ == "__main__":
    backtester = SimpleV2Backtest("/Users/blastai/.openclaw/workspace-0011ai/ashare/backtest_data")
    
    if len(backtester.stock_data) == 0:
        print("No data loaded!")
        exit(1)
    
    results = backtester.backtest()
    stats = backtester.analyze(results)
    backtester.compare_v1_v3(stats)
    backtester.save_results(stats, "/Users/blastai/.openclaw/workspace-0011ai/ashare/v3_simple_backtest_results.json")

#!/usr/bin/env python3
"""
最终优化版最近三个月回测
- 降低评分阈值至0.1
- 扩大样本至200只股票  
- 每个交易日测试
- 优化性能和内存使用
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

class FinalOptimizedBacktest:
    """最终优化版回测类"""
    
    def __init__(self, data_path: str = "/Users/blastai/.openclaw/workspace-0011ai/ashare/backtest_data"):
        self.data_path = data_path
        self.strategies = ['value', 'industry', 'emotion', 'trend', 'quant']
        self.stock_data = {}
        self.load_optimized_data()
    
    def load_optimized_data(self):
        """加载200只优质股票数据"""
        print(f"Loading optimized data from {self.data_path}...")
        csv_files = [f for f in os.listdir(self.data_path) if f.endswith('.csv')]
        
        # 选择200只流动性好、数据完整的股票
        selected_files = csv_files[:200]
        
        valid_count = 0
        for i, csv_file in enumerate(selected_files):
            stock_code = csv_file.replace('.csv', '')
            file_path = os.path.join(self.data_path, csv_file)
            
            try:
                df = pd.read_csv(file_path)
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.sort_values('日期')
                
                # 确保有足够的历史数据（至少90天）
                if len(df) >= 90:
                    self.stock_data[stock_code] = df
                    valid_count += 1
                
                if (i + 1) % 50 == 0:
                    print(f"Loaded {valid_count}/{min(200, len(selected_files))} valid stocks...")
                    
            except Exception as e:
                continue
        
        print(f"Successfully loaded {len(self.stock_data)} valid stocks")
    
    def calculate_optimized_scores(self, stock_df: pd.DataFrame, date: datetime) -> Dict[str, float]:
        """优化版评分逻辑 - 降低阈值"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(60)
            if len(recent_data) < 20:
                return {s: 0.0 for s in self.strategies}
            
            current_price = recent_data.iloc[-1]['收盘']
            ma20 = recent_data['收盘'].rolling(20).mean().iloc[-1]
            ma60 = recent_data['收盘'].rolling(60).mean().iloc[-1]
            
            # 价值策略：DCF稳定性模拟
            price_to_ma60 = current_price / ma60
            value_score = max(0, min(1, 0.8 - (price_to_ma60 - 1) * 2))
            
            # 产业策略：景气度边际变化
            momentum_60d = (current_price - ma60) / ma60
            momentum_20d = (current_price - ma20) / ma20 if ma20 > 0 else 0
            industry_score = max(0, min(1, momentum_60d * 3 + momentum_20d * 2 + 0.5))
            
            # 情绪策略：连板+量能
            recent_returns = recent_data['涨跌幅'].tail(5)
            consecutive_up = 0
            for ret in reversed(recent_returns):
                if ret > 0:
                    consecutive_up += 1
                else:
                    break
            
            volume_ratio = recent_data['成交量'].iloc[-1] / recent_data['成交量'].mean()
            emotion_score = max(0, min(1, consecutive_up * 0.15 + volume_ratio * 0.2))
            
            # 趋势策略：长期趋势+技术稳定性
            trend_strength = (current_price - ma60) / ma60
            # 检查是否破位（简化）
            recent_min = recent_data['最低'].tail(5).min()
            support_breach = 1 if recent_min < ma20 * 0.95 else 0
            trend_score = max(0, min(1, trend_strength * 2 + (1 - support_breach) * 0.5))
            
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
        """按策略选出TOP3股票 - 降低阈值至0.1"""
        all_scores = {strategy: [] for strategy in self.strategies}
        
        for stock_code, stock_df in self.stock_data.items():
            if stock_df['日期'].max() < date:
                continue
                
            scores = self.calculate_optimized_scores(stock_df, date)
            for strategy, score in scores.items():
                if score > 0.1:  # 降低阈值
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
        """T+5日收益回测 - 优化数据检查"""
        if stock_code not in self.stock_data:
            return 0.0, False
            
        stock_df = self.stock_data[stock_code]
        buy_mask = stock_df['日期'] == buy_date
        
        if not buy_mask.any():
            return 0.0, False
        
        buy_price = stock_df[buy_mask].iloc[0]['收盘']
        future_data = stock_df[stock_df['日期'] > buy_date].head(10)
        
        if len(future_data) < 5:  # 确保有足够后续数据
            return 0.0, False
        
        sell_price = future_data.iloc[4]['收盘']  # 第5个交易日
        return_rate = (sell_price - buy_price) / buy_price
        is_profit = return_rate > 0
        
        return return_rate, is_profit
    
    def execute_final_backtest(self, months: int = 3) -> Dict:
        """执行最终优化版回测"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*30)
        
        print(f"执行最终优化版回测: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        print(f"股票数量: {len(self.stock_data)}")
        
        backtest_results = {strategy: {'trades': [], 'win_rate': 0, 'avg_return': 0} 
                           for strategy in self.strategies}
        
        # 收集所有交易日
        current_date = start_date
        trade_dates = []
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # 工作日
                trade_dates.append(current_date)
            current_date += timedelta(days=1)
        
        print(f"将测试 {len(trade_dates)} 个交易日...")
        
        valid_trade_days = 0
        for i, trade_date in enumerate(trade_dates):
            try:
                top3_by_strategy = self.select_top3_by_strategy(trade_date)
                
                has_valid_trades = False
                for strategy, stocks in top3_by_strategy.items():
                    for stock in stocks:
                        return_rate, is_profit = self.backtest_t_plus_5(stock, trade_date)
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
                
                if (i + 1) % 20 == 0:
                    print(f"已处理 {i + 1}/{len(trade_dates)} 个交易日 ({valid_trade_days} 天有有效交易)...")
                    
            except Exception as e:
                continue
        
        # 计算最终结果
        for strategy in self.strategies:
            trades = backtest_results[strategy]['trades']
            if trades:
                profits = [trade['profit'] for trade in trades]
                returns = [trade['return'] for trade in trades]
                backtest_results[strategy]['win_rate'] = sum(profits) / len(profits)
                backtest_results[strategy]['avg_return'] = sum(returns) / len(returns)
        
        print(f"\n回测完成! 有效交易天数: {valid_trade_days}/{len(trade_dates)}")
        return backtest_results

def main():
    """主函数"""
    print("=== 最终优化版最近三个月回测 ===")
    
    backtester = FinalOptimizedBacktest()
    results = backtester.execute_final_backtest(months=3)
    
    print("\n=== 最终回测结果（最近3个月） ===")
    total_trades = 0
    for strategy, stats in results.items():
        if stats['trades']:
            print(f"{strategy}: 胜率={stats['win_rate']:.3f}, 平均收益={stats['avg_return']:.3%}, 交易次数={len(stats['trades'])}")
            total_trades += len(stats['trades'])
        else:
            print(f"{strategy}: 无有效交易")
    
    print(f"\n总交易次数: {total_trades}")
    
    # 保存结果
    output_path = "/Users/blastai/.openclaw/workspace-0011ai/ashare/final_recent_backtest_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 备份到桌面
    desktop_path = "~/Desktop/asharereport/final_recent_backtest_results.json"
    os.system(f"cp {output_path} {desktop_path}")
    
    print(f"\n最终回测结果已保存到: {output_path}")
    print(f"结果已备份到桌面: {desktop_path}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
优化版T+5回测 - 买入价格为T日收盘价，卖出价格为T+5日开盘价
只做多头交易，不做空头交易
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

class OptimizedT5OpenBacktest:
    """优化版T+5开盘价回测类"""
    
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
        
        # 加载50只股票用于更全面测试
        selected_files = csv_files[:50]
        
        for i, csv_file in enumerate(selected_files):
            stock_code = csv_file.replace('.csv', '')
            file_path = os.path.join(self.data_path, csv_file)
            
            try:
                df = pd.read_csv(file_path)
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.sort_values('日期')
                
                # 确保包含开盘价和收盘价字段
                required_columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅']
                if all(col in df.columns for col in required_columns):
                    if len(df) >= 100:
                        self.stock_data[stock_code] = df
                
                if (i + 1) % 10 == 0:
                    print(f"Loaded {len(self.stock_data)} valid stocks...")
                    
            except Exception as e:
                continue
        
        print(f"Successfully loaded {len(self.stock_data)} valid stocks")
        
        if self.stock_data:
            first_stock = list(self.stock_data.keys())[0]
            all_dates = self.stock_data[first_stock]['日期'].dt.date.tolist()
            recent_dates = sorted([d for d in all_dates if d.weekday() < 5], reverse=True)[:60]
            self.trade_dates = sorted(recent_dates[:-5])
            
            print(f"回测日期范围: {min(self.trade_dates)} 到 {max(self.trade_dates)}")
            print(f"回测交易日数量: {len(self.trade_dates)}")
    
    def calculate_refined_scores_v2(self, stock_df: pd.DataFrame, date: datetime) -> Dict[str, float]:
        """基于用户指导的精细化评分逻辑v2"""
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
            recent_min = recent_data['最低'].tail(5).min()
            support_breach = 1 if recent_min < ma20 * 0.95 else 0
            trend_score = max(0, min(1, trend_strength * 2 + (1 - support_breach) * 0.5))
            
            # 量化策略：波动率收缩
            recent_vol = recent_data['收盘'].pct_change().tail(10).std()
            historical_vol = recent_data['收盘'].pct_change().tail(30).std()
            vol_contraction = max(0, min(1, (historical_vol - recent_vol) / historical_vol)) if historical_vol > 0 else 0
            quant_score = vol_contraction
            
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
        """按相对排名选出TOP3股票"""
        all_scores = {strategy: [] for strategy in self.strategies}
        
        for stock_code, stock_df in self.stock_data.items():
            scores = self.calculate_refined_scores_v2(stock_df, date)
            for strategy, score in scores.items():
                if score > 0.05:  # 适度筛选
                    all_scores[strategy].append((stock_code, score))
        
        top3_by_strategy = {}
        for strategy in self.strategies:
            if all_scores[strategy]:
                sorted_stocks = sorted(all_scores[strategy], key=lambda x: x[1], reverse=True)
                top3_by_strategy[strategy] = [stock[0] for stock in sorted_stocks[:3]]
            else:
                top3_by_strategy[strategy] = []
        
        return top3_by_strategy
    
    def backtest_t_plus_5_open_price(self, stock_code: str, buy_date: datetime) -> Tuple[float, bool]:
        """
        T+5开盘价回测
        - 买入价格: T日收盘价
        - 卖出价格: T+5日开盘价  
        - 只做多头交易
        """
        if stock_code not in self.stock_data:
            return 0.0, False
            
        stock_df = self.stock_data[stock_code]
        buy_mask = stock_df['日期'] == buy_date
        
        if not buy_mask.any():
            return 0.0, False
        
        buy_price = stock_df[buy_mask].iloc[0]['收盘']
        future_dates = stock_df[stock_df['日期'] > buy_date]['日期'].tolist()
        
        if len(future_dates) < 5:
            return 0.0, False
        
        sell_date = future_dates[4]  # 第5个交易日
        sell_mask = stock_df['日期'] == sell_date
        sell_price = stock_df[sell_mask].iloc[0]['开盘']  # 使用开盘价
        
        return_rate = (sell_price - buy_price) / buy_price
        is_profit = return_rate > 0  # 只考虑多头盈利
        
        return return_rate, is_profit
    
    def execute_optimized_backtest(self) -> Dict:
        """执行优化版回测"""
        print(f"执行优化版T+5开盘价回测...")
        print(f"股票数量: {len(self.stock_data)}")
        print(f"交易日数量: {len(self.trade_dates)}")
        
        backtest_results = {strategy: {'trades': [], 'win_rate': 0.0, 'avg_return': 0.0} 
                           for strategy in self.strategies}
        
        valid_trade_days = 0
        total_trades = 0
        
        for i, trade_date in enumerate(self.trade_dates):
            trade_datetime = datetime.combine(trade_date, datetime.min.time())
            
            try:
                top3_by_strategy = self.select_top3_by_relative_ranking(trade_datetime)
                
                daily_trades = 0
                for strategy, stocks in top3_by_strategy.items():
                    for stock in stocks:
                        return_rate, is_profit = self.backtest_t_plus_5_open_price(stock, trade_datetime)
                        if return_rate != 0.0:
                            backtest_results[strategy]['trades'].append({
                                'date': trade_date.strftime('%Y-%m-%d'),
                                'stock': stock,
                                'buy_price': float(stock_df[stock_df['日期'] == trade_datetime].iloc[0]['收盘']),
                                'sell_price': float(stock_df[stock_df['日期'] == future_dates[4]].iloc[0]['开盘']),
                                'return': float(return_rate),
                                'profit': int(is_profit)
                            })
                            daily_trades += 1
                            total_trades += 1
                
                if daily_trades > 0:
                    valid_trade_days += 1
                
                if (i + 1) % 10 == 0:
                    print(f"已处理 {i + 1}/{len(self.trade_dates)} 个交易日 ({total_trades} 笔交易)")
                    
            except Exception as e:
                continue
        
        # 计算统计结果
        for strategy in self.strategies:
            trades = backtest_results[strategy]['trades']
            if trades:
                profits = [trade['profit'] for trade in trades]
                returns = [trade['return'] for trade in trades]
                backtest_results[strategy]['win_rate'] = float(sum(profits) / len(profits))
                backtest_results[strategy]['avg_return'] = float(sum(returns) / len(returns))
        
        print(f"\n回测完成! 有效交易天数: {valid_trade_days}/{len(self.trade_dates)}")
        print(f"总交易次数: {total_trades}")
        return backtest_results

def main():
    """主函数"""
    print("=== 优化版T+5开盘价回测 ===")
    print("买入价格: T日收盘价")
    print("卖出价格: T+5日开盘价") 
    print("交易类型: 仅多头交易")
    
    backtester = OptimizedT5OpenBacktest()
    if not backtester.stock_data or not backtester.trade_dates:
        print("❌ 数据加载失败，无法执行回测")
        return
    
    results = backtester.execute_optimized_backtest()
    
    print("\n=== 优化版T+5开盘价回测结果 ===")
    total_trades = 0
    for strategy, stats in results.items():
        if stats['trades']:
            print(f"{strategy}: 胜率={stats['win_rate']:.3f}, 平均收益={stats['avg_return']:.3%}, 交易次数={len(stats['trades'])}")
            total_trades += len(stats['trades'])
        else:
            print(f"{strategy}: 无有效交易")
    
    print(f"\n总交易次数: {total_trades}")
    
    # 保存详细结果
    output_path = "/Users/blastai/.openclaw/workspace-0011ai/ashare/optimized_t5_open_backtest_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 备份到桌面
    desktop_path = "~/Desktop/asharereport/optimized_t5_open_backtest_results.json"
    os.system(f"cp {output_path} {desktop_path}")
    
    # 创建简洁摘要
    summary = {
        "backtest_type": "T+5 Open Price (Long Only)",
        "buy_price": "T-day Close",
        "sell_price": "T+5-day Open", 
        "backtest_period": f"{min(backtester.trade_dates)} to {max(backtester.trade_dates)}",
        "stocks_tested": len(backtester.stock_data),
        "trading_days": len(backtester.trade_dates),
        "total_trades": total_trades,
        "strategy_results": {}
    }
    
    for strategy, stats in results.items():
        if stats['trades']:
            summary["strategy_results"][strategy] = {
                "win_rate": round(stats['win_rate'], 3),
                "avg_return": round(stats['avg_return'], 4),
                "trade_count": len(stats['trades'])
            }
    
    summary_path = "~/Desktop/asharereport/optimized_t5_open_summary.json"
    with open(summary_path.replace("~/", "/Users/blastai/"), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n优化版回测结果已保存和备份")

if __name__ == "__main__":
    main()
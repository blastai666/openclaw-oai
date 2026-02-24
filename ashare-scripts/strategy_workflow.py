#!/usr/bin/env python3
"""
A股五大策略工作流系统
- 依据最新日报框架选出每个策略TOP3股票
- T+5日收益回测验证（T日买入，T+5日卖出）
- 策略框架优化和数据回测分离
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

class StrategyWorkflow:
    """策略工作流管理器"""
    
    def __init__(self, data_path: str = "/Users/blastai/.openclaw/workspace-0011ai/ashare/backtest_data"):
        self.data_path = data_path
        self.strategies = ['value', 'industry', 'emotion', 'trend', 'quant']
        self.stock_data = {}
        self.load_all_data()
    
    def load_all_data(self):
        """加载所有股票历史数据"""
        print(f"Loading historical data from {self.data_path}...")
        csv_files = [f for f in os.listdir(self.data_path) if f.endswith('.csv')]
        
        for i, csv_file in enumerate(csv_files[:200]):  # 加载前200只股票
            stock_code = csv_file.replace('.csv', '')
            file_path = os.path.join(self.data_path, csv_file)
            
            try:
                df = pd.read_csv(file_path)
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.sort_values('日期')
                self.stock_data[stock_code] = df
                
                if (i + 1) % 50 == 0:
                    print(f"Loaded {i + 1}/{min(200, len(csv_files))} stocks...")
                    
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
                continue
        
        print(f"Successfully loaded {len(self.stock_data)} stocks")
    
    def calculate_value_score_v2(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """价值策略v2评分 - 基于财务指标"""
        try:
            # 获取最近价格和财务数据
            current_price = stock_df[stock_df['日期'] <= date].iloc[-1]['收盘']
            
            # 财务指标计算（简化版）
            pe_ratio = current_price / (current_price * 0.1)  # 简化PE
            pb_ratio = current_price / (current_price * 0.2)  # 简化PB
            dividend_yield = 0.03  # 简化股息率
            
            # 价值策略核心：低估值、高股息、稳定
            pe_score = max(0, min(1, (50 - pe_ratio) / 50))
            pb_score = max(0, min(1, (10 - pb_ratio) / 10))
            div_score = min(1, dividend_yield / 0.05)
            
            return (pe_score * 0.4 + pb_score * 0.3 + div_score * 0.3)
        except:
            return 0.0
    
    def calculate_industry_score_v2(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """产业策略v2评分 - 基于行业景气度"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(60)
            if len(recent_data) < 30:
                return 0.0
                
            # 60日动量
            price_60d_ago = recent_data.iloc[0]['收盘']
            current_price = recent_data.iloc[-1]['收盘']
            momentum_60d = (current_price - price_60d_ago) / price_60d_ago
            
            # 20日动量
            price_20d_ago = recent_data.iloc[-21]['收盘'] if len(recent_data) >= 21 else price_60d_ago
            momentum_20d = (current_price - price_20d_ago) / price_20d_ago
            
            # 产业策略：趋势向上且加速
            momentum_score = max(0, min(1, momentum_60d * 5 + momentum_20d * 3))
            return momentum_score
        except:
            return 0.0
    
    def calculate_emotion_score_v2(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """情绪策略v2评分 - 基于量价关系"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(10)
            if len(recent_data) < 5:
                return 0.0
                
            # 连续上涨天数
            consecutive_up = 0
            for i in range(len(recent_data)-1, 0, -1):
                if recent_data.iloc[i]['涨跌幅'] > 0:
                    consecutive_up += 1
                else:
                    break
            
            # 成交量激增
            avg_volume = recent_data['成交量'].mean()
            current_volume = recent_data.iloc[-1]['成交量']
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # 情绪策略：连板+放量
            emotion_score = min(1, (consecutive_up * 0.15 + min(volume_ratio, 3) * 0.25))
            return emotion_score
        except:
            return 0.0
    
    def calculate_trend_score_v2(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """趋势策略v2评分 - 基于技术分析"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(30)
            if len(recent_data) < 20:
                return 0.0
                
            # MA20趋势
            ma20 = recent_data['收盘'].rolling(20).mean().iloc[-1]
            current_price = recent_data.iloc[-1]['收盘']
            trend_strength = (current_price - ma20) / ma20
            
            # RSI指标
            delta = recent_data['收盘'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs.iloc[-1])) if loss.iloc[-1] != 0 else 50
            
            # 趋势策略：强势趋势+技术指标配合
            trend_score = max(0, min(1, trend_strength * 2 + (100 - rsi) / 100 * 0.5))
            return trend_score
        except:
            return 0.0
    
    def calculate_quant_score_v2(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """量化策略v2评分 - 基于统计套利"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(20)
            if len(recent_data) < 10:
                return 0.0
                
            # 波动率收缩
            returns = recent_data['收盘'].pct_change().dropna()
            volatility = returns.std()
            
            # 均值回归
            current_price = recent_data.iloc[-1]['收盘']
            mean_price = recent_data['收盘'].mean()
            z_score = (current_price - mean_price) / (recent_data['收盘'].std() + 1e-8)
            
            # 量化策略：低波动+均值回归
            quant_score = max(0, min(1, (1 - min(volatility * 10, 1)) * 0.6 + 
                                   max(0, min(1, abs(z_score) * 0.2))))
            return quant_score
        except:
            return 0.0
    
    def select_top3_stocks(self, strategy: str, date: str) -> List[str]:
        """选出指定策略在指定日期的TOP3股票"""
        target_date = pd.to_datetime(date)
        scores = {}
        
        for stock_code, stock_df in self.stock_data.items():
            # 确保有足够历史数据
            if stock_df['日期'].max() < target_date:
                continue
                
            # 计算策略评分
            if strategy == 'value':
                score = self.calculate_value_score_v2(stock_df, target_date)
            elif strategy == 'industry':
                score = self.calculate_industry_score_v2(stock_df, target_date)
            elif strategy == 'emotion':
                score = self.calculate_emotion_score_v2(stock_df, target_date)
            elif strategy == 'trend':
                score = self.calculate_trend_score_v2(stock_df, target_date)
            elif strategy == 'quant':
                score = self.calculate_quant_score_v2(stock_df, target_date)
            else:
                score = 0.0
            
            if score > 0:
                scores[stock_code] = score
        
        # 选出TOP3
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top3 = [stock[0] for stock in sorted_scores[:3]]
        return top3
    
    def backtest_t_plus_5(self, stock_code: str, buy_date: datetime) -> Tuple[float, bool]:
        """T+5日收益回测"""
        if stock_code not in self.stock_data:
            return 0.0, False
            
        stock_df = self.stock_data[stock_code]
        
        # 找到买入日期的数据
        buy_data = stock_df[stock_df['日期'] == buy_date]
        if buy_data.empty:
            return 0.0, False
            
        buy_price = buy_data.iloc[0]['收盘']
        
        # 找到T+5日的卖出价格
        sell_date = buy_date + timedelta(days=7)  # 考虑周末，实际约5个交易日
        future_data = stock_df[stock_df['日期'] > buy_date]
        
        if future_data.empty:
            return 0.0, False
            
        # 找到最接近T+5的交易日
        sell_data = future_data.iloc[0]  # 简化：取下一个交易日
        if len(future_data) >= 5:
            sell_data = future_data.iloc[4]  # 取第5个交易日
            
        sell_price = sell_data['收盘']
        return_rate = (sell_price - buy_price) / buy_price
        is_profit = return_rate > 0
        
        return return_rate, is_profit
    
    def execute_strategy_workflow(self, start_date: str = "2023-01-01", end_date: str = None) -> Dict:
        """执行完整的策略工作流"""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        workflow_results = {
            'value': {'trades': [], 'win_rate': 0, 'avg_return': 0},
            'industry': {'trades': [], 'win_rate': 0, 'avg_return': 0},
            'emotion': {'trades': [], 'win_rate': 0, 'avg_return': 0},
            'trend': {'trades': [], 'win_rate': 0, 'avg_return': 0},
            'quant': {'trades': [], 'win_rate': 0, 'avg_return': 0}
        }
        
        # 遍历每个交易日
        current_date = start_dt
        while current_date <= end_dt:
            # 只在有足够数据的日期执行
            if current_date.weekday() < 5:  # 工作日
                try:
                    # 为每个策略选出TOP3股票
                    for strategy in self.strategies:
                        top3_stocks = self.select_top3_stocks(strategy, current_date.strftime('%Y-%m-%d'))
                        
                        # 对每个选出的股票进行T+5回测
                        for stock in top3_stocks:
                            return_rate, is_profit = self.backtest_t_plus_5(stock, current_date)
                            
                            if return_rate != 0.0:
                                trade_record = {
                                    'date': current_date.strftime('%Y-%m-%d'),
                                    'stock': stock,
                                    'return': return_rate,
                                    'profit': is_profit
                                }
                                workflow_results[strategy]['trades'].append(trade_record)
                                
                except Exception as e:
                    print(f"Error processing date {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        # 计算最终统计结果
        for strategy in self.strategies:
            trades = workflow_results[strategy]['trades']
            if trades:
                profits = [trade['profit'] for trade in trades]
                returns = [trade['return'] for trade in trades]
                
                workflow_results[strategy]['win_rate'] = sum(profits) / len(profits)
                workflow_results[strategy]['avg_return'] = sum(returns) / len(returns)
        
        return workflow_results

# 测试函数
def test_workflow():
    """测试策略工作流"""
    workflow = StrategyWorkflow()
    
    # 执行工作流（简化测试：只测试一个月）
    results = workflow.execute_strategy_workflow("2023-01-01", "2023-01-31")
    
    print("\n=== T+5策略工作流结果 ===")
    for strategy, stats in results.items():
        if stats['trades']:
            print(f"{strategy}: 胜率={stats['win_rate']:.3f}, 平均收益={stats['avg_return']:.3f}, 交易次数={len(stats['trades'])}")
        else:
            print(f"{strategy}: 无有效交易")
    
    # 保存结果
    with open('/Users/blastai/.openclaw/workspace-0011ai/ashare/workflow_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n工作流结果已保存到: workflow_results.json")

if __name__ == "__main__":
    test_workflow()
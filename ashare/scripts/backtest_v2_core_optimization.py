#!/usr/bin/env python3
"""
五大策略 v2.0 核心优化回测
基于预期差驱动的核心思想重构

回测方法：
- T+5 开盘价回测（T 日买入，T+5 日开盘卖出）
- 对比 v1 vs v2 策略表现
- 分析各策略胜率、收益、夏普比率
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
import sys

# 导入 v2 策略
sys.path.insert(0, '/Users/blastai/.openclaw/workspace-0011ai/ashare/scripts')
from strategy_core_optimization_v2 import CoreOptimizedStrategies

class V2CoreOptimizationBacktest:
    """v2 核心优化策略回测类"""
    
    def __init__(self, data_path: str = "/Users/blastai/.openclaw/workspace-0011ai/ashare/backtest_data"):
        self.data_path = data_path
        self.strategies = ['value', 'industry', 'emotion', 'trend', 'quant']
        self.stock_data = {}
        self.trade_dates = []
        self.optimizer = CoreOptimizedStrategies()
        self.load_data_and_dates()
    
    def load_data_and_dates(self):
        """加载数据和确定交易日期"""
        print(f"Loading data from {self.data_path}...")
        csv_files = [f for f in os.listdir(self.data_path) if f.endswith('.csv')]
        
        # 加载 50 只股票（增加样本）
        selected_files = csv_files[:50]
        
        for i, csv_file in enumerate(selected_files):
            stock_code = csv_file.replace('.csv', '')
            file_path = os.path.join(self.data_path, csv_file)
            
            try:
                df = pd.read_csv(file_path)
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.sort_values('日期')
                
                required_columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅']
                if all(col in df.columns for col in required_columns):
                    if len(df) >= 80:  # 确保有足够数据
                        self.stock_data[stock_code] = df
                
                if (i + 1) % 10 == 0:
                    print(f"Loaded {len(self.stock_data)} valid stocks...")
                    
            except Exception as e:
                continue
        
        print(f"Successfully loaded {len(self.stock_data)} valid stocks")
        
        if self.stock_data:
            # 使用所有股票的共同交易日
            all_common_dates = None
            for stock_df in self.stock_data.values():
                stock_dates = set(stock_df['日期'].dt.date)
                if all_common_dates is None:
                    all_common_dates = stock_dates
                else:
                    all_common_dates = all_common_dates.intersection(stock_dates)
            
            if all_common_dates:
                all_common_dates = sorted([d for d in all_common_dates if d.weekday() < 5], reverse=True)
                recent_dates = all_common_dates[:80]  # 最近 80 个交易日
                self.trade_dates = sorted(recent_dates[:-5])  # 去掉最后 5 天
                
                print(f"共同交易日范围：{min(self.trade_dates)} 到 {max(self.trade_dates)}")
                print(f"共同交易日数量：{len(self.trade_dates)}")
            else:
                print("❌ 无法找到共同交易日")
    
    def calculate_v2_scores(self, stock_df: pd.DataFrame, date: datetime) -> Dict[str, float]:
        """
        使用 v2 核心优化策略计算评分
        
        v2 核心思想：
        - 价值：预期差驱动
        - 产业：景气度拐点
        - 情绪：情绪拐点（逆向）
        - 趋势：趋势加速
        - 量化：量化 + 基本面融合
        """
        try:
            # 使用 v2 策略优化器
            results = self.optimizer.calculate_composite_score(
                stock_df=stock_df,
                date=date,
                fundamentals=None,  # 简化版，暂不使用基本面数据
                industry_data=None,
                sentiment_data=None,
                trend_data=None
            )
            
            # 提取各策略得分
            strategy_scores = {}
            for strategy in self.strategies:
                if strategy in results['strategies']:
                    strategy_scores[strategy] = results['strategies'][strategy]['score']
                else:
                    strategy_scores[strategy] = 0.5
            
            return strategy_scores
            
        except Exception as e:
            print(f"Error calculating v2 scores: {e}")
            return {s: 0.5 for s in self.strategies}
    
    def select_top_stocks_per_strategy(self, date: datetime, top_n: int = 3) -> Dict[str, List[str]]:
        """为每个策略选出得分最高的 top_n 只股票"""
        selected_stocks = {strategy: [] for strategy in self.strategies}
        
        # 计算所有股票在各策略下的得分
        stock_scores = {stock: {} for stock in self.stock_data.keys()}
        
        for stock_code, stock_df in self.stock_data.items():
            scores = self.calculate_v2_scores(stock_df, date)
            stock_scores[stock_code] = scores
        
        # 为每个策略选出 top_n
        for strategy in self.strategies:
            sorted_stocks = sorted(
                stock_scores.items(),
                key=lambda x: x[1].get(strategy, 0),
                reverse=True
            )
            selected_stocks[strategy] = [stock for stock, _ in sorted_stocks[:top_n]]
        
        return selected_stocks
    
    def backtest_t5_open(self) -> Dict:
        """
        T+5 开盘价回测
        
        交易规则：
        - T 日收盘前买入
        - T+5 日开盘价卖出
        - 计算收益率和胜率
        """
        print("\n" + "="*60)
        print("开始 v2 核心优化策略 T+5 回测")
        print("="*60)
        
        results = {strategy: {'trades': [], 'returns': []} for strategy in self.strategies}
        
        total_trades = 0
        
        for i, date in enumerate(self.trade_dates):
            # 选出每个策略的 top3 股票
            selected_stocks = self.select_top_stocks_per_strategy(date, top_n=3)
            
            # 为每个策略执行交易
            for strategy in self.strategies:
                for stock_code in selected_stocks[strategy]:
                    if stock_code not in self.stock_data:
                        continue
                    
                    stock_df = self.stock_data[stock_code]
                    
                    # 找到 T 日和 T+5 日的数据
                    try:
                        t_day_data = stock_df[stock_df['日期'].dt.date == date]
                        
                        if len(t_day_data) == 0:
                            continue
                        
                        # T+5 日（跳过 5 个交易日）
                        t_plus_5_idx = i + 5
                        if t_plus_5_idx >= len(self.trade_dates):
                            continue
                        
                        t_plus_5_date = self.trade_dates[t_plus_5_idx]
                        t_plus_5_data = stock_df[stock_df['日期'].dt.date == t_plus_5_date]
                        
                        if len(t_plus_5_data) == 0:
                            continue
                        
                        # 获取价格
                        t_close = t_day_data.iloc[-1]['收盘']
                        t_plus_5_open = t_plus_5_data.iloc[0]['开盘']
                        
                        # 计算收益率
                        return_pct = (t_plus_5_open - t_close) / t_close
                        
                        # 记录交易
                        trade = {
                            'date': str(date),
                            'stock': stock_code,
                            'strategy': strategy,
                            't_close': float(t_close),
                            't_plus_5_open': float(t_plus_5_open),
                            'return': float(return_pct),
                            'profit': 1 if return_pct > 0 else 0
                        }
                        
                        results[strategy]['trades'].append(trade)
                        results[strategy]['returns'].append(return_pct)
                        total_trades += 1
                        
                    except Exception as e:
                        continue
            
            if (i + 1) % 10 == 0:
                print(f"已回测 {i+1}/{len(self.trade_dates)} 交易日，总交易数：{total_trades}")
        
        return results
    
    def analyze_strategy_performance(self, results: Dict) -> Dict:
        """分析各策略表现"""
        print("\n" + "="*60)
        print("v2 核心优化策略表现分析")
        print("="*60)
        
        stats = {}
        
        for strategy in self.strategies:
            trades = results[strategy]['trades']
            returns = results[strategy]['returns']
            
            if len(returns) == 0:
                print(f"\n{strategy}: 无交易数据")
                continue
            
            # 计算统计指标
            returns_array = np.array(returns)
            wins = np.sum(returns_array > 0)
            total = len(returns_array)
            win_rate = wins / total if total > 0 else 0
            
            avg_return = np.mean(returns_array)
            std_return = np.std(returns_array)
            
            # 夏普比率（年化，假设 252 个交易日）
            if std_return > 0:
                sharpe = (avg_return / std_return) * np.sqrt(252)
            else:
                sharpe = 0
            
            # 累计收益
            cumulative_return = np.prod(1 + returns_array) - 1
            
            # 最大回撤
            cumulative = np.cumprod(1 + returns_array)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = np.min(drawdown)
            
            stats[strategy] = {
                'win_rate': float(win_rate),
                'avg_return': float(avg_return),
                'sharpe': float(sharpe),
                'cumulative_return': float(cumulative_return),
                'max_drawdown': float(max_drawdown),
                'total_trades': int(total),
                'wins': int(wins),
                'losses': int(total - wins)
            }
            
            # 打印结果
            print(f"\n{strategy.upper()} 策略:")
            print(f"  交易次数：{total}")
            print(f"  胜率：{win_rate:.2%} (赢{wins}/输{total-wins})")
            print(f"  平均收益：{avg_return:.4f} ({avg_return*100:.2f}%)")
            print(f"  夏普比率：{sharpe:.3f}")
            print(f"  累计收益：{cumulative_return:.2%}")
            print(f"  最大回撤：{max_drawdown:.2%}")
        
        return stats
    
    def compare_with_v1(self, v2_stats: Dict):
        """与 v1 策略对比"""
        print("\n" + "="*60)
        print("v1 vs v2 策略对比")
        print("="*60)
        
        # v1 回测结果（来自之前的回测）
        v1_stats = {
            'value': {'win_rate': 0.4238, 'avg_return': -0.00175, 'sharpe': -0.062},
            'industry': {'win_rate': 0.4500, 'avg_return': -0.00141, 'sharpe': -0.044},
            'emotion': {'win_rate': 0.4038, 'avg_return': -0.00082, 'sharpe': -0.021},
            'trend': {'win_rate': 0.4241, 'avg_return': -0.00172, 'sharpe': -0.041},
            'quant': {'win_rate': 0.4129, 'avg_return': -0.00034, 'sharpe': -0.010}
        }
        
        print("\n胜率对比:")
        print(f"{'策略':<10} {'v1 胜率':<10} {'v2 胜率':<10} {'改进':<10}")
        print("-" * 40)
        for strategy in self.strategies:
            v1_wr = v1_stats[strategy]['win_rate']
            v2_wr = v2_stats.get(strategies, {}).get('win_rate', 0) if strategy in v2_stats else 0
            improvement = v2_wr - v1_wr
            print(f"{strategy:<10} {v1_wr:>8.2%}   {v2_wr:>8.2%}   {improvement:>+8.2%}")
        
        print("\n平均收益对比:")
        print(f"{'策略':<10} {'v1 收益':<10} {'v2 收益':<10} {'改进':<10}")
        print("-" * 40)
        for strategy in self.strategies:
            v1_ar = v1_stats[strategy]['avg_return']
            v2_ar = v2_stats.get(strategies, {}).get('avg_return', 0) if strategy in v2_stats else 0
            improvement = v2_ar - v1_ar
            print(f"{strategy:<10} {v1_ar:>8.4f}   {v2_ar:>8.4f}   {improvement:>+8.4f}")
        
        print("\n夏普比率对比:")
        print(f"{'策略':<10} {'v1 夏普':<10} {'v2 夏普':<10} {'改进':<10}")
        print("-" * 40)
        for strategy in self.strategies:
            v1_sh = v1_stats[strategy]['sharpe']
            v2_sh = v2_stats.get(strategies, {}).get('sharpe', 0) if strategy in v2_stats else 0
            improvement = v2_sh - v1_sh
            print(f"{strategy:<10} {v1_sh:>8.3f}   {v2_sh:>8.3f}   {improvement:>+8.3f}")
    
    def save_results(self, results: Dict, stats: Dict, output_path: str = "/Users/blastai/.openclaw/workspace-0011ai/ashare/v2_backtest_results.json"):
        """保存回测结果"""
        output = {
            'backtest_info': {
                'version': 'v2.0_core_optimization',
                'method': 'T+5_open',
                'date_range': {
                    'start': str(min(self.trade_dates)),
                    'end': str(max(self.trade_dates))
                },
                'total_trading_days': len(self.trade_dates),
                'total_stocks': len(self.stock_data)
            },
            'strategy_stats': stats,
            'detailed_trades': results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 回测结果已保存到：{output_path}")
    
    def generate_report(self, stats: Dict) -> str:
        """生成回测报告"""
        report = []
        report.append("# 五大策略 v2.0 核心优化回测报告")
        report.append(f"\n**回测日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"\n**回测区间**: {min(self.trade_dates)} 到 {max(self.trade_dates)}")
        report.append(f"\n**股票数量**: {len(self.stock_data)}")
        report.append(f"\n**交易日数**: {len(self.trade_dates)}")
        
        report.append("\n## 策略表现汇总")
        report.append("\n| 策略 | 胜率 | 平均收益 | 夏普比率 | 累计收益 | 最大回撤 | 交易次数 |")
        report.append("|------|------|----------|----------|----------|----------|----------|")
        
        for strategy in self.strategies:
            if strategy in stats:
                s = stats[strategy]
                report.append(
                    f"| {strategy} | {s['win_rate']:.2%} | {s['avg_return']:.4f} | "
                    f"{s['sharpe']:.3f} | {s['cumulative_return']:.2%} | "
                    f"{s['max_drawdown']:.2%} | {s['total_trades']} |"
                )
        
        report.append("\n## 核心优化点")
        report.append("\n### 价值策略 v2.0: 预期差驱动")
        report.append("- 从'DCF 稳定性'转向'预期差驱动'")
        report.append("- 权重：预期差 (40%) + 估值修复 (30%) + 质量 (20%) + 安全边际 (10%)")
        
        report.append("\n### 产业策略 v2.0: 景气度拐点")
        report.append("- 从'景气度绝对值'转向'景气度拐点'")
        report.append("- 权重：景气加速 (35%) + 政策变化 (25%) + 供需矛盾 (25%) + 产业链验证 (15%)")
        
        report.append("\n### 情绪策略 v2.0: 情绪拐点")
        report.append("- 从'追涨杀跌'转向'情绪拐点（逆向）'")
        report.append("- 权重：情绪极端 (40%) + 拐点信号 (30%) + 板块梯队 (20%) + 资金分歧 (10%)")
        
        report.append("\n### 趋势策略 v2.0: 趋势加速")
        report.append("- 从'跟随趋势'转向'趋势加速'")
        report.append("- 权重：趋势强度 (35%) + 趋势加速 (30%) + 产业链验证 (20%) + 技术破位 (15%)")
        
        report.append("\n### 量化策略 v2.0: 量化 + 基本面融合")
        report.append("- 从'纯量化'转向'量化 + 基本面融合'")
        report.append("- 权重：波动率收缩 (30%) + 换手率异常 (25%) + 热门度 (25%) + 基本面确认 (20%)")
        
        report.append("\n## 结论")
        
        # 计算平均表现
        avg_win_rate = np.mean([stats[s]['win_rate'] for s in self.strategies if s in stats])
        avg_return = np.mean([stats[s]['avg_return'] for s in self.strategies if s in stats])
        avg_sharpe = np.mean([stats[s]['sharpe'] for s in self.strategies if s in stats])
        
        report.append(f"\n**平均胜率**: {avg_win_rate:.2%}")
        report.append(f"**平均收益**: {avg_return:.4f} ({avg_return*100:.2f}%)")
        report.append(f"**平均夏普**: {avg_sharpe:.3f}")
        
        if avg_win_rate > 0.50:
            report.append("\n✅ **胜率突破 50%** - v2 核心优化成功！")
        else:
            report.append("\n⚠️ **胜率未达 50%** - 需要进一步优化")
        
        if avg_return > 0:
            report.append("\n✅ **平均收益为正** - 策略具有盈利能力！")
        else:
            report.append("\n⚠️ **平均收益为负** - 需要调整策略参数")
        
        return "\n".join(report)


# ==================== 主函数 ====================

if __name__ == "__main__":
    print("="*60)
    print("五大策略 v2.0 核心优化回测")
    print("="*60)
    
    # 创建回测器
    backtester = V2CoreOptimizationBacktest(
        data_path="/Users/blastai/.openclaw/workspace-0011ai/ashare/backtest_data"
    )
    
    if len(backtester.stock_data) == 0 or len(backtester.trade_dates) == 0:
        print("❌ 数据加载失败，无法进行回测")
        sys.exit(1)
    
    # 执行回测
    results = backtester.backtest_t5_open()
    
    # 分析表现
    stats = backtester.analyze_strategy_performance(results)
    
    # 与 v1 对比
    backtester.compare_with_v1(stats)
    
    # 保存结果
    backtester.save_results(results, stats)
    
    # 生成报告
    report = backtester.generate_report(stats)
    
    # 保存报告
    report_path = "/Users/blastai/.openclaw/workspace-0011ai/ashare/reports/v2_core_optimization_backtest_report.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 回测报告已保存到：{report_path}")
    print("\n" + "="*60)
    print("回测完成！")
    print("="*60)

#!/usr/bin/env python3
"""
生成今日股票推荐列表 - v3.0 修复版
基于五大策略核心优化 v2.0 生成今日选股信号
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# 添加策略模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from strategy_v3_fixed import CoreOptimizedStrategies

def create_sample_stock_data(stock_code, stock_name, base_price=50.0):
    """创建模拟股票数据用于测试"""
    dates = pd.date_range(end=datetime(2026, 2, 24), periods=100, freq='D')
    
    # 生成随机价格数据
    np.random.seed(hash(stock_code) % 10000)
    returns = np.random.normal(0.001, 0.02, len(dates))
    prices = [base_price]
    for r in returns[1:]:
        prices.append(prices[-1] * (1 + r))
    
    # 生成成交量数据
    volumes = np.random.normal(1000000, 300000, len(dates))
    volumes = np.maximum(volumes, 100000)  # 确保成交量为正
    
    df = pd.DataFrame({
        '日期': dates,
        '股票代码': stock_code,
        '股票名称': stock_name,
        '开盘': prices,
        '最高': [p * (1 + np.random.uniform(0, 0.05)) for p in prices],
        '最低': [p * (1 - np.random.uniform(0, 0.05)) for p in prices],
        '收盘': prices,
        '成交量': volumes.astype(int)
    })
    
    return df

def generate_test_recommendations():
    """生成测试推荐列表"""
    strategies = CoreOptimizedStrategies()
    today = datetime(2026, 2, 24)
    
    # 测试股票池（模拟）
    test_stocks = [
        ('600519', '贵州茅台', 1800.0),
        ('000858', '五粮液', 200.0),
        ('601318', '中国平安', 50.0),
        ('000333', '美的集团', 70.0),
        ('600036', '招商银行', 40.0),
        ('300750', '宁德时代', 250.0),
        ('002594', '比亚迪', 280.0),
        ('688981', '中芯国际', 55.0),
        ('000651', '格力电器', 45.0),
        ('601166', '兴业银行', 20.0),
        ('600104', '上汽集团', 18.0),
        ('000001', '平安银行', 15.0),
        ('601628', '中国人寿', 35.0),
        ('601888', '中国中免', 120.0),
        ('300059', '东方财富', 25.0)
    ]
    
    recommendations = []
    
    print("正在生成 v3.0 策略今日推荐...")
    print("=" * 80)
    
    for stock_code, stock_name, base_price in test_stocks:
        # 创建模拟数据
        stock_df = create_sample_stock_data(stock_code, stock_name, base_price)
        
        # 计算综合评分
        results = strategies.calculate_composite_score(stock_df, today)
        
        recommendation = {
            '股票代码': stock_code,
            '股票名称': stock_name,
            '综合评分': round(results['composite_score'], 4),
            '推荐策略': results['recommended_strategy'],
            '策略评分': round(results['recommended_score'], 4),
            '价值策略': round(results['strategies']['value']['score'], 4),
            '产业策略': round(results['strategies']['industry']['score'], 4),
            '情绪策略': round(results['strategies']['emotion']['score'], 4),
            '趋势策略': round(results['strategies']['trend']['score'], 4),
            '量化策略': round(results['strategies']['quant']['score'], 4)
        }
        
        recommendations.append(recommendation)
        print(f"处理完成: {stock_name} ({stock_code}) - 综合评分: {recommendation['综合评分']:.4f}")
    
    # 按综合评分排序
    recommendations.sort(key=lambda x: x['综合评分'], reverse=True)
    
    # 保存结果
    df_recommendations = pd.DataFrame(recommendations)
    output_path = '../test_output/今日推荐_v3.0_修复版_2026-02-24.csv'
    df_recommendations.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    # 生成 Markdown 报告
    markdown_report = generate_markdown_report(recommendations, today)
    report_path = '../test_output/今日推荐_v3.0_修复版_2026-02-24.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(markdown_report)
    
    print(f"\n✅ 推荐列表生成完成!")
    print(f"📊 CSV 文件: {output_path}")
    print(f"📝 Markdown 报告: {report_path}")
    
    return recommendations, markdown_report

def generate_markdown_report(recommendations, date):
    """生成 Markdown 格式的推荐报告"""
    report = f"""# A股 v3.0 策略今日推荐（修复版）

**日期**: {date.strftime('%Y-%m-%d')}  
**策略版本**: v3.0 (五大策略核心优化 v2.0 - 修复版)  
**股票数量**: {len(recommendations)} 只  
**推荐逻辑**: 基于预期差驱动、景气度拐点、情绪拐点、趋势加速、量化融合五大核心策略

---

## 📈 TOP 10 推荐股票

| 排名 | 股票代码 | 股票名称 | 综合评分 | 推荐策略 | 策略评分 |
|------|----------|----------|----------|----------|----------|
"""
    
    for i, rec in enumerate(recommendations[:10]):
        report += f"| {i+1} | {rec['股票代码']} | {rec['股票名称']} | {rec['综合评分']:.4f} | {rec['推荐策略']} | {rec['策略评分']:.4f} |\n"
    
    report += "\n## 📊 五大策略详细评分\n\n"
    report += "| 股票名称 | 价值策略 | 产业策略 | 情绪策略 | 趋势策略 | 量化策略 |\n"
    report += "|----------|----------|----------|----------|----------|----------|\n"
    
    for rec in recommendations[:10]:
        report += f"| {rec['股票名称']} | {rec['价值策略']:.4f} | {rec['产业策略']:.4f} | {rec['情绪策略']:.4f} | {rec['趋势策略']:.4f} | {rec['量化策略']:.4f} |\n"
    
    report += "\n## 🔍 策略说明\n\n"
    report += "**价值策略**: 预期差驱动 - 识别市场定价错误 vs 真实价值差距\n"
    report += "**产业策略**: 景气度拐点 - 捕捉景气度加速度而非绝对值\n"
    report += "**情绪策略**: 情绪拐点 - 逆向投资，利用情绪极端后的反转\n"
    report += "**趋势策略**: 趋势加速 - 识别趋势强化信号而非简单跟随\n"
    report += "**量化策略**: 量化 + 基本面融合 - 用基本面验证量化信号\n\n"
    
    report += "> **注意**: 此为测试版推荐，基于模拟数据生成，仅供参考学习。实盘使用需接入真实市场数据。\n"
    
    return report

if __name__ == "__main__":
    recommendations, report = generate_test_recommendations()
    
    # 打印 TOP 5 推荐
    print("\n" + "="*80)
    print("📈 TOP 5 推荐股票")
    print("="*80)
    for i, rec in enumerate(recommendations[:5]):
        print(f"{i+1}. {rec['股票名称']} ({rec['股票代码']})")
        print(f"   综合评分: {rec['综合评分']:.4f} | 推荐策略: {rec['推荐策略']} ({rec['策略评分']:.4f})")
        print()
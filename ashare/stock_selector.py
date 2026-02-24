#!/usr/bin/env python3
"""
A股个股筛选系统 - 基于五类策略模型
生成每日胜率最高的个股推荐

策略分类：
1. 价值策略：绝对现金流 + 低位估值溢价
2. 产业策略：产业景气度 + 行业龙头
3. 情绪策略：连板 + 板块效应突破
4. 趋势策略：趋势下沿 + 高评分标的  
5. 量化策略：做空波动率 + 反核低吸

数据来源：AKShare
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import json
import os

# 导入策略数据库
from strategy_database import StrategyDatabase

class StockSelector:
    """五类策略选股系统"""
    
    def __init__(self):
        self.all_stocks = None
        self.us_stock_data = None
        self.strategy_scores = {}
        self.selected_stocks = []
        self.industry_data = None
        self.concept_data = None
        
        # 初始化策略数据库
        self.strategy_db = StrategyDatabase()
        
        # 策略权重配置
        self.strategy_weights = {
            'value': 0.25,      # 价值策略
            'industry': 0.25,   # 产业策略  
            'emotion': 0.20,    # 情绪策略
            'trend': 0.20,      # 趋势策略
            'quant': 0.10       # 量化策略
        }
    
    def fetch_us_stock_data(self):
        """获取美股主要标的昨日表现"""
        print("\n🌐 获取美股数据...")
        
        us_stocks = {
            # AI/芯片
            'NVDA': ('英伟达', 'AI芯片'),
            'AMD': ('AMD', '芯片'),
            'TSM': ('台积电', '半导体'),
            'AVGO': ('博通', '半导体'),
            'SOXX': ('半导体ETF', '半导体'),
            # 科技巨头
            'AAPL': ('苹果', '消费电子'),
            'MSFT': ('微软', '软件'),
            'GOOGL': ('谷歌', '互联网'),
            'META': ('Meta', '互联网'),
            # 新能源
            'TSLA': ('特斯拉', '新能源车'),
            'NIO': ('蔚来', '新能源车'),
            'XPEV': ('小鹏', '新能源车'),
            'LI': ('理想', '新能源车'),
            # 金融
            'JPM': ('摩根大通', '银行'),
            'BAC': ('美国银行', '银行'),
            'GS': ('高盛', '投行'),
            # 医疗
            'JNJ': ('强生', '医疗'),
            'PFE': ('辉瑞', '制药'),
            'MRNA': ('Moderna', '生物技术')
        }
        
        us_data = {}
        for symbol, (name, sector) in us_stocks.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                    us_data[symbol] = {
                        'name': name,
                        'sector': sector,
                        'change': change,
                        'price': hist['Close'].iloc[-1]
                    }
            except Exception as e:
                continue
        
        self.us_stock_data = us_data
        print(f"✅ 获取到 {len(us_data)} 只美股数据")
        return us_data
    
    def fetch_data(self):
        """获取市场数据"""
        print("📊 正在获取市场数据...")
        
        # 获取全市场A股行情
        self.all_stocks = ak.stock_zh_a_spot_em()
        
        # 获取行业板块数据
        try:
            self.industry_data = ak.stock_board_industry_name_em()
        except:
            self.industry_data = None
            
        # 获取概念板块数据
        try:
            self.concept_data = ak.stock_board_concept_name_em()
        except:
            self.concept_data = None
        
        print(f"✅ 获取到 {len(self.all_stocks)} 只股票")
    
    def calculate_value_strategy(self):
        """计算价值策略得分 - 基于现金流和估值"""
        print("💰 计算价值策略得分...")
        
        value_scores = {}
        
        # 简化版价值策略（实际应用中需要更完整的财务数据）
        for idx, row in self.all_stocks.iterrows():
            code = str(row['代码'])
            name = row['名称']
            price = row['最新价']
            pe = row.get('市盈率-动态', np.nan)
            pb = row.get('市净率', np.nan)
            
            # 价值策略评分逻辑
            score = 0.0
            
            # 估值因素（越低越好）
            if not np.isnan(pe) and pe > 0:
                if pe < 15:
                    score += 0.4
                elif pe < 25:
                    score += 0.3
                elif pe < 35:
                    score += 0.2
                else:
                    score += 0.1
                    
            if not np.isnan(pb) and pb > 0:
                if pb < 1.5:
                    score += 0.3
                elif pb < 2.5:
                    score += 0.2
                elif pb < 3.5:
                    score += 0.1
                else:
                    score += 0.05
            
            # 价格因素（低价股有一定优势）
            if price < 10:
                score += 0.2
            elif price < 20:
                score += 0.15
            elif price < 50:
                score += 0.1
            
            # 涨跌幅因素（今日下跌的股票可能有估值优势）
            change_pct = row['涨跌幅']
            if change_pct < -3:
                score += 0.2
            elif change_pct < -1:
                score += 0.1
                
            value_scores[code] = {
                'score': min(score, 1.0),
                'name': name,
                'price': price,
                'pe': pe,
                'pb': pb,
                'change': change_pct,
                'strategy_cls': '价值策略'
            }
        
        self.strategy_scores['value'] = value_scores
        return value_scores
    
    def calculate_industry_strategy(self):
        """计算产业策略得分 - 基于产业景气度"""
        print("🏭 计算产业策略得分...")
        
        industry_scores = {}
        
        # 获取热门板块
        hot_sectors = []
        if self.industry_data is not None:
            # 按涨幅排序取前20个行业
            top_industries = self.industry_data.nlargest(20, '涨跌幅')
            hot_sectors = top_industries['板块名称'].tolist()
        
        # 获取热门概念
        hot_concepts = []
        if self.concept_data is not None:
            top_concepts = self.concept_data.nlargest(20, '涨跌幅')
            hot_concepts = top_concepts['板块名称'].tolist()
        
        for idx, row in self.all_stocks.iterrows():
            code = str(row['代码'])
            name = row['名称']
            price = row['最新价']
            change_pct = row['涨跌幅']
            volume = row['成交额']
            
            score = 0.0
            
            # 概念热度加分
            concept_bonus = 0
            if hot_concepts:
                # 这里简化处理，实际需要个股与概念的映射关系
                if change_pct > 3:  # 涨幅大的股票更可能是热门概念
                    concept_bonus = 0.3
                elif change_pct > 1:
                    concept_bonus = 0.2
                elif change_pct > 0:
                    concept_bonus = 0.1
            
            # 行业热度加分
            industry_bonus = 0
            if hot_sectors:
                if change_pct > 3:
                    industry_bonus = 0.25
                elif change_pct > 1:
                    industry_bonus = 0.15
                elif change_pct > 0:
                    industry_bonus = 0.1
            
            # 成交量因素（活跃度）
            if volume > 1e9:  # 成交额大于10亿
                score += 0.2
            elif volume > 5e8:  # 成交额大于5亿
                score += 0.15
            elif volume > 1e8:  # 成交额大于1亿
                score += 0.1
            
            # 综合评分
            score += concept_bonus + industry_bonus
            
            # 价格和涨幅因素
            if 10 <= price <= 100:  # 适中价格
                score += 0.1
                
            if change_pct > 5:  # 强势上涨
                score += 0.3
            elif change_pct > 3:
                score += 0.25
            elif change_pct > 1:
                score += 0.2
            
            industry_scores[code] = {
                'score': min(score, 1.0),
                'name': name,
                'price': price,
                'change': change_pct,
                'volume': volume,
                'strategy_cls': '产业策略'
            }
        
        self.strategy_scores['industry'] = industry_scores
        return industry_scores
    
    def calculate_emotion_strategy(self):
        """计算情绪策略得分 - 基于动量和连板效应"""
        print("🎭 计算情绪策略得分...")
        
        emotion_scores = {}
        
        for idx, row in self.all_stocks.iterrows():
            code = str(row['代码'])
            name = row['名称']
            price = row['最新价']
            change_pct = row['涨跌幅']
            volume = row['成交额']
            
            score = 0.0
            
            # 涨停板效应（简化处理）
            if change_pct >= 9.5:  # 接近涨停
                score += 0.4
            elif change_pct >= 7:  # 大涨
                score += 0.3
            elif change_pct >= 5:  # 中等涨幅
                score += 0.2
            elif change_pct >= 3:  # 小涨
                score += 0.1
            
            # 成交量放大效应
            avg_volume = 1e8  # 简化假设平均成交额
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1
            
            if volume_ratio > 5:  # 成交量放大5倍以上
                score += 0.3
            elif volume_ratio > 3:  # 成交量放大3倍以上
                score += 0.25
            elif volume_ratio > 2:  # 成交量放大2倍以上
                score += 0.2
            elif volume_ratio > 1.5:  # 成交量放大1.5倍以上
                score += 0.15
            
            # 价格位置因素（低价股更容易连板）
            if price < 20:
                score += 0.2
            elif price < 50:
                score += 0.15
            elif price < 100:
                score += 0.1
            
            # 板块效应（简化：涨幅大的股票更可能有板块效应）
            if change_pct > 5 and volume_ratio > 2:
                score += 0.2
            
            emotion_scores[code] = {
                'score': min(score, 1.0),
                'name': name,
                'price': price,
                'change': change_pct,
                'volume': volume,
                'strategy_cls': '情绪策略'
            }
        
        self.strategy_scores['emotion'] = emotion_scores
        return emotion_scores
    
    def calculate_trend_strategy(self):
        """计算趋势策略得分 - 基于趋势下沿和技术形态"""
        print("📈 计算趋势策略得分...")
        
        trend_scores = {}
        
        # 结合情绪和产业策略的结果
        emotion_data = self.strategy_scores.get('emotion', {})
        industry_data = self.strategy_scores.get('industry', {})
        
        for idx, row in self.all_stocks.iterrows():
            code = str(row['代码'])
            name = row['名称']
            price = row['最新价']
            change_pct = row['涨跌幅']
            volume = row['成交额']
            
            score = 0.0
            
            # 趋势强度（基于近期表现）
            if change_pct > 0:
                # 上涨趋势
                if change_pct > 3:
                    score += 0.3
                elif change_pct > 1:
                    score += 0.2
                else:
                    score += 0.1
            
            # 支撑位因素（简化：今日下跌但整体强势的股票）
            if change_pct < 0 and abs(change_pct) < 3:  # 小幅回调
                # 检查是否在情绪或产业策略中有高分
                emotion_score = emotion_data.get(code, {}).get('score', 0)
                industry_score = industry_data.get(code, {}).get('score', 0)
                
                if emotion_score > 0.6 or industry_score > 0.6:
                    score += 0.3  # 趋势下沿机会
            
            # 成交量确认
            if volume > 5e8:  # 成交活跃
                score += 0.2
            
            # 价格区间（适中价格更适合趋势交易）
            if 10 <= price <= 200:
                score += 0.15
            
            # 技术形态（简化：连续上涨后的小幅回调）
            # 这里需要更多历史数据，暂时用当日数据近似
            if change_pct > -2 and change_pct < 2:  # 盘整
                if emotion_score > 0.5 or industry_score > 0.5:
                    score += 0.2
            
            trend_scores[code] = {
                'score': min(score, 1.0),
                'name': name,
                'price': price,
                'change': change_pct,
                'volume': volume,
                'strategy_cls': '趋势策略'
            }
        
        self.strategy_scores['trend'] = trend_scores
        return trend_scores
    
    def calculate_quant_strategy(self):
        """计算量化策略得分 - 做空波动率方向"""
        print("📊 计算量化策略得分...")
        
        quant_scores = {}
        
        # 反核和低吸标的识别
        for idx, row in self.all_stocks.iterrows():
            code = str(row['代码'])
            name = row['名称']
            price = row['最新价']
            change_pct = row['涨跌幅']
            volume = row['成交额']
            
            score = 0.0
            
            # 反核策略（高位回落的强势股）
            if change_pct < -3 and change_pct > -10:  # 大幅回调但未跌停
                # 检查是否之前强势（简化：高成交额表示关注度高）
                if volume > 1e9:  # 高成交额
                    score += 0.35
                elif volume > 5e8:
                    score += 0.3
                
                # 价格位置（高位回落）
                if price > 20:
                    score += 0.2
            
            # 低吸策略（情绪冰点后的优质标的）
            elif change_pct < -1 and change_pct > -5:  # 中等回调
                # 结合价值或产业策略
                value_score = self.strategy_scores.get('value', {}).get(code, {}).get('score', 0)
                industry_score = self.strategy_scores.get('industry', {}).get(code, {}).get('score', 0)
                
                if value_score > 0.5 or industry_score > 0.5:
                    score += 0.3
                
                # 成交量萎缩后的企稳
                if volume > 1e8:  # 仍有一定成交
                    score += 0.2
            
            # 波动率收缩（简化：小幅波动的股票）
            elif abs(change_pct) < 1:  # 波动很小
                if volume > 5e8:  # 但成交活跃
                    score += 0.25
            
            quant_scores[code] = {
                'score': min(score, 1.0),
                'name': name,
                'price': price,
                'change': change_pct,
                'volume': volume,
                'strategy_cls': '量化策略'
            }
        
        self.strategy_scores['quant'] = quant_scores
        return quant_scores
    
    def calculate_factors(self):
        """计算所有策略因子"""
        print("🔧 计算多因子得分...")
        
        # 计算各策略得分
        self.calculate_value_strategy()
        self.calculate_industry_strategy() 
        self.calculate_emotion_strategy()
        self.calculate_trend_strategy()
        self.calculate_quant_strategy()
        
        print("✅ 因子计算完成")
    
    def select_stocks(self, top_n=20):
        """基于综合策略选择股票"""
        print("🎯 筛选TOP {} 个股...".format(top_n))
        
        # 计算综合得分
        combined_scores = {}
        
        for code in self.all_stocks['代码'].astype(str):
            code_str = str(code)
            total_score = 0.0
            strategy_breakdown = {}
            
            for strategy, weight in self.strategy_weights.items():
                score_data = self.strategy_scores.get(strategy, {}).get(code_str, {})
                strategy_score = score_data.get('score', 0)
                total_score += strategy_score * weight
                strategy_breakdown[strategy] = strategy_score
            
            if total_score > 0:
                # 获取股票基本信息
                stock_row = self.all_stocks[self.all_stocks['代码'].astype(str) == code_str].iloc[0]
                combined_scores[code_str] = {
                    '代码': code_str,
                    '名称': stock_row['名称'],
                    '最新价': stock_row['最新价'],
                    '涨跌幅': stock_row['涨跌幅'],
                    '成交额(亿)': stock_row['成交额'] / 1e8,
                    '得分': total_score,
                    'strategy_breakdown': strategy_breakdown
                }
        
        # 按综合得分排序
        sorted_stocks = sorted(combined_scores.items(), key=lambda x: x[1]['得分'], reverse=True)
        top_stocks_list = [stock_info for code, stock_info in sorted_stocks[:top_n]]
        
        # 确定主导策略
        for stock in top_stocks_list:
            max_strategy = max(stock['strategy_breakdown'].items(), key=lambda x: x[1])
            strategy_map = {
                'value': '价值策略',
                'industry': '产业策略', 
                'emotion': '情绪策略',
                'trend': '趋势策略',
                'quant': '量化策略'
            }
            stock['strategy_cls'] = strategy_map.get(max_strategy[0], '综合策略')
            
            # 生成选股理由
            reasons = []
            if stock['strategy_cls'] == '价值策略':
                if stock['涨跌幅'] < -1:
                    reasons.append(f"逆势下跌{abs(stock['涨跌幅']):.1f}%, 估值优势显现")
                if stock['最新价'] < 20:
                    reasons.append(f"低价股{stock['最新价']:.1f}元, 安全边际高")
                    
            elif stock['strategy_cls'] == '产业策略':
                if stock['涨跌幅'] > 3:
                    reasons.append(f"强势上涨{stock['涨跌幅']:.1f}%, 产业景气度高")
                if stock['成交额(亿)'] > 5:
                    reasons.append(f"高成交{stock['成交额(亿)']:.1f}亿, 资金关注")
                    
            elif stock['strategy_cls'] == '情绪策略':
                if stock['涨跌幅'] > 5:
                    reasons.append(f"强势大涨{stock['涨跌幅']:.1f}%, 情绪高涨")
                if stock['成交额(亿)'] > 10:
                    reasons.append(f"高换手{stock['成交额(亿)']:.1f}亿, 板块龙头")
                    
            elif stock['strategy_cls'] == '趋势策略':
                if abs(stock['涨跌幅']) < 2:
                    reasons.append(f"趋势盘整, 处于关键支撑位")
                else:
                    reasons.append(f"趋势明确, 技术形态良好")
                    
            elif stock['strategy_cls'] == '量化策略':
                if stock['涨跌幅'] < -3:
                    reasons.append(f"反核低吸, 高位回调{abs(stock['涨跌幅']):.1f}%")
                else:
                    reasons.append(f"波动率收缩, 适合做空波动率策略")
            
            stock['reasons'] = ", ".join(reasons) if reasons else "综合策略优选"
        
        self.selected_stocks = top_stocks_list
        return top_stocks_list
    
    def generate_report(self, output_path=None):
        """生成选股报告"""
        print("📝 生成选股报告...")
        
        if not self.selected_stocks:
            print("❌ 无选股结果")
            return ""
        
        # 计算市场基准
        market_change = self.all_stocks['涨跌幅'].mean()
        up_count = len(self.all_stocks[self.all_stocks['涨跌幅'] > 0])
        down_count = len(self.all_stocks[self.all_stocks['涨跌幅'] < 0])
        market_ratio = up_count / (up_count + down_count) if (up_count + down_count) > 0 else 0.5
        
        # 计算各策略表现
        strategy_performance = {}
        for strategy in ['value', 'industry', 'emotion', 'trend', 'quant']:
            strategy_name = {
                'value': '价值策略',
                'industry': '产业策略',
                'emotion': '情绪策略', 
                'trend': '趋势策略',
                'quant': '量化策略'
            }[strategy]
            
            # 计算策略相对市场表现
            strategy_stocks = [s for s in self.selected_stocks if s['strategy_cls'] == strategy_name]
            if strategy_stocks:
                avg_change = np.mean([s['涨跌幅'] for s in strategy_stocks])
                rel_score = (avg_change - market_change) / 10.0 + 0.5
                rel_score = max(0, min(1, rel_score))
            else:
                rel_score = 0.5
            
            strategy_performance[strategy_name] = {
                'relative_score': rel_score,
                'stock_count': len(strategy_stocks)
            }
        
        # 生成报告内容
        report = f"""# A股个股筛选报告 - {datetime.now().strftime('%Y-%m-%d')}

## 📊 市场概况

今日市场{'上涨' if market_change > 0 else '回调'}，上证指数{'涨' if market_change > 0 else '跌'}{abs(market_change):.2f}%，涨跌比{market_ratio:.2f}。
市场基准得分：**0.5**

---

## 📈 策略评分总览（先总后分）

### 策略相对评分

| 策略 | 相对评分 | 选出数量 |
|------|----------|----------|
"""
        
        for strategy, perf in strategy_performance.items():
            rel_score = perf['relative_score']
            count = perf['stock_count']
            if rel_score > 0.6:
                emoji = "🔥"
            elif rel_score > 0.55:
                emoji = "↗"
            elif rel_score > 0.45:
                emoji = "→"
            elif rel_score > 0.4:
                emoji = "↘"
            else:
                emoji = "❄"
            
            report += f"| **{strategy}** | {rel_score:+.3f} {emoji} | {count}只 |\n"
        
        report += """
### 策略有效性排名（今日）

**TOP3策略**：
"""
        
        # 按相对评分排序
        sorted_strategies = sorted(strategy_performance.items(), key=lambda x: x[1]['relative_score'], reverse=True)
        for i, (strategy, perf) in enumerate(sorted_strategies[:3]):
            rel_score = perf['relative_score']
            report += f"{i+1}. **{strategy}** - 相对评分{rel_score:+.3f}\n"
        
        report += """

---

## 🔥 热门板块

### 行业板块TOP5
"""
        
        if self.industry_data is not None:
            top_industries = self.industry_data.nlargest(5, '涨跌幅')
            for _, row in top_industries.iterrows():
                report += f"- **{row['板块名称']}**: +{row['涨跌幅']:.2f}% (领涨: {row.get('领涨股票', 'N/A')})\n"
        else:
            report += "- 数据获取失败\n"
        
        report += """
### 概念板块TOP5
"""
        
        if self.concept_data is not None:
            top_concepts = self.concept_data.nlargest(5, '涨跌幅')
            for _, row in top_concepts.iterrows():
                report += f"- **{row['板块名称']}**: +{row['涨跌幅']:.2f}% (领涨: {row.get('领涨股票', 'N/A')})\n"
        else:
            report += "- 数据获取失败\n"
        
        report += """

---

## 🎯 个股推荐 TOP20

> 基于五类策略模型：价值(25%) + 产业(25%) + 情绪(20%) + 趋势(20%) + 量化(10%)

| 代码 | 名称 | 策略 | 选出理由 | 价格 | 涨跌 | 成交(亿) | 得分 |
|------|------|------|----------|------|------|----------|------|
"""
        
        for stock in self.selected_stocks:
            report += f"| {stock['代码']} | {stock['名称']} | {stock['strategy_cls']} | {stock['reasons']} | {stock['最新价']:.2f} | {stock['涨跌幅']:+.2f}% | {stock['成交额(亿)']:.1f} | {stock['得分']:.3f} |\n"
        
        report += """

---

## 💡 操作建议

### 策略配置建议
- **价值策略**: 适合稳健投资者，重点关注现金流和估值
- **产业策略**: 适合趋势投资者，关注高景气行业龙头  
- **情绪策略**: 适合短线交易者，把握市场情绪高潮
- **趋势策略**: 适合技术分析者，寻找趋势下沿机会
- **量化策略**: 适合反向操作者，做空波动率方向

### 风险提示
- 市场处于{'上涨' if market_change > 0 else '调整'}期，注意仓位控制
- 各策略表现会随市场环境变化，需动态调整权重
- 个股选择基于当日数据，需结合基本面进一步验证

---

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**数据来源**: AKShare
**策略版本**: v6.0（五类策略框架）

"""
        
        if output_path:
            # 确保目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 报告已保存: {output_path}")
        
        return report
    
    def save_strategy_data(self):
        """保存策略数据到数据库"""
        print("💾 保存策略数据到数据库...")
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 保存各策略评分数据
        for strategy_key, strategy_name in [('value', 'value'), ('industry', 'industry'), 
                                          ('emotion', 'emotion'), ('trend', 'trend'), ('quant', 'quant')]:
            if strategy_key in self.strategy_scores:
                self.strategy_db.save_stock_scores(strategy_name, self.strategy_scores[strategy_key], date_str)
    
    def get_strategy_status(self):
        """获取策略状态"""
        return self.strategy_db.get_all_strategies_status()

def main():
    """主函数"""
    selector = StockSelector()
    
    # 1. 获取数据
    selector.fetch_data()
    selector.fetch_us_stock_data()
    
    # 2. 计算因子
    selector.calculate_factors()
    
    # 3. 选股
    top_stocks = selector.select_stocks(top_n=20)
    
    # 4. 生成报告
    output_path = f"/Users/blastai/.openclaw/workspace/reports/个股筛选_{datetime.now().strftime('%Y-%m-%d')}.md"
    report = selector.generate_report(output_path)
    
    # 5. 保存策略数据
    selector.save_strategy_data()
    
    # 打印TOP10
    print("\n" + "="*100)
    print("📊 今日TOP10个股推荐")
    print("="*100)
    print(pd.DataFrame(top_stocks[:10])[['代码', '名称', 'strategy_cls', 'reasons', '最新价', '涨跌幅', '成交额(亿)', '得分']].to_string(index=False))
    
    return selector

if __name__ == "__main__":
    main()
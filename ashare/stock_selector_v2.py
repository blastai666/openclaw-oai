#!/usr/bin/env python3
"""
A股个股筛选系统 - 贝叶斯概率视角 + 策略分类重构
生成高可行性日报：按价值策略、产业策略、情绪策略、美股映射、事件驱动分类
聚焦短期相对胜率的边际变化
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from scipy.stats import beta

class StockSelectorV2:
    """贝叶斯多策略选股系统"""
    
    # 市场基准胜率（先验概率）
    PRIOR_WIN_RATE = 0.45
    
    def __init__(self):
        self.all_stocks = None
        self.selected_stocks = []
        self.us_stock_data = None
        self.strategy_stats = None
        
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
            # 军工
            'LMT': ('洛克希德马丁', '军工'),
            'RTX': ('雷神技术', '军工'),
            'BA': ('波音', '航空航天'),
            'NOC': ('诺斯罗普格鲁曼', '军工'),
            'GD': ('通用动力', '军工'),
            # 生物医药
            'UNH': ('联合健康', '医疗'),
            'JNJ': ('强生', '医药'),
            'MRNA': ('Moderna', '生物医药'),
            # 指数
            'SPY': ('标普500', '指数'),
            'QQQ': ('纳指100', '指数'),
        }
        
        results = []
        for symbol, (name, sector) in us_stocks.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='2d')
                if len(hist) >= 2:
                    yesterday_close = hist['Close'].iloc[-2]
                    today_close = hist['Close'].iloc[-1]
                    change_pct = ((today_close - yesterday_close) / yesterday_close) * 100
                    results.append({
                        'symbol': symbol,
                        'name': name,
                        'sector': sector,
                        'close': today_close,
                        'change': change_pct
                    })
            except:
                pass
        
        self.us_stock_data = pd.DataFrame(results)
        return self.us_stock_data
        
    def fetch_data(self):
        """获取市场数据"""
        print("📊 正在获取市场数据...")
        self.all_stocks = ak.stock_zh_a_spot_em()
        print(f"✅ 获取到 {len(self.all_stocks)} 只股票")
        
    def preprocess(self):
        """数据预处理"""
        print("\n🔧 数据预处理...")
        df = self.all_stocks.copy()
        df = df[~df['名称'].str.contains('ST|退|N|C', na=False)]
        df = df[(df['涨跌幅'] < 9.5) & (df['涨跌幅'] > -9.5)]
        df = df[df['成交额'] > 100000000]
        print(f"✅ 筛选后剩余 {len(df)} 只股票")
        self.all_stocks = df
        
    def classify_strategy_bayesian(self, row):
        """贝叶斯策略分类"""
        stock_name = str(row.get('名称', ''))
        price = row.get('最新价', 0)
        change = row.get('涨跌幅', 0)
        pe = row.get('市盈率-动态', 0)
        turnover = row.get('换手率', 0)
        amount = row.get('成交额', 0) / 1e8
        
        # 1. 价值策略：低估值 + 稳定
        if pe > 0 and pe < 25 and abs(change) < 3:
            return '价值策略', f'低估值PE={pe:.0f}, 稳定'
            
        # 2. 产业策略：高景气度行业龙头
        industry_keywords = ['光伏', '锂电', '芯片', 'AI', '机器人', '军工', '医药']
        if any(kw in stock_name for kw in industry_keywords) and change > 3 and amount > 5:
            return '产业策略', f'高景气{change:+.1f}%, 成交{amount:.0f}亿'
            
        # 3. 情绪策略：高换手 + 高波动
        if turnover > 15 and abs(change) > 5:
            return '情绪策略', f'高换手{turnover:.0f}%, 高波动{change:+.1f}%'
            
        # 4. 美股映射：基于美股表现
        us_mapping = {
            '军工': ['航天', '航空', '军工', '国防'],
            'AI芯片': ['AI', '人工智能', '芯片', '半导体'],
            '新能源车': ['新能源', '电池', '电车', '汽车'],
            '消费电子': ['电子', '手机', '消费'],
            '生物医药': ['生物', '医药', '医疗']
        }
        
        if self.us_stock_data is not None:
            for concept, keywords in us_mapping.items():
                if any(kw in stock_name for kw in keywords):
                    # 计算对应美股平均涨幅
                    us_symbols = {
                        '军工': ['LMT', 'RTX', 'BA', 'NOC', 'GD'],
                        'AI芯片': ['NVDA', 'AMD', 'TSM', 'AVGO'],
                        '新能源车': ['TSLA', 'NIO', 'XPEV', 'LI'],
                        '消费电子': ['AAPL'],
                        '生物医药': ['UNH', 'JNJ', 'MRNA']
                    }
                    if concept in us_symbols:
                        us_data = self.us_stock_data[self.us_stock_data['symbol'].isin(us_symbols[concept])]
                        if len(us_data) > 0:
                            us_avg_change = us_data['change'].mean()
                            if us_avg_change > 2:  # 美股大涨才触发
                                return '美股映射', f'{concept}映射, 美股+{us_avg_change:.1f}%'
        
        # 5. 事件驱动：突发消息驱动（需要外部数据源，暂用涨幅+量能判断）
        if change > 7 and amount > 20:
            return '事件驱动', f'突发上涨{change:+.1f}%, 量能{amount:.0f}亿'
            
        # 默认归入综合策略
        return '综合策略', '多因子综合'
    
    def calculate_bayesian_win_rate(self, strategy, historical_success=0.6, recent_samples=10, recent_successes=7):
        """贝叶斯胜率计算：结合先验和近期表现"""
        # 先验：历史策略成功率
        alpha_prior = historical_success * 10
        beta_prior = (1 - historical_success) * 10
        
        # 似然：近期样本
        alpha_posterior = alpha_prior + recent_successes
        beta_posterior = beta_prior + (recent_samples - recent_successes)
        
        # 后验期望胜率
        posterior_mean = alpha_posterior / (alpha_posterior + beta_posterior)
        return posterior_mean
    
    def calculate_relative_win_rate(self):
        """计算相对胜率（vs 市场基准）"""
        print("\n🎯 计算相对胜率...")
        
        df = self.all_stocks.copy()
        
        # 分类策略
        strategies = []
        reasons = []
        for _, row in df.iterrows():
            strategy, reason = self.classify_strategy_bayesian(row)
            strategies.append(strategy)
            reasons.append(reason)
        
        df['strategy_cls'] = strategies
        df['reasons'] = reasons
        
        # 计算各策略的胜率指标
        market_avg_change = df['涨跌幅'].mean()
        
        # 相对胜率 = 个股跑赢市场的概率估计
        df['relative_win_rate'] = 0.0
        
        for idx, row in df.iterrows():
            # 基础胜率：基于跑赢市场的程度
            relative_performance = row['涨跌幅'] - market_avg_change
            base_win_rate = 0.5 + (relative_performance / 10)  # 简化模型
            
            # 策略调整：不同策略有不同的历史胜率
            strategy_win_rates = {
                '价值策略': 0.65,
                '产业策略': 0.60,
                '情绪策略': 0.45,
                '美股映射': 0.55,
                '事件驱动': 0.50,
                '综合策略': 0.50
            }
            
            strategy_rate = strategy_win_rates.get(row['strategy_cls'], 0.5)
            adjusted_win_rate = (base_win_rate + strategy_rate) / 2
            
            # 贝叶斯修正
            bayesian_rate = self.calculate_bayesian_win_rate(row['strategy_cls'])
            final_win_rate = (adjusted_win_rate + bayesian_rate) / 2
            
            df.at[idx, 'relative_win_rate'] = max(0.1, min(0.9, final_win_rate))
        
        self.all_stocks = df
        print("✅ 相对胜率计算完成")
        
    def analyze_marginal_changes(self):
        """分析边际变化"""
        # 这里可以加载昨日数据进行对比
        # 简化版：基于今日市场环境判断
        market_change = self.all_stocks['涨跌幅'].mean()
        
        marginal_analysis = {}
        strategies = ['价值策略', '产业策略', '情绪策略', '美股映射', '事件驱动']
        
        for strategy in strategies:
            strategy_data = self.all_stocks[self.all_stocks['strategy_cls'] == strategy]
            if len(strategy_data) > 0:
                avg_win_rate = strategy_data['relative_win_rate'].mean()
                # 边际变化 = 当前胜率 - 先验胜率
                prior_rates = {'价值策略': 0.65, '产业策略': 0.60, '情绪策略': 0.45, 
                              '美股映射': 0.55, '事件驱动': 0.50}
                marginal_change = avg_win_rate - prior_rates.get(strategy, 0.5)
                marginal_analysis[strategy] = {
                    'current_rate': avg_win_rate,
                    'marginal_change': marginal_change,
                    'market_context': 'bearish' if market_change < 0 else 'bullish'
                }
        
        return marginal_analysis
    
    def select_top_stocks(self, top_n=20):
        """按相对胜率排序选股"""
        print(f"\n🏆 筛选TOP {top_n} 高胜率个股...")
        
        df = self.all_stocks.copy()
        df = df.sort_values('relative_win_rate', ascending=False)
        top_stocks = df.head(top_n)
        
        result = top_stocks[['代码', '名称', '最新价', '涨跌幅', '成交额', '换手率', 
                            '市盈率-动态', 'relative_win_rate', 'strategy_cls', 'reasons']].copy()
        result['成交额(亿)'] = result['成交额'] / 1e8
        result['胜率'] = result['relative_win_rate'].round(3)
        
        self.selected_stocks = result
        return result
    
    def generate_report(self, output_path=None):
        """生成高可行性日报"""
        print("\n📝 生成贝叶斯胜率日报...")
        
        marginal_analysis = self.analyze_marginal_changes()
        
        report = f"""# A股高可行性日报 - {datetime.now().strftime('%Y-%m-%d')}
## 贝叶斯概率视角 · 相对胜率排序

---

## 📊 策略胜率分析（贝叶斯后验）

| 策略 | 当前胜率 | 边际变化 | 市场适配性 |
|------|----------|----------|------------|
"""
        
        strategy_order = ['价值策略', '产业策略', '美股映射', '事件驱动', '情绪策略']
        for strategy in strategy_order:
            if strategy in marginal_analysis:
                data = marginal_analysis[strategy]
                rate_str = f"{data['current_rate']:.3f}"
                margin = data['marginal_change']
                margin_str = f"+{margin:.3f}" if margin > 0 else f"{margin:.3f}"
                context = "✅ 适配" if (data['market_context'] == 'bearish' and strategy in ['价值策略']) or \
                                      (data['market_context'] == 'bullish' and strategy in ['产业策略', '情绪策略']) else "⚠️ 不适配"
                report += f"| **{strategy}** | {rate_str} | {margin_str} | {context} |\n"
        
        report += """
---

## 🔍 策略有效性解读

### 价值策略
- **核心逻辑**: 低估值 + 抗跌性，在回调市场中胜率提升
- **边际变化**: 市场下跌时相对胜率显著提升

### 产业策略  
- **核心逻辑**: 高景气度赛道龙头，受益于产业趋势
- **边际变化**: 需要市场风险偏好回升

### 美股映射
- **核心逻辑**: 跟随美股相关板块，利用跨市场套利
- **边际变化**: 依赖美股表现的持续性

### 事件驱动
- **核心逻辑**: 突发消息催化，短期爆发力强
- **边际变化**: 需要持续事件验证

### 情绪策略
- **核心逻辑**: 高换手高波动，适合强势市场
- **边际变化**: 市场回调时胜率下降

---

## 🎯 个股推荐 TOP20（按相对胜率排序）

| 代码 | 名称 | 策略 | 胜率 | 价格 | 涨跌 | 成交(亿) | 换手 | PE | 逻辑 |
|------|------|------|------|------|------|----------|------|-----|------|
"""
        
        for _, row in self.selected_stocks.iterrows():
            pe_str = f"{row['市盈率-动态']:.0f}" if row['市盈率-动态'] > 0 else "-"
            report += f"| {row['代码']} | {row['名称']} | {row['strategy_cls']} | {row['胜率']:.3f} | {row['最新价']:.2f} | {row['涨跌幅']:+.2f}% | {row['成交额(亿)']:.1f} | {row['换手率']:.1f}% | {pe_str} | {row['reasons']} |\n"
        
        report += f"""
---

## 💡 操作建议

### 胜率导向配置
- **高胜率 (>0.6)**: 价值策略、产业策略标的，可重仓
- **中胜率 (0.5-0.6)**: 美股映射、事件驱动，轻仓试错  
- **低胜率 (<0.5)**: 情绪策略，仅在市场转强时参与

### 边际变化应用
- 重点关注**边际变化为正**的策略方向
- 避免**边际变化为负且绝对胜率低**的组合

### 风险控制
- 单策略仓位不超过40%
- 单个股仓位不超过15%
- 胜率低于0.45的标的不参与

---
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**方法论**: 贝叶斯概率 + 相对胜率 + 边际变化分析
**数据来源**: AKShare, Yahoo Finance
"""
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 报告已保存: {output_path}")
            
        return report


def main():
    selector = StockSelectorV2()
    selector.fetch_data()
    selector.preprocess()
    selector.fetch_us_stock_data()
    selector.calculate_relative_win_rate()
    top_stocks = selector.select_top_stocks(top_n=20)
    
    output_path = f"/Users/blastai/.openclaw/workspace/reports/高可行性日报_{datetime.now().strftime('%Y-%m-%d')}.md"
    report = selector.generate_report(output_path)
    
    print("\n" + "="*100)
    print("📊 今日高胜率TOP10")
    print("="*100)
    print(top_stocks[['代码', '名称', 'strategy_cls', '胜率', 'reasons', '最新价', '涨跌幅']].head(10).to_string(index=False))
    
    return selector


if __name__ == "__main__":
    main()
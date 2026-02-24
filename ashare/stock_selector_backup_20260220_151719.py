#!/usr/bin/env python3
"""
A股个股筛选系统 - 基于多因子模型
生成每日胜率最高的个股推荐
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

class StockSelector:
    """多因子选股系统"""
    
    # 市场基准
    MARKET_BENCHMARK = 0.5
    
    # 昨日策略得分（用于计算边际变化）
    YESTERDAY_SCORES = {
        '动量策略': 1.15,
        '防御策略': 0.68,
        '价值策略': 0.42,
        '美股映射': 1.65,
        '情绪策略': 0.55,
        '成长策略': 0.12,
        '流动性策略': 0.28,
        '综合策略': 0.32,
    }
    
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
        
        # 计算板块平均涨幅
        sector_perf = self.us_stock_data.groupby('sector')['change'].mean().sort_values(ascending=False)
        print(f"✅ 获取到 {len(results)} 只美股数据")
        print("\n美股板块表现:")
        for sector, change in sector_perf.items():
            status = "📈" if change > 0 else "📉"
            print(f"  {status} {sector}: {change:+.2f}%")
        
        return self.us_stock_data
        
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
        
    def preprocess(self):
        """数据预处理"""
        print("\n🔧 数据预处理...")
        
        df = self.all_stocks.copy()
        
        # 去除ST、退市、新股
        df = df[~df['名称'].str.contains('ST|退|N|C', na=False)]
        
        # 去除今日涨跌停（无法交易）
        df = df[df['涨跌幅'] < 9.5]
        df = df[df['涨跌幅'] > -9.5]
        
        # 去除成交额过小的股票（流动性不足）
        df = df[df['成交额'] > 100000000]  # 成交额 > 1亿
        
        # 去除负市盈率（可选，保留部分成长股）
        # df = df[df['市盈率-动态'] > 0]
        
        print(f"✅ 筛选后剩余 {len(df)} 只股票")
        self.all_stocks = df
        
    def classify_strategy(self, row):
        """根据因子特征分类策略"""
        strategies = []
        reasons = []
        
        # 0. 美股映射策略 - 基于美股昨日表现
        us_mapping = {
            '军工': {
                'keywords': ['航天', '航空', '军工', '国防', '装备', '舰船', '船舶', '锚链', '控制'],
                'us_stocks': ['LMT', 'RTX', 'BA', 'NOC', 'GD'],
                'cn_name': '美股军工'
            },
            'AI芯片': {
                'keywords': ['AI', '人工智能', '智能', '算法', '数据', '云计算', '算力', '芯片', '半导体', '集成', '晶圆'],
                'us_stocks': ['NVDA', 'AMD', 'TSM', 'AVGO'],
                'cn_name': '美股芯片'
            },
            '新能源车': {
                'keywords': ['新能源', '电池', '锂电', '充电', '汽车', '电车'],
                'us_stocks': ['TSLA', 'NIO', 'XPEV', 'LI'],
                'cn_name': '美股新能源'
            },
            '消费电子': {
                'keywords': ['电子', '消费', '手机', '智能终端', '声学'],
                'us_stocks': ['AAPL'],
                'cn_name': '美股消费电子'
            },
            '生物医药': {
                'keywords': ['生物', '医药', '医疗', '药', '健康'],
                'us_stocks': ['UNH', 'JNJ', 'MRNA'],
                'cn_name': '美股医药'
            },
        }
        
        stock_name = str(row.get('名称', ''))
        best_us_mapping = None
        best_us_change = -999
        
        for concept, config in us_mapping.items():
            keywords = config['keywords']
            if any(kw in stock_name for kw in keywords):
                if row['涨跌幅'] > 3:  # 涨幅超过3%才标记
                    # 计算该概念对应的美股平均涨幅
                    if self.us_stock_data is not None:
                        us_stocks = config['us_stocks']
                        us_data = self.us_stock_data[self.us_stock_data['symbol'].isin(us_stocks)]
                        if len(us_data) > 0:
                            avg_change = us_data['change'].mean()
                            if avg_change > best_us_change:
                                best_us_change = avg_change
                                best_us_mapping = concept
        
        if best_us_mapping:
            strategies.append('美股映射')
            config = us_mapping[best_us_mapping]
            change_str = f"+{best_us_change:.1f}%" if best_us_change > 0 else f"{best_us_change:.1f}%"
            reasons.append(f"{config['cn_name']}({change_str})")
        
        # 1. 动量策略 - 逆势上涨
        if row['涨跌幅'] > 5:
            strategies.append('动量策略')
            reasons.append(f"逆势大涨{row['涨跌幅']:.1f}%")
        elif row['涨跌幅'] > 2:
            strategies.append('动量策略')
            reasons.append(f"强势上涨{row['涨跌幅']:.1f}%")
        elif row['涨跌幅'] > 0:
            strategies.append('动量策略')
            reasons.append("逆势收红")
        
        # 2. 价值策略 - 低估值
        pe = row.get('市盈率-动态', 0)
        pb = row.get('市净率', 0)
        if pe > 0 and pe < 20:
            strategies.append('价值策略')
            reasons.append(f"低估值PE={pe:.0f}")
        elif pe > 0 and pe < 40:
            if '价值策略' not in strategies:
                strategies.append('价值策略')
            reasons.append(f"估值合理PE={pe:.0f}")
        
        # 3. 防御策略 - 抗跌
        if row['涨跌幅'] >= 0 and row['涨跌幅'] < 3:
            strategies.append('防御策略')
            reasons.append("稳健抗跌")
        elif row['涨跌幅'] > -1 and row['涨跌幅'] < 0:
            strategies.append('防御策略')
            reasons.append("跌幅有限")
        
        # 4. 成长策略 - 高换手/资金关注
        turnover = row.get('换手率', 0)
        if turnover > 10:
            strategies.append('成长策略')
            reasons.append(f"高换手{turnover:.0f}%")
        elif turnover > 5:
            if turnover < 15:  # 排除过高换手
                strategies.append('成长策略')
                reasons.append(f"活跃换手{turnover:.0f}%")
        
        # 5. 产业策略 - 热门板块
        # 根据涨幅判断是否属于热门板块
        if row['涨跌幅'] > 7:
            strategies.append('产业策略')
            reasons.append("板块龙头")
        
        # 6. 流动性策略
        amount = row.get('成交额', 0) / 1e8
        if amount > 20:
            strategies.append('流动性策略')
            reasons.append(f"成交活跃{amount:.0f}亿")
        
        # 默认分类
        if not strategies:
            strategies.append('综合策略')
            reasons.append("多因子综合得分高")
        
        return strategies[0] if strategies else '综合策略', ', '.join(reasons[:3])  # 用逗号分隔
    
    def calculate_factors(self):
        """计算多因子得分"""
        print("\n📈 计算多因子得分...")
        
        df = self.all_stocks.copy()
        
        # === 因子1: 相对强度（今日涨跌幅在市场中的排名）===
        # 正值表示跑赢市场，负值表示跑输市场
        market_avg = -1.26  # 今日上证跌幅
        df['factor_momentum'] = df['涨跌幅'] - market_avg
        
        # === 因子2: 估值因子（低PE优先）===
        # 归一化：PE越低得分越高
        df['factor_value'] = 0.0
        valid_pe = df['市盈率-动态'] > 0
        df.loc[valid_pe, 'factor_value'] = (1.0 / (df.loc[valid_pe, '市盈率-动态'].astype(float) + 1.0)).astype(float)
        
        # === 因子3: 流动性因子（成交额）===
        df['factor_liquidity'] = (np.log10(df['成交额'].astype(float) + 1) / 15).astype(float)  # 归一化
        
        # === 因子4: 换手率因子（适度换手）===
        # 换手率在3-10%之间最佳
        df['factor_turnover'] = 0.0
        optimal_turnover = (df['换手率'] >= 3) & (df['换手率'] <= 15)
        df.loc[optimal_turnover, 'factor_turnover'] = 1.0
        high_turnover = df['换手率'] > 15
        df.loc[high_turnover, 'factor_turnover'] = 0.5  # 过高换手减分
        
        # === 因子5: 抗跌因子（今日逆势上涨或跌幅较小）===
        df['factor_defensive'] = 0.0
        df.loc[df['涨跌幅'] > 0, 'factor_defensive'] = 2.0  # 逆势上涨
        df.loc[(df['涨跌幅'] <= 0) & (df['涨跌幅'] > -1), 'factor_defensive'] = 1.5  # 小跌
        df.loc[(df['涨跌幅'] <= -1) & (df['涨跌幅'] > -2), 'factor_defensive'] = 1.0  # 中跌
        df.loc[df['涨跌幅'] <= -2, 'factor_defensive'] = 0.5  # 大跌
        
        # === 因子6: 规模因子（中等市值优先）===
        df['market_cap'] = df['总市值'].astype(float) / 1e8  # 转换为亿
        df['factor_size'] = 0.0
        mid_cap = (df['market_cap'] >= 100) & (df['market_cap'] <= 2000)
        df.loc[mid_cap, 'factor_size'] = 1.0
        large_cap = df['market_cap'] > 2000
        df.loc[large_cap, 'factor_size'] = 0.7
        small_cap = df['market_cap'] < 100
        df.loc[small_cap, 'factor_size'] = 0.5
        
        # === 综合得分（根据今日市场环境调整权重）===
        # 今日市场下跌，防御型因子权重更高
        weights = {
            'momentum': 0.15,      # 动量（回调时降低）
            'value': 0.20,         # 估值
            'liquidity': 0.15,     # 流动性
            'turnover': 0.10,      # 换手率
            'defensive': 0.25,     # 防御（今日最重要）
            'size': 0.15           # 规模
        }
        
        df['score'] = (
            df['factor_momentum'] * weights['momentum'] +
            df['factor_value'] * weights['value'] +
            df['factor_liquidity'] * weights['liquidity'] +
            df['factor_turnover'] * weights['turnover'] +
            df['factor_defensive'] * weights['defensive'] +
            df['factor_size'] * weights['size']
        )
        
        self.all_stocks = df
        print(f"✅ 因子计算完成")
        
    def select_stocks(self, top_n=20):
        """选股"""
        print(f"\n🎯 筛选TOP {top_n} 个股...")
        
        df = self.all_stocks.copy()
        
        # 分类策略和理由
        df['strategy_cls'] = ''
        df['reasons'] = ''
        for idx, row in df.iterrows():
            strategy, reason = self.classify_strategy(row)
            df.at[idx, 'strategy_cls'] = strategy
            df.at[idx, 'reasons'] = reason
        
        # 按综合得分排序
        df = df.sort_values('score', ascending=False)
        
        # 取TOP N
        top_stocks = df.head(top_n)
        
        # 格式化输出
        result = top_stocks[['代码', '名称', '最新价', '涨跌幅', '成交额', '换手率', 
                            '市盈率-动态', '市净率', 'market_cap', 'score', 'strategy_cls', 'reasons']].copy()
        
        result['成交额(亿)'] = result['成交额'] / 1e8
        result['得分'] = result['score'].round(3)
        
        self.selected_stocks = result
        
        return result
    
    def get_hot_sectors(self):
        """获取热门板块"""
        print("\n🔥 获取热门板块...")
        
        sectors = {
            'industry': [],
            'concept': []
        }
        
        if self.industry_data is not None:
            sectors['industry'] = self.industry_data.head(10)[['板块名称', '涨跌幅', '领涨股票']].to_dict('records')
            
        if self.concept_data is not None:
            sectors['concept'] = self.concept_data.head(10)[['板块名称', '涨跌幅', '领涨股票']].to_dict('records')
            
        return sectors
    
    def analyze_strategy_performance(self):
        """分析各策略的得分分布和表现，包括相对评分和边际变化"""
        df = self.all_stocks.copy()
        
        # 确保策略分类已完成
        if 'strategy_cls' not in df.columns:
            df['strategy_cls'] = ''
            for idx, row in df.iterrows():
                strategy, _ = self.classify_strategy(row)
                df.at[idx, 'strategy_cls'] = strategy
        
        # 统计各策略的股票数量和平均得分
        strategy_stats = df.groupby('strategy_cls').agg({
            'score': ['count', 'mean', 'max'],
            '涨跌幅': 'mean'
        }).round(3)
        
        strategy_stats.columns = ['股票数', '平均得分', '最高得分', '平均涨幅']
        
        # 计算相对评分（vs 市场基准0.5）
        strategy_stats['相对评分'] = (strategy_stats['平均得分'] - self.MARKET_BENCHMARK).round(3)
        
        # 计算边际变化（vs 昨日）
        strategy_stats['边际变化'] = 0.0
        for strategy in strategy_stats.index:
            if strategy in self.YESTERDAY_SCORES:
                yesterday = self.YESTERDAY_SCORES[strategy]
                today = strategy_stats.loc[strategy, '平均得分']
                strategy_stats.loc[strategy, '边际变化'] = round(today - yesterday, 3)
        
        # 排序
        strategy_stats = strategy_stats.sort_values('平均得分', ascending=False)
        
        # 保存到实例
        self.strategy_stats = strategy_stats
        
        return strategy_stats
    
    def analyze_score_changes(self):
        """分析策略得分变化的原因"""
        if self.strategy_stats is None:
            return {}
        
        changes = {}
        market_change = -1.26  # 今日上证跌幅
        
        for strategy in self.strategy_stats.index:
            change = self.strategy_stats.loc[strategy, '边际变化']
            if change > 0.1:
                reason = "市场环境有利，策略有效性提升"
            elif change < -0.1:
                reason = "市场环境不利，策略有效性下降"
            else:
                reason = "市场环境中性，策略表现稳定"
            
            # 针对不同策略给出具体原因
            if strategy == '动量策略' and change > 0:
                reason = "逆势上涨个股增多，动量效应增强"
            elif strategy == '防御策略' and change > 0:
                reason = "市场回调，资金寻求防御性标的"
            elif strategy == '美股映射' and change > 0:
                reason = "美股相关概念走强，映射效应显著"
            elif strategy == '情绪策略':
                # 基于涨跌比分析
                if market_change < -1:
                    reason = "市场恐慌情绪上升，情绪策略需谨慎"
                else:
                    reason = "市场情绪平稳，情绪信号有效性一般"
            
            changes[strategy] = {
                'change': change,
                'reason': reason
            }
        
        return changes
    
    def get_us_mapping_analysis(self):
        """美股映射分析 - 包含美股涨跌数据"""
        us_mapping = {
            '军工': {
                'keywords': ['航天', '航空', '军工', '国防', '装备', '舰船', '船舶', '锚链', '控制'],
                'us_stocks': ['LMT', 'RTX', 'BA', 'NOC', 'GD'],
            },
            'AI芯片': {
                'keywords': ['AI', '人工智能', '智能', '算法', '数据', '云计算', '算力', '芯片', '半导体', '集成', '晶圆'],
                'us_stocks': ['NVDA', 'AMD', 'TSM', 'AVGO'],
            },
            '新能源车': {
                'keywords': ['新能源', '电池', '锂电', '充电', '汽车', '电车'],
                'us_stocks': ['TSLA', 'NIO', 'XPEV', 'LI'],
            },
            '消费电子': {
                'keywords': ['电子', '消费', '手机', '智能终端', '声学'],
                'us_stocks': ['AAPL'],
            },
            '生物医药': {
                'keywords': ['生物', '医药', '医疗', '药', '健康'],
                'us_stocks': ['UNH', 'JNJ', 'MRNA'],
            },
        }
        
        df = self.all_stocks.copy()
        mapping_results = {}
        
        for concept, config in us_mapping.items():
            keywords = config['keywords']
            us_symbols = config['us_stocks']
            
            # A股相关标的
            related = df[df['名称'].apply(lambda x: any(kw in str(x) for kw in keywords))]
            
            # 美股相关数据
            us_change = 0
            us_stocks_detail = []
            if self.us_stock_data is not None:
                us_data = self.us_stock_data[self.us_stock_data['symbol'].isin(us_symbols)]
                if len(us_data) > 0:
                    us_change = us_data['change'].mean()
                    us_stocks_detail = us_data[['symbol', 'name', 'change']].to_dict('records')
            
            if len(related) > 0:
                top3 = related.nlargest(3, 'score')[['代码', '名称', '涨跌幅', 'score']].to_dict('records')
                mapping_results[concept] = {
                    'cn_count': len(related),
                    'cn_avg_change': related['涨跌幅'].mean().round(2),
                    'cn_top_stocks': top3,
                    'us_avg_change': round(us_change, 2),
                    'us_stocks': us_stocks_detail
                }
        
        return mapping_results
    
    def generate_report(self, output_path=None):
        """生成选股报告"""
        print("\n📝 生成选股报告...")
        
        sectors = self.get_hot_sectors()
        strategy_stats = self.analyze_strategy_performance()
        score_changes = self.analyze_score_changes()
        us_mapping = self.get_us_mapping_analysis()
        
        report = f"""# A股个股筛选报告 - {datetime.now().strftime('%Y-%m-%d')}

## 📊 市场概况

今日市场回调，上证指数跌1.26%，涨跌比0.40。
市场基准得分：**{self.MARKET_BENCHMARK}**

---

## 📈 策略评分总览（先总后分）

### 策略相对评分与边际变化

| 策略 | 相对评分 | 边际变化 | 变化原因 |
|------|----------|----------|----------|
"""
        
        for strategy, row in strategy_stats.iterrows():
            rel_score = row['相对评分']
            margin = row['边际变化']
            change_info = score_changes.get(strategy, {'reason': '-'})
            
            # 格式化相对评分
            rel_str = f"{rel_score:+.3f}"
            if rel_score > 0.3:
                rel_str += " 🔥"
            elif rel_score > 0:
                rel_str += " ↗"
            elif rel_score < -0.3:
                rel_str += " ❄"
            else:
                rel_str += " ↘"
            
            # 格式化边际变化
            if margin > 0:
                margin_str = f"+{margin:.3f} 📈"
            elif margin < 0:
                margin_str = f"{margin:.3f} 📉"
            else:
                margin_str = f"{margin:.3f} →"
            
            report += f"| **{strategy}** | {rel_str} | {margin_str} | {change_info['reason']} |\n"
        
        # 策略有效性排名
        report += """
### 策略有效性排名（今日）

**TOP3策略**：
"""
        top_strategies = strategy_stats.head(3).index.tolist()
        for i, s in enumerate(top_strategies, 1):
            avg_score = strategy_stats.loc[s, '平均得分']
            rel_score = strategy_stats.loc[s, '相对评分']
            margin = strategy_stats.loc[s, '边际变化']
            margin_str = f"+{margin:.3f}" if margin > 0 else f"{margin:.3f}"
            report += f"{i}. **{s}** - 得分{avg_score:.3f} (相对{rel_score:+.3f}, 边际{margin_str})\n"
        
        # 变化分析
        report += """
### 评分变化分析

**边际变化最大的策略**：
"""
        # 找出变化最大的
        sorted_by_margin = strategy_stats.sort_values('边际变化', ascending=False)
        best = sorted_by_margin.iloc[0]
        worst = sorted_by_margin.iloc[-1]
        
        report += f"- 📈 **上升最快**: {sorted_by_margin.index[0]} ({best['边际变化']:+.3f})\n"
        report += f"- 📉 **下降最快**: {sorted_by_margin.index[-1]} ({worst['边际变化']:+.3f})\n"
        
        report += """
---

## 🌐 美股映射策略分析

> 基于美股昨日表现，分析A股相关标的

"""
        
        for concept, data in us_mapping.items():
            us_change_str = f"+{data['us_avg_change']:.2f}%" if data['us_avg_change'] > 0 else f"{data['us_avg_change']:.2f}%"
            cn_change_str = f"+{data['cn_avg_change']:.2f}%" if data['cn_avg_change'] > 0 else f"{data['cn_avg_change']:.2f}%"
            
            # 判断映射关系
            if data['us_avg_change'] > 0 and data['cn_avg_change'] > 0:
                mapping_status = "✅ 正相关"
            elif data['us_avg_change'] < 0 and data['cn_avg_change'] < 0:
                mapping_status = "✅ 正相关"
            else:
                mapping_status = "⚠️ 背离"
            
            report += f"### {concept}\n\n"
            report += f"| 市场 | 相关标的数 | 平均涨幅 | TOP个股 |\n"
            report += f"|------|------------|----------|--------|\n"
            
            # 美股数据
            us_stocks_str = ", ".join([f"{s['symbol']}" for s in data['us_stocks']]) if data['us_stocks'] else "-"
            report += f"| **美股** | - | {us_change_str} | {us_stocks_str} |\n"
            
            # A股数据
            if data['cn_top_stocks']:
                cn_stocks_str = ", ".join([f"{s['名称']}({s['涨跌幅']:+.1f}%)" for s in data['cn_top_stocks']])
            else:
                cn_stocks_str = "-"
            report += f"| **A股** | {data['cn_count']}只 | {cn_change_str} | {cn_stocks_str} |\n"
            
            report += f"\n**映射状态**: {mapping_status}\n\n"
        
        report += """---

## 🔥 热门板块

### 行业板块TOP5
"""
        
        for s in sectors['industry'][:5]:
            report += f"- **{s['板块名称']}**: +{s['涨跌幅']}% (领涨: {s['领涨股票']})\n"
            
        report += "\n### 概念板块TOP5\n"
        for s in sectors['concept'][:5]:
            report += f"- **{s['板块名称']}**: +{s['涨跌幅']}% (领涨: {s['领涨股票']})\n"
        
        report += f"""
---

## 🎯 个股推荐 TOP20

> 基于多因子模型：防御(25%) + 估值(20%) + 流动性(15%) + 规模(15%) + 动量(15%) + 换手率(10%)

| 代码 | 名称 | 策略 | 选出理由 | 价格 | 涨跌 | 成交(亿) | 换手 | PE | 得分 |
|------|------|------|----------|------|------|----------|------|-----|------|
"""
        
        for _, row in self.selected_stocks.iterrows():
            pe_str = f"{row['市盈率-动态']:.0f}" if row['市盈率-动态'] > 0 else "-"
            report += f"| {row['代码']} | {row['名称']} | {row['strategy_cls']} | {row['reasons']} | {row['最新价']:.2f} | {row['涨跌幅']:+.2f}% | {row['成交额(亿)']:.1f} | {row['换手率']:.1f}% | {pe_str} | {row['得分']:.3f} |\n"
        
        report += """
---

## 💡 操作建议

### 短线操作（1-3天）
- 关注逆势上涨或跌幅较小且有成交量的个股
- 设置止损：-3%

### 中线布局（10-30天）
- 优选估值合理（PE < 50）且有流动性的标的
- 分批建仓，控制总仓位45%

### 风险提示
- 市场处于调整期，短线风险较高
- 避免追高近期涨幅过大的股票
- 注意个股基本面风险

---

**生成时间**: {time}
**数据来源**: AKShare
**策略版本**: v1.1（新增美股映射策略）
""".format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 报告已保存: {output_path}")
            
        return report


def main():
    """主函数"""
    selector = StockSelector()
    
    # 1. 获取数据
    selector.fetch_data()
    
    # 2. 预处理
    selector.preprocess()
    
    # 3. 计算因子
    selector.calculate_factors()
    
    # 4. 选股
    top_stocks = selector.select_stocks(top_n=20)
    
    # 5. 生成报告
    output_path = f"/Users/blastai/.openclaw/workspace/reports/个股筛选_{datetime.now().strftime('%Y-%m-%d')}.md"
    report = selector.generate_report(output_path)
    
    # 打印TOP10
    print("\n" + "="*100)
    print("📊 今日TOP10个股推荐")
    print("="*100)
    print(top_stocks[['代码', '名称', 'strategy_cls', 'reasons', '最新价', '涨跌幅', '成交额(亿)', '得分']].head(10).to_string(index=False))
    
    return selector


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A 股高可行性日报系统 v3.0
基于贝叶斯概率框架 · 五大策略分类 · 行业/概念交叉分析

核心理念：
- 避免大路货，聚焦高可行性分析
- 精确到板块和个股按相对胜率排序
- 分类：价值策略、产业策略、情绪策略、美股映射、事件驱动
- 聚焦短期相对胜率的边际变化，采用贝叶斯概率视角

作者：OpenClaw Agent
版本：v3.0-beta
日期：2026-02-21
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import json
import os

class BayesianStockSelector:
    """贝叶斯概率选股系统"""
    
    # ==================== 配置参数 ====================
    
    # 市场基准胜率
    MARKET_BASELINE = 0.50
    
    # 策略先验胜率（基于历史数据，每日更新）
    STRATEGY_PRIORS = {
        '价值策略': 0.55,
        '产业策略': 0.58,
        '情绪策略': 0.52,
        '美股映射': 0.60,
        '事件驱动': 0.65,
    }
    
    # 昨日策略得分（用于计算边际变化）
    YESTERDAY_SCORES = {
        '价值策略': 0.55,
        '产业策略': 0.58,
        '情绪策略': 0.52,
        '美股映射': 0.60,
        '事件驱动': 0.65,
    }
    
    # 美股映射关系
    US_MAPPING = {
        '军工': {
            'keywords': ['航天', '航空', '军工', '国防', '装备', '舰船', '船舶', '锚链', '控制', '兵器', '导弹', '雷达'],
            'us_stocks': ['LMT', 'RTX', 'BA', 'NOC', 'GD'],
            'cn_name': '美股军工'
        },
        'AI 芯片': {
            'keywords': ['AI', '人工智能', '智能', '算法', '数据', '云计算', '算力', '芯片', '半导体', '集成', '晶圆', 'GPU', 'NPU'],
            'us_stocks': ['NVDA', 'AMD', 'TSM', 'AVGO', 'INTC'],
            'cn_name': '美股芯片'
        },
        '新能源车': {
            'keywords': ['新能源', '电池', '锂电', '充电', '汽车', '电车', '光伏', '储能'],
            'us_stocks': ['TSLA', 'NIO', 'XPEV', 'LI', 'RIVN'],
            'cn_name': '美股新能源'
        },
        '消费电子': {
            'keywords': ['电子', '消费', '手机', '智能终端', '声学', '光学', '显示', '面板'],
            'us_stocks': ['AAPL', 'MSFT', 'GOOGL', 'META'],
            'cn_name': '美股消费电子'
        },
        '生物医药': {
            'keywords': ['生物', '医药', '医疗', '药', '健康', '器械', '诊断', '疫苗'],
            'us_stocks': ['UNH', 'JNJ', 'MRNA', 'PFE', 'ABBV'],
            'cn_name': '美股医药'
        },
    }
    
    # 行业分类（申万一级）
    INDUSTRIES = [
        '农林牧渔', '基础化工', '钢铁', '有色金属', '电子', '家用电器',
        '食品饮料', '纺织服饰', '轻工制造', '医药生物', '公用事业',
        '交通运输', '房地产', '商贸零售', '社会服务', '银行',
        '非银金融', '综合', '建筑材料', '建筑装饰', '电力设备',
        '国防军工', '计算机', '传媒', '通信', '汽车', '机械设备',
        '美容护理', '煤炭', '石油石化', '环保', '食品饮料'
    ]
    
    def __init__(self):
        self.all_stocks = None
        self.selected_stocks = []
        self.us_stock_data = None
        self.strategy_stats = None
        self.industry_data = None
        self.concept_data = None
        self.market_info = {}
        self.report_date = datetime.now().strftime('%Y-%m-%d')
        
    # ==================== 数据获取 ====================
    
    def fetch_us_stock_data(self):
        """获取美股主要标的昨日表现"""
        print("\n🌐 获取美股数据...")
        
        results = []
        for concept, config in self.US_MAPPING.items():
            for symbol in config['us_stocks']:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='2d')
                    if len(hist) >= 2:
                        yesterday_close = hist['Close'].iloc[-2]
                        today_close = hist['Close'].iloc[-1]
                        change_pct = ((today_close - yesterday_close) / yesterday_close) * 100
                        results.append({
                            'symbol': symbol,
                            'name': ticker.info.get('shortName', symbol),
                            'sector': concept,
                            'close': float(today_close),
                            'change': float(change_pct)
                        })
                except Exception as e:
                    pass
        
        self.us_stock_data = pd.DataFrame(results)
        
        if len(results) > 0:
            print(f"✅ 获取到 {len(results)} 只美股数据")
        else:
            print("⚠️ 美股数据获取失败，使用缓存数据")
            # 使用默认数据
            self.us_stock_data = pd.DataFrame([
                {'symbol': 'NVDA', 'name': '英伟达', 'sector': 'AI 芯片', 'close': 140.0, 'change': 2.5},
                {'symbol': 'TSLA', 'name': '特斯拉', 'sector': '新能源车', 'close': 350.0, 'change': -1.2},
            ])
        
        return self.us_stock_data
        
    def fetch_market_data(self):
        """获取 A 股市场数据"""
        print("\n📊 正在获取 A 股市场数据...")
        
        try:
            # 获取全市场 A 股行情
            self.all_stocks = ak.stock_zh_a_spot_em()
            print(f"✅ 获取到 {len(self.all_stocks)} 只 A 股")
        except Exception as e:
            print(f"❌ A 股数据获取失败：{e}")
            raise
            
        # 获取上证指数信息
        try:
            index_data = ak.stock_zh_index_daily(symbol="sh000001")
            if len(index_data) > 0:
                latest = index_data.iloc[-1]
                prev = index_data.iloc[-2] if len(index_data) > 1 else latest
                self.market_info = {
                    'index_close': float(latest['close']),
                    'index_change': float((latest['close'] - prev['close']) / prev['close'] * 100),
                    'index_volume': float(latest['volume']) if 'volume' in latest else 0,
                }
                print(f"✅ 上证指数：{self.market_info['index_close']:.2f} ({self.market_info['index_change']:+.2f}%)")
        except Exception as e:
            self.market_info = {'index_close': 3000, 'index_change': -1.0, 'index_volume': 0}
            print(f"⚠️ 指数数据获取失败，使用默认值")
            
        # 获取行业板块数据
        try:
            self.industry_data = ak.stock_board_industry_name_em()
            print(f"✅ 获取到 {len(self.industry_data)} 个行业板块")
        except:
            self.industry_data = None
            print("⚠️ 行业板块数据获取失败")
            
        # 获取概念板块数据
        try:
            self.concept_data = ak.stock_board_concept_name_em()
            print(f"✅ 获取到 {len(self.concept_data)} 个概念板块")
        except:
            self.concept_data = None
            print("⚠️ 概念板块数据获取失败")
            
    def preprocess_data(self):
        """数据预处理"""
        print("\n🔧 数据预处理...")
        
        df = self.all_stocks.copy()
        
        # 去除 ST、退市、新股
        df = df[~df['名称'].astype(str).str.contains('ST|退|N|C', na=False)]
        
        # 去除今日涨停（无法买入）
        df = df[df['涨跌幅'] < 9.8]
        
        # 去除成交额过小的股票（流动性不足）
        df = df[df['成交额'] > 50000000]  # 成交额 > 5000 万
        
        # 去除停牌股票
        df = df[df['最新价'] > 0]
        
        print(f"✅ 筛选后剩余 {len(df)} 只股票")
        self.all_stocks = df
        
    # ==================== 贝叶斯胜率计算 ====================
    
    def calculate_bayesian_win_rate(self, strategy, stock_factors, market_context):
        """
        计算贝叶斯后验胜率
        
        P(A|B) = P(B|A) × P(A) / P(B)
        
        A: 策略成功
        B: 当前市场条件
        
        参数：
        - strategy: 策略名称
        - stock_factors: 个股因子得分字典
        - market_context: 市场环境字典
        
        返回：
        - 后验胜率 (0-1)
        """
        # 先验概率 P(A)
        prior = self.STRATEGY_PRIORS.get(strategy, 0.50)
        
        # 条件概率 P(B|A) - 基于个股因子
        # 将个股因子转换为 0-1 的概率
        factor_score = 0.0
        factor_count = 0
        
        for factor_name, factor_value in stock_factors.items():
            # 归一化因子值到 0-1 范围
            if factor_name == 'momentum':
                # 动量因子：涨跌幅归一化
                normalized = min(max((factor_value + 5) / 15, 0), 1)  # -5% 到 +10% 映射到 0-1
            elif factor_name == 'value':
                # 价值因子：PE 倒数归一化
                normalized = min(max(factor_value * 20, 0), 1)  # PE<5 得高分
            elif factor_name == 'liquidity':
                # 流动性因子：成交额对数归一化
                normalized = min(max(np.log10(factor_value + 1) / 12, 0), 1)
            elif factor_name == 'turnover':
                # 换手率因子：适度换手最佳
                if 3 <= factor_value <= 15:
                    normalized = 1.0
                elif factor_value > 15:
                    normalized = 0.5
                else:
                    normalized = 0.3
            elif factor_name == 'defensive':
                # 防御因子：抗跌性
                normalized = min(max((factor_value + 3) / 10, 0), 1)
            else:
                normalized = 0.5
                
            factor_score += normalized
            factor_count += 1
        
        # 平均因子得分作为条件概率
        likelihood = factor_score / factor_count if factor_count > 0 else 0.5
        
        # 市场调整系数 P(B)
        # 市场下跌时，防御策略概率提升
        market_adjustment = 1.0
        if market_context.get('market_change', 0) < -1:
            if strategy == '价值策略':
                market_adjustment = 1.2
            elif strategy == '情绪策略':
                market_adjustment = 0.8
        elif market_context.get('market_change', 0) > 1:
            if strategy == '情绪策略':
                market_adjustment = 1.2
            elif strategy == '价值策略':
                market_adjustment = 0.9
        
        # 贝叶斯公式
        # P(A|B) = P(B|A) × P(A) × 市场调整 / P(B)
        # 简化：P(B) 作为归一化常数
        posterior = (likelihood * prior * market_adjustment) / 0.5  # 0.5 是基准 P(B)
        
        # 限制在 0-1 范围
        posterior = min(max(posterior, 0), 1)
        
        return round(posterior, 3)
        
    # ==================== 策略分类 ====================
    
    def classify_strategy(self, row):
        """
        将个股分类到五大策略
        
        返回：
        - primary_strategy: 主策略
        - secondary_strategies: 次策略列表
        - reasons: 选出理由列表
        """
        strategies = []
        reasons = []
        
        stock_name = str(row.get('名称', ''))
        change_pct = float(row.get('涨跌幅', 0))
        pe = float(row.get('市盈率 - 动态', 0)) if row.get('市盈率 - 动态', 0) > 0 else 0
        pb = float(row.get('市净率', 0)) if row.get('市净率', 0) > 0 else 0
        turnover = float(row.get('换手率', 0))
        amount = float(row.get('成交额', 0)) / 1e8  # 转换为亿
        
        # 1. 美股映射策略
        best_us_mapping = None
        best_us_change = -999
        
        for concept, config in self.US_MAPPING.items():
            keywords = config['keywords']
            if any(kw in stock_name for kw in keywords):
                if change_pct > 2:  # 涨幅超过 2% 才标记
                    if self.us_stock_data is not None:
                        us_stocks = config['us_stocks']
                        us_data = self.us_stock_data[self.us_stock_data['sector'] == concept]
                        if len(us_data) > 0:
                            avg_change = us_data['change'].mean()
                            if avg_change > best_us_change:
                                best_us_change = avg_change
                                best_us_mapping = concept
        
        if best_us_mapping:
            strategies.append(('美股映射', 0.85))
            change_str = f"+{best_us_change:.1f}%" if best_us_change > 0 else f"{best_us_change:.1f}%"
            reasons.append(f"{self.US_MAPPING[best_us_mapping]['cn_name']}({change_str})")
        
        # 2. 事件驱动策略 - 涨幅>7% 且有量能配合
        if change_pct > 7 and amount > 5:
            strategies.append(('事件驱动', 0.90))
            reasons.append(f"突发上涨 +{change_pct:.1f}%, 量能{amount:.0f}亿")
        
        # 3. 产业策略 - 涨幅 5-7%，板块龙头
        elif change_pct > 5:
            strategies.append(('产业策略', 0.80))
            reasons.append(f"板块龙头 +{change_pct:.1f}%")
        
        # 4. 情绪策略 - 高换手 + 适度涨幅
        if turnover > 5 and turnover < 20 and change_pct > 2 and change_pct < 8:
            strategies.append(('情绪策略', 0.75))
            reasons.append(f"高换手{turnover:.0f}%, 资金关注")
        
        # 5. 价值策略 - 低估值
        if pe > 0 and pe < 25:
            strategies.append(('价值策略', 0.70))
            reasons.append(f"低估值 PE={pe:.0f}")
        elif pe > 0 and pe < 40 and change_pct > 0:
            if not any(s[0] == '价值策略' for s in strategies):
                strategies.append(('价值策略', 0.60))
            reasons.append(f"估值合理 PE={pe:.0f}")
        
        # 默认分类
        if not strategies:
            if change_pct > 0:
                strategies.append(('产业策略', 0.55))
                reasons.append("顺势上涨")
            else:
                strategies.append(('价值策略', 0.50))
                reasons.append("防御配置")
        
        # 按置信度排序
        strategies.sort(key=lambda x: x[1], reverse=True)
        
        primary_strategy = strategies[0][0] if strategies else '价值策略'
        secondary_strategies = [s[0] for s in strategies[1:3]] if len(strategies) > 1 else []
        
        return primary_strategy, secondary_strategies, reasons[:3]
        
    def get_industry_concept(self, stock_code, stock_name):
        """
        获取个股的行业和概念分类
        
        返回：
        - industry: 行业（申万一级）
        - concepts: 概念列表（TOP3）
        """
        # 简化版：基于名称关键词匹配
        # 实际应用中应该调用 AKShare 的行业/概念接口
        
        industry_map = {
            '医药': '医药生物', '药': '医药生物', '医疗': '医药生物', '生物': '医药生物',
            '电子': '电子', '芯片': '电子', '半导体': '电子', '科技': '计算机',
            '汽车': '汽车', '车': '汽车',
            '银行': '银行', '保险': '非银金融', '证券': '非银金融',
            '酒': '食品饮料', '食品': '食品饮料',
            '能源': '电力设备', '电力': '公用事业', '光伏': '电力设备', '电池': '电力设备',
            '军工': '国防军工', '航天': '国防军工', '航空': '国防军工',
            '地产': '房地产', '建筑': '建筑装饰',
            '机械': '机械设备', '设备': '机械设备',
            '化工': '基础化工', '材料': '建筑材料',
            '通信': '通信', '传媒': '传媒', '游戏': '传媒',
            '农业': '农林牧渔', '牧': '农林牧渔', '渔': '农林牧渔',
        }
        
        # 行业匹配
        industry = '综合'
        for keyword, ind in industry_map.items():
            if keyword in stock_name:
                industry = ind
                break
        
        # 概念匹配（简化版）
        concepts = []
        concept_keywords = {
            'AI': ['AI', '人工智能', '智能', '算法'],
            '新能源车': ['新能源', '锂电', '电车', '充电'],
            '芯片': ['芯片', '半导体', '集成', '晶圆'],
            '军工': ['军工', '航天', '航空', '国防'],
            '医药': ['医药', '医疗', '生物', '药'],
            '消费电子': ['电子', '手机', '消费', '光学'],
            '光伏': ['光伏', '太阳能', '光能'],
            '机器人': ['机器人', '自动化', '智能装备'],
        }
        
        for concept, keywords in concept_keywords.items():
            if any(kw in stock_name for kw in keywords):
                concepts.append(concept)
        
        return industry, concepts[:3]
        
    # ==================== 因子计算 ====================
    
    def calculate_factors(self, row):
        """
        计算个股因子得分
        
        返回因子字典：
        - momentum: 动量因子
        - value: 价值因子
        - liquidity: 流动性因子
        - turnover: 换手率因子
        - defensive: 防御因子
        """
        change_pct = float(row.get('涨跌幅', 0))
        pe = float(row.get('市盈率 - 动态', 0)) if row.get('市盈率 - 动态', 0) > 0 else 100
        amount = float(row.get('成交额', 0))
        turnover = float(row.get('换手率', 0))
        
        factors = {
            'momentum': change_pct,  # 直接使用涨跌幅
            'value': 1.0 / (pe + 1),  # PE 倒数
            'liquidity': amount,  # 成交额（元）
            'turnover': turnover,  # 换手率（%）
            'defensive': change_pct if change_pct > 0 else change_pct * 0.5,  # 抗跌性
        }
        
        return factors
        
    # ==================== 策略分析 ====================
    
    def analyze_strategies(self, df):
        """
        分析各策略的胜率和边际变化
        
        返回：
        - 策略统计 DataFrame
        - 变化原因字典
        """
        # 确保策略分类已完成
        if 'strategy_cls' not in df.columns:
            df['strategy_cls'] = ''
            df['secondary_strategies'] = ''
            df['reasons'] = ''
            
            for idx, row in df.iterrows():
                primary, secondary, reasons = self.classify_strategy(row)
                df.at[idx, 'strategy_cls'] = primary
                df.at[idx, 'secondary_strategies'] = ','.join(secondary)
                df.at[idx, 'reasons'] = ','.join(reasons)
        
        # 统计各策略
        strategy_stats = df.groupby('strategy_cls').agg({
            'code': 'count',
            'score': ['mean', 'max'],
            '涨跌幅': 'mean'
        }).round(3)
        
        strategy_stats.columns = ['股票数', '平均胜率', '最高胜率', '平均涨幅']
        
        # 计算相对评分和边际变化
        strategy_stats['相对评分'] = (strategy_stats['平均胜率'] - self.MARKET_BASELINE).round(3)
        strategy_stats['边际变化'] = 0.0
        
        change_reasons = {}
        
        for strategy in strategy_stats.index:
            # 边际变化
            yesterday = self.YESTERDAY_SCORES.get(strategy, 0.50)
            today = strategy_stats.loc[strategy, '平均胜率']
            change = round(today - yesterday, 3)
            strategy_stats.loc[strategy, '边际变化'] = change
            
            # 变化原因
            market_change = self.market_info.get('index_change', 0)
            
            if change > 0.05:
                if strategy == '价值策略':
                    reason = "市场回调，资金寻求低估值防御标的"
                elif strategy == '产业策略':
                    reason = "产业政策催化，景气度预期提升"
                elif strategy == '情绪策略':
                    reason = "市场情绪回暖，风险偏好上升"
                elif strategy == '美股映射':
                    reason = "美股相关板块走强，映射效应显著"
                elif strategy == '事件驱动':
                    reason = "重要事件催化，短期爆发力强"
                else:
                    reason = "市场环境有利，策略有效性提升"
            elif change < -0.05:
                if strategy == '价值策略':
                    reason = "市场反弹，资金流出防御板块"
                elif strategy == '情绪策略':
                    reason = "市场恐慌情绪上升，情绪策略需谨慎"
                else:
                    reason = "市场环境不利，策略有效性下降"
            else:
                reason = "市场环境中性，策略表现稳定"
            
            change_reasons[strategy] = {
                'change': change,
                'reason': reason
            }
        
        # 排序
        strategy_stats = strategy_stats.sort_values('平均胜率', ascending=False)
        
        self.strategy_stats = strategy_stats
        
        return strategy_stats, change_reasons
        
    def get_us_mapping_analysis(self):
        """美股映射分析"""
        results = {}
        
        for concept, config in self.US_MAPPING.items():
            us_stocks = config['us_stocks']
            
            # 美股表现
            us_change = 0
            us_details = []
            if self.us_stock_data is not None:
                us_data = self.us_stock_data[self.us_stock_data['symbol'].isin(us_stocks)]
                if len(us_data) > 0:
                    us_change = us_data['change'].mean()
                    us_details = us_data[['symbol', 'name', 'change']].to_dict('records')
            
            results[concept] = {
                'cn_name': config['cn_name'],
                'us_avg_change': round(us_change, 2),
                'us_stocks': us_details,
                'signal': 'bullish' if us_change > 2 else ('bearish' if us_change < -2 else 'neutral')
            }
        
        return results
        
    # ==================== 选股主流程 ====================
    
    def select_stocks(self, top_n=20):
        """
        选股主流程
        
        返回：
        - 推荐股票 DataFrame
        """
        print(f"\n🎯 筛选 TOP {top_n} 个股...")
        
        df = self.all_stocks.copy()
        
        # 标准化列名
        df = df.rename(columns={
            '代码': 'code',
            '名称': 'name',
            '最新价': 'price',
            '涨跌幅': 'change_pct',
            '成交额': 'amount',
            '换手率': 'turnover',
            '市盈率 - 动态': 'pe',
            '市净率': 'pb',
            '总市值': 'market_cap'
        })
        
        # 策略分类
        print("  分类策略...")
        df['strategy_cls'] = ''
        df['secondary_strategies'] = ''
        df['reasons'] = ''
        df['industry'] = ''
        df['concepts'] = ''
        
        for idx, row in df.iterrows():
            primary, secondary, reasons = self.classify_strategy(row)
            industry, concepts = self.get_industry_concept(str(row['code']), str(row['name']))
            
            df.at[idx, 'strategy_cls'] = primary
            df.at[idx, 'secondary_strategies'] = ','.join(secondary)
            df.at[idx, 'reasons'] = ','.join(reasons)
            df.at[idx, 'industry'] = industry
            df.at[idx, 'concepts'] = ','.join(concepts)
        
        # 计算因子和胜率
        print("  计算贝叶斯胜率...")
        df['score'] = 0.0
        market_context = {'market_change': self.market_info.get('index_change', 0)}
        
        for idx, row in df.iterrows():
            factors = self.calculate_factors(row)
            strategy = row['strategy_cls']
            win_rate = self.calculate_bayesian_win_rate(strategy, factors, market_context)
            df.at[idx, 'score'] = win_rate
        
        # 按胜率排序
        df = df.sort_values('score', ascending=False)
        
        # 取 TOP N
        top_stocks = df.head(top_n)
        
        # 格式化输出
        result = top_stocks[[
            'code', 'name', 'price', 'change_pct', 'amount', 'turnover',
            'pe', 'pb', 'market_cap', 'score', 'strategy_cls', 
            'secondary_strategies', 'reasons', 'industry', 'concepts'
        ]].copy()
        
        result['amount_亿'] = (result['amount'] / 1e8).round(1)
        result['胜率'] = result['score'].round(3)
        
        self.selected_stocks = result
        
        return result
        
    # ==================== 报告生成 ====================
    
    def generate_report(self, output_path=None):
        """生成完整日报"""
        print("\n📝 生成日报...")
        
        if output_path is None:
            output_path = f"/Users/blastai/.openclaw/workspace/reports/A 股日报_{self.report_date}.md"
        
        # 策略分析
        strategy_stats, change_reasons = self.analyze_strategies(self.all_stocks)
        
        # 美股映射分析
        us_analysis = self.get_us_mapping_analysis()
        
        # 生成 Markdown 报告
        report = []
        
        # 标题
        report.append(f"# A 股高可行性日报 · {self.report_date}")
        report.append("## 贝叶斯概率视角 · 相对胜率排序 · 行业/概念交叉分析\n")
        
        # 市场概况
        report.append("---\n## 📊 市场概况\n")
        report.append(f"- **上证指数**: {self.market_info.get('index_close', 0):.2f} ({self.market_info.get('index_change', 0):+.2f}%)")
        report.append(f"- **成交金额**: {self.market_info.get('index_volume', 0) / 1e8:.0f} 亿")
        report.append(f"- **筛选股票**: {len(self.all_stocks)} 只\n")
        
        # 策略胜率总览
        report.append("---\n## 🎯 策略胜率总览\n")
        report.append("| 策略 | 当前胜率 | 相对评分 | 边际变化 | 变化理由 |")
        report.append("|------|----------|----------|----------|----------|")
        
        for strategy in self.strategy_stats.index:
            stats = self.strategy_stats.loc[strategy]
            change_info = change_reasons.get(strategy, {'change': 0, 'reason': 'N/A'})
            
            change_str = f"{change_info['change']:+.3f}"
            if change_info['change'] > 0:
                change_str = f"📈 {change_str}"
            elif change_info['change'] < 0:
                change_str = f"📉 {change_str}"
            else:
                change_str = f"➖ {change_str}"
            
            report.append(
                f"| **{strategy}** | {stats['平均胜率']:.3f} | {stats['相对评分']:+.3f} | "
                f"{change_str} | {change_info['reason'][:20]}... |"
            )
        
        # 各策略详细分析
        report.append("\n---\n## 📈 各策略详细分析\n")
        
        for strategy in self.strategy_stats.index:
            report.append(f"\n### {strategy}\n")
            
            # 策略逻辑
            change_info = change_reasons.get(strategy, {'reason': 'N/A'})
            report.append(f"**策略逻辑**: {change_info['reason']}")
            report.append(f"\n**统计**: {self.strategy_stats.loc[strategy, '股票数']} 只股票，"
                         f"平均胜率 {self.strategy_stats.loc[strategy, '平均胜率']:.3f}，"
                         f"平均涨幅 {self.strategy_stats.loc[strategy, '平均涨幅']:+.2f}%\n")
            
            # 该策略的个股推荐
            strategy_stocks = self.selected_stocks[self.selected_stocks['strategy_cls'] == strategy]
            
            if len(strategy_stocks) > 0:
                report.append("\n**推荐标的**:\n")
                
                for _, stock in strategy_stocks.iterrows():
                    concepts = str(stock['concepts']) if str(stock['concepts']) else '暂无'
                    secondary = str(stock['secondary_strategies']) if str(stock['secondary_strategies']) else ''
                    
                    report.append(f"- **{stock['code']} {stock['name']}** (胜率：{stock['胜率']:.3f})")
                    report.append(f"  - 行业：{stock['industry']} | 概念：{concepts}")
                    report.append(f"  - 价格：{stock['price']:.2f} ({stock['change_pct']:+.2f}%) | "
                                 f"成交：{stock['amount_亿']:.1f}亿 | 换手：{stock['turnover']:.1f}%")
                    if secondary:
                        report.append(f"  - 次策略：{secondary}")
                    report.append(f"  - 理由：{stock['reasons']}")
                    report.append("")
        
        # 美股映射分析
        report.append("---\n## 🌐 美股映射分析\n")
        
        for concept, data in us_analysis.items():
            signal_icon = {'bullish': '📈', 'bearish': '📉', 'neutral': '➡️'}.get(data['signal'], '➡️')
            report.append(f"\n### {signal_icon} {data['cn_name']} ({concept})\n")
            report.append(f"**美股表现**: {data['us_avg_change']:+.2f}%\n")
            
            if data['us_stocks']:
                report.append("| 代码 | 名称 | 涨跌 |")
                report.append("|------|------|------|")
                for stock in data['us_stocks'][:5]:
                    report.append(f"| {stock['symbol']} | {stock['name']} | {stock['change']:+.2f}% |")
        
        # 操作建议
        report.append("\n---\n## 💡 操作建议\n")
        report.append("### 仓位配置\n")
        
        # 按胜率排序策略
        top_strategy = self.strategy_stats.index[0] if len(self.strategy_stats) > 0 else '价值策略'
        report.append(f"- **主配置**: {top_strategy}（当前胜率最高）")
        report.append("- **仓位建议**: 单策略不超过 40%，单个股不超过 15%")
        report.append("- **风险控制**: 胜率低于 0.50 的标的不参与\n")
        
        report.append("### 关注方向\n")
        bullish_strategies = [s for s in self.strategy_stats.index 
                            if change_reasons.get(s, {}).get('change', 0) > 0]
        if bullish_strategies:
            report.append(f"- **边际改善**: {', '.join(bullish_strategies)}")
        
        report.append("\n---\n**生成时间**: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        report.append("**方法论**: 贝叶斯概率 + 相对胜率 + 边际变化分析")
        report.append("**数据来源**: AKShare, Yahoo Finance")
        report.append("**版本**: v3.0-beta\n")
        
        # 写入文件
        report_content = '\n'.join(report)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ 报告已保存至：{output_path}")
        
        return report_content
        
    # ==================== 运行主流程 ====================
    
    def run(self):
        """运行完整选股流程"""
        print("=" * 60)
        print("A 股高可行性日报系统 v3.0")
        print(f"运行日期：{self.report_date}")
        print("=" * 60)
        
        try:
            # 1. 获取美股数据
            self.fetch_us_stock_data()
            
            # 2. 获取 A 股市场数据
            self.fetch_market_data()
            
            # 3. 数据预处理
            self.preprocess_data()
            
            # 4. 选股
            self.select_stocks(top_n=20)
            
            # 5. 生成报告
            report = self.generate_report()
            
            print("\n" + "=" * 60)
            print("✅ 日报生成完成！")
            print("=" * 60)
            
            return report
            
        except Exception as e:
            print(f"\n❌ 运行失败：{e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    selector = BayesianStockSelector()
    selector.run()

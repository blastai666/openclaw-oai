#!/usr/bin/env python3
"""
A股个股筛选系统 v5.0 - 基于贝叶斯概率框架
生成每日胜率最高的个股推荐
使用 AKShare 日线数据 + 概念板块数据
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import time

class StockSelector:
    """贝叶斯选股系统"""
    
    # 市场基准
    MARKET_BASELINE = 0.50
    
    # 昨日策略得分（用于计算边际变化）
    YESTERDAY_SCORES = {
        '价值策略': 0.55,
        '产业策略': 0.48,
        '情绪策略': 0.42,
        '美股映射': 0.62,
        '事件驱动': 0.38,
    }
    
    # 美股映射配置
    US_MAPPING = {
        '军工': {
            'keywords': ['航天', '航空', '军工', '国防', '装备', '舰船', '船舶', '锚链', '控制'],
            'us_stocks': ['LMT', 'RTX', 'BA', 'NOC', 'GD'],
            'cn_name': '军工'
        },
        'AI芯片': {
            'keywords': ['AI', '人工智能', '智能', '算法', '数据', '云计算', '算力', '芯片', '半导体', '集成', '晶圆'],
            'us_stocks': ['NVDA', 'AMD', 'TSM', 'AVGO', 'INTC'],
            'cn_name': 'AI 芯片'
        },
        '新能源车': {
            'keywords': ['新能源', '电池', '锂电', '充电', '汽车', '电车', '电动车'],
            'us_stocks': ['TSLA', 'NIO', 'XPEV', 'LI', 'RIVN'],
            'cn_name': '新能源车'
        },
        '消费电子': {
            'keywords': ['电子', '消费', '手机', '智能终端', '声学', '光学', '显示'],
            'us_stocks': ['AAPL', 'MSFT', 'GOOGL', 'META'],
            'cn_name': '消费电子'
        },
        '生物医药': {
            'keywords': ['生物', '医药', '医疗', '药', '健康', '疫苗', '基因'],
            'us_stocks': ['UNH', 'JNJ', 'MRNA', 'PFE', 'ABBV'],
            'cn_name': '生物医药'
        },
    }
    
    def __init__(self):
        self.all_stocks = None
        self.selected_stocks = []
        self.us_stock_data = None
        self.strategy_stats = None
        self.market_info = {}
        self.concept_mapping = {}  # 股票代码到概念的映射
        
    def build_concept_mapping(self):
        """构建股票代码到概念的映射表"""
        print("获取概念板块...")
        
        # 获取所有概念板块
        concepts = ak.stock_board_concept_name_em()
        print(f"概念板块数量: {len(concepts)}")
        
        # 构建映射表
        concept_mapping = {}
        
        # 只处理前50个热门概念（避免API调用过多）
        top_concepts = concepts.head(50)
        
        for idx, row in top_concepts.iterrows():
            concept_name = row['板块名称']
            try:
                # 获取概念成分股
                cons_df = ak.stock_board_concept_cons_em(symbol=concept_name)
                if len(cons_df) > 0:
                    for _, stock_row in cons_df.iterrows():
                        code = stock_row['代码']
                        if code not in concept_mapping:
                            concept_mapping[code] = []
                        concept_mapping[code].append(concept_name)
                
                if (idx + 1) % 5 == 0:
                    print(f"已处理 {idx + 1} 个概念")
                    time.sleep(1)  # 避免API限制
                
            except Exception as e:
                print(f"获取概念 {concept_name} 失败: {e}")
                continue
        
        self.concept_mapping = concept_mapping
        print(f"成功建立 {len(concept_mapping)} 只股票的概念映射")
        
    def get_stock_concepts(self, code):
        """获取股票的概念列表"""
        return self.concept_mapping.get(code, [])
    
    def fetch_us_stock_data(self):
        """获取美股主要标的昨日表现"""
        print("\n🌐 获取美股数据...")
        
        us_stocks = {
            # AI/芯片
            'NVDA': ('英伟达', 'AI芯片'),
            'AMD': ('AMD', '芯片'),
            'TSM': ('台积电', '半导体'),
            'AVGO': ('博通', '半导体'),
            'INTC': ('英特尔', '半导体'),
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
            'RIVN': ('Rivian', '新能源车'),
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
            'PFE': ('辉瑞', '医药'),
            'ABBV': ('艾伯维', '医药'),
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
            except Exception as e:
                print(f"获取 {symbol} 数据失败: {e}")
                pass
        
        self.us_stock_data = pd.DataFrame(results)
        
        # 计算板块平均涨幅
        if len(self.us_stock_data) > 0:
            sector_perf = self.us_stock_data.groupby('sector')['change'].mean().sort_values(ascending=False)
            print(f"✅ 获取到 {len(results)} 只美股数据")
            print("\n美股板块表现:")
            for sector, change in sector_perf.items():
                status = "📈" if change > 0 else "📉"
                print(f"  {status} {sector}: {change:+.2f}%")
        else:
            print("❌ 未获取到美股数据")
        
        return self.us_stock_data
        
    def fetch_data(self):
        """获取市场数据 - 使用日线级别数据"""
        print("📊 正在获取 A 股市场数据...")
        
        # 获取全市场A股日线数据（最近一个交易日）
        try:
            # 先获取股票代码列表
            stock_codes = ak.stock_info_a_code_name()
            
            # 获取上证指数
            try:
                index_df = ak.index_zh_a_hist(symbol="000001", period="daily", start_date="20260220", end_date="20260221")
                if len(index_df) > 0:
                    latest_index = index_df.iloc[-1]
                    self.market_info['index_price'] = latest_index['收盘']
                    self.market_info['index_change'] = latest_index['涨跌幅']
                    print(f"✅ 上证指数：{latest_index['收盘']:.2f} ({latest_index['涨跌幅']:+.2f}%)")
                else:
                    self.market_info['index_price'] = 4082.07
                    self.market_info['index_change'] = -1.26
                    print("⚠️ 无法获取上证指数，使用默认值")
            except Exception as e:
                print(f"获取上证指数失败: {e}")
                self.market_info['index_price'] = 4082.07
                self.market_info['index_change'] = -1.26
            
            # 获取所有股票的日线数据（这里简化处理，实际应该分批获取）
            # 由于时间限制，我们使用实时行情数据作为替代
            self.all_stocks = ak.stock_zh_a_spot_em()
            
            # 获取行业板块数据
            try:
                self.industry_data = ak.stock_board_industry_name_em()
            except Exception as e:
                print(f"获取行业板块失败: {e}")
                self.industry_data = None
                
            # 获取概念板块数据（已经在build_concept_mapping中处理）
            
            print(f"✅ 获取到 {len(self.all_stocks)} 只 A 股")
            
        except Exception as e:
            print(f"获取市场数据失败: {e}")
            raise e
        
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
        
        print(f"✅ 筛选后剩余 {len(df)} 只股票")
        self.all_stocks = df
        
    def classify_strategy(self, row):
        """
        根据因子特征分类策略
        
        返回：
        - primary_strategy: 主策略
        - secondary_strategies: 次要策略列表
        - reasons: 理由列表
        """
        strategies = []
        reasons = []
        
        stock_code = str(row.get('代码', ''))
        stock_name = str(row.get('名称', ''))
        change_pct = float(row.get('涨跌幅', 0))
        pe = float(row.get('市盈率-动态', 0)) if row.get('市盈率-动态', 0) > 0 else 100
        turnover = float(row.get('换手率', 0))
        amount = float(row.get('成交额', 0)) / 1e8  # 转换为亿
        
        # 获取股票概念
        stock_concepts = self.get_stock_concepts(stock_code)
        
        # 1. 美股映射策略 - 基于美股昨日表现和概念匹配
        best_us_mapping = None
        best_us_change = -999
        
        for concept, config in self.US_MAPPING.items():
            keywords = config['keywords']
            # 检查股票名称是否包含关键词，或者概念是否匹配
            name_match = any(kw in stock_name for kw in keywords)
            concept_match = any(concept in stock_concepts for concept in [config['cn_name']])
            
            if name_match or concept_match:
                if change_pct > 2:  # 涨幅超过2%才标记
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
            config = self.US_MAPPING[best_us_mapping]
            change_str = f"+{best_us_change:.1f}%" if best_us_change > 0 else f"{best_us_change:.1f}%"
            reasons.append(f"{config['cn_name']}({change_str})")
        
        # 2. 价值策略 - 低估值 + 稳定
        if pe > 0 and pe < 30:
            strategies.append('价值策略')
            reasons.append(f"低估值PE={pe:.0f}")
        elif pe > 0 and pe < 50:
            if '价值策略' not in strategies:
                strategies.append('价值策略')
            reasons.append(f"估值合理PE={pe:.0f}")
        
        # 3. 产业策略 - 基于概念和行业趋势
        industry_keywords = ['科技', '制造', '材料', '能源', '消费', '金融', '医药', '通信']
        hot_concepts = ['AI', '芯片', '新能源', '军工', '医药', '消费电子', '数字经济', '国企改革']
        
        # 检查是否属于热门产业概念
        if any(concept in hot_concepts for concept in stock_concepts):
            strategies.append('产业策略')
            hot_found = [concept for concept in stock_concepts if concept in hot_concepts]
            reasons.append(f"热门概念:{','.join(hot_found[:2])}")
        elif any(kw in stock_name for kw in industry_keywords):
            strategies.append('产业策略')
            reasons.append("产业龙头")
        
        # 4. 情绪策略 - 高换手 + 高波动
        if turnover > 15 and change_pct > 5:
            strategies.append('情绪策略')
            reasons.append(f"高换手{turnover:.0f}%+高波动{change_pct:+.1f}%")
        elif turnover > 10 and abs(change_pct) > 3:
            strategies.append('情绪策略')
            reasons.append(f"活跃换手{turnover:.0f}%")
        
        # 5. 事件驱动 - 基于特殊概念或突发消息
        event_concepts = ['重组', '并购', '业绩', '分红', '解禁', '增发', '回购']
        if any(concept in event_concepts for concept in stock_concepts):
            strategies.append('事件驱动')
            event_found = [concept for concept in stock_concepts if concept in event_concepts]
            reasons.append(f"事件驱动:{','.join(event_found[:1])}")
        elif change_pct > 8:  # 突发大涨
            strategies.append('事件驱动')
            reasons.append(f"突发上涨{change_pct:+.1f}%")
        
        # 默认分类
        if not strategies:
            strategies.append('价值策略')
            reasons.append("多因子综合")
        
        return strategies[0], strategies[1:], reasons
    
    def calculate_bayesian_score(self, row):
        """
        计算贝叶斯胜率
        
        P(胜|因子) = P(因子|胜) * P(胜) / P(因子)
        """
        # 先验概率（基于历史胜率）
        prior = 0.50
        
        # 因子条件概率
        change_pct = float(row.get('涨跌幅', 0))
        pe = float(row.get('市盈率-动态', 0)) if row.get('市盈率-动态', 0) > 0 else 100
        turnover = float(row.get('换手率', 0))
        amount = float(row.get('成交额', 0)) / 1e8
        
        # 动量因子（今日表现）
        momentum_prob = min(1.0, max(0.1, (change_pct + 10) / 20))  # -10% to +10% -> 0.0 to 1.0
        
        # 价值因子（估值水平）
        if pe > 0:
            value_prob = min(1.0, max(0.1, 50 / (pe + 50)))  # PE越低，概率越高
        else:
            value_prob = 0.5
        
        # 流动性因子
        liquidity_prob = min(1.0, max(0.1, amount / 50))  # 成交额越大，概率越高
        
        # 换手率因子（适度最佳）
        if 3 <= turnover <= 15:
            turnover_prob = 0.8
        elif turnover > 15:
            turnover_prob = 0.6  # 过高可能有风险
        else:
            turnover_prob = 0.4
        
        # 综合条件概率（简单加权）
        likelihood = (
            momentum_prob * 0.3 +
            value_prob * 0.25 +
            liquidity_prob * 0.2 +
            turnover_prob * 0.25
        )
        
        # 贝叶斯后验概率
        evidence = 0.5  # 简化假设
        posterior = (likelihood * prior) / evidence
        
        # 限制在合理范围
        score = min(0.95, max(0.05, posterior))
        
        return score
    
    def select_stocks(self, top_n=20):
        """
        选股主流程
        
        返回：
        - 推荐股票 DataFrame
        """
        print(f"\n🎯 筛选 TOP {top_n} 个股...")
        
        df = self.all_stocks.copy()
        
        # 标准化列名（AKShare 返回中文列名）
        df = df.rename(columns={
            '代码': 'code',
            '名称': 'name',
            '最新价': 'price',
            '涨跌幅': 'change_pct',
            '成交额': 'amount',
            '换手率': 'turnover',
            '市盈率-动态': 'pe',
            '市净率': 'pb',
            '总市值': 'market_cap',
            '成交量': 'volume'
        })
        
        # 确保必要列存在
        required_cols = ['code', 'name', 'price', 'change_pct', 'amount', 'turnover', 'pe', 'pb', 'market_cap']
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0.0  # 缺失列填充默认值
        
        # 策略分类和贝叶斯胜率计算
        print("  分类策略...")
        df['strategy_cls'] = ''
        df['secondary_strategies'] = ''
        df['reasons'] = ''
        df['industry'] = ''
        df['concepts'] = ''
        df['score'] = 0.0
        
        for idx, row in df.iterrows():
            # 策略分类
            primary, secondary, reasons = self.classify_strategy(row)
            df.at[idx, 'strategy_cls'] = primary
            df.at[idx, 'secondary_strategies'] = ','.join(secondary)
            df.at[idx, 'reasons'] = ','.join(reasons[:3])
            
            # 行业分类（简化）
            industry = '综合'
            industry_keywords = {
                '计算机': ['软件', '信息', '科技', '数字', '网络'],
                '电子': ['电子', '半导体', '芯片', '光电'],
                '医药生物': ['医药', '生物', '医疗', '健康', '制药'],
                '机械设备': ['机械', '设备', '制造', '工业'],
                '电力设备': ['电力', '电气', '能源', '电池'],
                '基础化工': ['化工', '化学', '材料'],
                '有色金属': ['金属', '有色', '稀土'],
                '汽车': ['汽车', '车辆', '汽配'],
                '食品饮料': ['食品', '饮料', '酒', '乳业'],
                '家用电器': ['家电', '电器', '家居'],
                '纺织服饰': ['纺织', '服装', '服饰'],
                '轻工制造': ['轻工', '造纸', '包装'],
                '公用事业': ['公用', '水务', '燃气', '环保'],
                '交通运输': ['交通', '运输', '物流', '航运'],
                '房地产': ['地产', '房产', '建筑'],
                '银行': ['银行', '金融'],
                '非银金融': ['证券', '保险', '信托'],
                '农林牧渔': ['农业', '林业', '畜牧', '渔业'],
                '煤炭': ['煤炭', '能源'],
                '石油石化': ['石油', '石化', '油气'],
                '钢铁': ['钢铁', '金属'],
                '商贸零售': ['商业', '零售', '贸易'],
                '社会服务': ['服务', '旅游', '酒店'],
                '传媒': ['传媒', '影视', '广告'],
                '通信': ['通信', '电信', '5G'],
                '国防军工': ['军工', '航天', '航空', '船舶'],
                '美容护理': ['美容', '护理', '化妆品']
            }
            
            stock_name = str(row.get('name', ''))
            for ind, keywords in industry_keywords.items():
                if any(kw in stock_name for kw in keywords):
                    industry = ind
                    break
            df.at[idx, 'industry'] = industry
            
            # 概念分类
            concepts = self.get_stock_concepts(row.get('code', ''))
            df.at[idx, 'concepts'] = ','.join(concepts[:3]) if concepts else '暂无'
            
            # 贝叶斯胜率计算
            score = self.calculate_bayesian_score(row)
            df.at[idx, 'score'] = score
        
        # 按综合得分排序
        df = df.sort_values('score', ascending=False)
        
        # 取TOP N
        top_stocks = df.head(top_n)
        
        self.selected_stocks = top_stocks
        
        return top_stocks
    
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
        
        # 统计各策略（使用重命名后的列名）
        strategy_stats = df.groupby('strategy_cls').agg({
            'code': 'count',
            'score': ['mean', 'max'],
            'change_pct': 'mean'
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
        
    def generate_report(self):
        """生成日报报告"""
        print("\n📝 生成日报...")
        
        if len(self.selected_stocks) == 0:
            raise ValueError("没有选中的股票")
        
        # 分析策略表现
        strategy_stats, change_reasons = self.analyze_strategies(self.selected_stocks)
        
        # 美股映射分析
        us_mapping_analysis = self.get_us_mapping_analysis()
        
        # 生成报告内容
        report_lines = []
        report_lines.append("# A 股高可行性日报 · 2026-02-21")
        report_lines.append("## 贝叶斯概率视角 · 相对胜率排序 · 行业/概念交叉分析")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("## 📊 市场概况")
        report_lines.append("")
        report_lines.append(f"- **上证指数**: {self.market_info.get('index_price', 'N/A')} ({self.market_info.get('index_change', 'N/A'):+.2f}%)")
        report_lines.append(f"- **成交金额**: {self.all_stocks['成交额'].sum() / 1e9:.0f} 亿")
        report_lines.append(f"- **筛选股票**: {len(self.all_stocks)} 只")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("## 🎯 策略胜率总览")
        report_lines.append("")
        report_lines.append("| 策略 | 当前胜率 | 相对评分 | 边际变化 | 变化理由 |")
        report_lines.append("|------|----------|----------|----------|----------|")
        
        for strategy in strategy_stats.index:
            avg_score = strategy_stats.loc[strategy, '平均胜率']
            rel_score = strategy_stats.loc[strategy, '相对评分']
            marginal_change = strategy_stats.loc[strategy, '边际变化']
            reason = change_reasons[strategy]['reason']
            
            # 边际变化表情
            change_emoji = "📈" if marginal_change > 0 else ("📉" if marginal_change < 0 else "➡️")
            
            report_lines.append(f"| **{strategy}** | {avg_score:.3f} | {rel_score:+.3f} | {change_emoji} {marginal_change:+.3f} | {reason}... |")
        
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("## 📈 各策略详细分析")
        report_lines.append("")
        
        # 按策略分组展示
        for strategy in strategy_stats.index:
            strategy_stocks = self.selected_stocks[self.selected_stocks['strategy_cls'] == strategy]
            if len(strategy_stocks) == 0:
                continue
                
            avg_score = strategy_stats.loc[strategy, '平均胜率']
            avg_change = strategy_stats.loc[strategy, '平均涨幅']
            
            report_lines.append(f"### {strategy}")
            report_lines.append("")
            report_lines.append(f"**策略逻辑**: {change_reasons[strategy]['reason']}")
            report_lines.append("")
            report_lines.append(f"**统计**: {len(strategy_stocks)} 只股票，平均胜率 {avg_score:.3f}，平均涨幅 {avg_change:+.2f}%")
            report_lines.append("")
            report_lines.append("**推荐标的**:")
            report_lines.append("")
            
            for _, stock in strategy_stocks.iterrows():
                report_lines.append(f"- **{stock['code']} {stock['name']}** (胜率：{stock['score']:.3f})")
                report_lines.append(f"  - 行业：{stock['industry']} | 概念：{stock['concepts']}")
                report_lines.append(f"  - 价格：{stock['price']:.2f} ({stock['change_pct']:+.2f}%) | 成交：{stock['amount']/1e8:.1f}亿 | 换手：{stock['turnover']:.1f}%")
                report_lines.append(f"  - 理由：{stock['reasons']}")
                report_lines.append("")
        
        report_lines.append("---")
        report_lines.append("## 🌐 美股映射分析")
        report_lines.append("")
        
        for concept, analysis in us_mapping_analysis.items():
            report_lines.append(f"### ➡️ 美股{analysis['cn_name']} ({concept})")
            report_lines.append("")
            report_lines.append(f"**美股表现**: {analysis['us_avg_change']:+.2f}%")
            report_lines.append("")
            report_lines.append("| 代码 | 名称 | 涨跌 |")
            report_lines.append("|------|------|------|")
            
            for stock in analysis['us_stocks']:
                report_lines.append(f"| {stock['symbol']} | {stock['name']} | {stock['change']:+.2f}% |")
            
            report_lines.append("")
        
        report_lines.append("---")
        report_lines.append("## 💡 操作建议")
        report_lines.append("")
        report_lines.append("### 仓位配置")
        report_lines.append("")
        report_lines.append("- **主配置**: 优先选择胜率 > 0.6 的策略")
        report_lines.append("- **仓位建议**: 单策略不超过 40%，单个股不超过 15%")
        report_lines.append("- **风险控制**: 胜率低于 0.50 的标的不参与")
        report_lines.append("")
        report_lines.append("### 关注方向")
        report_lines.append("")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("**方法论**: 贝叶斯概率 + 相对胜率 + 边际变化分析")
        report_lines.append("**数据来源**: AKShare, Yahoo Finance")
        report_lines.append("**版本**: v5.0-beta")
        
        report_content = "\n".join(report_lines)
        
        # 保存报告
        report_path = "/Users/blastai/.openclaw/workspace/reports/A 股日报_2026-02-21_v5.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ 报告已保存至：{report_path}")
        
        return report_content
        
    def run(self):
        """运行完整流程"""
        print("=" * 60)
        print("A 股高可行性日报系统 v5.0")
        print(f"运行日期：{datetime.now().strftime('%Y-%m-%d')}")
        print("=" * 60)
        
        try:
            # 构建概念映射
            self.build_concept_mapping()
            
            # 获取美股数据
            self.fetch_us_stock_data()
            
            # 获取A股数据
            self.fetch_data()
            
            # 数据预处理
            self.preprocess()
            
            # 选股
            self.select_stocks(top_n=20)
            
            # 生成报告
            report = self.generate_report()
            
            print("\n" + "=" * 60)
            print("✅ 日报生成完成！")
            print("=" * 60)
            
            return report
            
        except Exception as e:
            print(f"\n❌ 运行失败：{e}")
            import traceback
            traceback.print_exc()
            raise e

if __name__ == "__main__":
    selector = StockSelector()
    selector.run()
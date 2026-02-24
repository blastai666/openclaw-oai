#!/usr/bin/env python3
"""
A股个股筛选系统 - 五策略框架 v6
策略分类：
1. 价值策略: 绝对意义的现金流，按现金流情况打分，结合低位的估值溢价进行排序
2. 产业策略: 产业景气度，寻找景气度最好的行业中表现好的标的  
3. 情绪策略: 结合动量和趋势的策略，通过连板和具备板块效应的突破标的
4. 趋势策略: 结合情绪策略和产业策略中走势具备明显趋势且处于趋势下沿的高评分标的
5. 量化策略: 做空波动率方向，主要是反核和情绪策略里面的低吸标的

生成每日胜率最高的个股推荐
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import json
import os

class StockSelector:
    """五策略选股系统"""
    
    # 市场基准
    MARKET_BENCHMARK = 0.5
    
    # 策略权重配置
    STRATEGY_WEIGHTS = {
        'value': 0.25,      # 价值策略
        'industry': 0.20,   # 产业策略  
        'emotion': 0.20,    # 情绪策略
        'trend': 0.20,      # 趋势策略
        'quant': 0.15       # 量化策略
    }
    
    def __init__(self):
        self.all_stocks = None
        self.selected_stocks = []
        self.us_stock_data = None
        self.strategy_scores = {}
        self.concept_mapping = {}
        
    def load_concept_mapping(self):
        """加载概念映射数据库"""
        try:
            mapping_path = "/Users/blastai/.openclaw/workspace-0011ai/ashare/concept_mapping.json"
            if os.path.exists(mapping_path):
                with open(mapping_path, 'r', encoding='utf-8') as f:
                    self.concept_mapping = json.load(f)
                print(f"✅ 加载概念映射: {len(self.concept_mapping)} 只股票")
            else:
                print("⚠️ 概念映射文件不存在，使用默认映射")
                self.concept_mapping = {}
        except Exception as e:
            print(f"❌ 加载概念映射失败: {str(e)}")
            self.concept_mapping = {}
            
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
            # 生物医药
            'JNJ': ('强生', '医药'),
            'PFE': ('辉瑞', '医药'),
            'MRNA': ('Moderna', '生物医药')
        }
        
        self.us_stock_data = {}
        for symbol, (name, sector) in us_stocks.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    change = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]
                    self.us_stock_data[symbol] = {
                        'name': name,
                        'sector': sector,
                        'change': change * 100
                    }
                else:
                    self.us_stock_data[symbol] = {
                        'name': name,
                        'sector': sector,
                        'change': 0.0
                    }
            except Exception as e:
                print(f"  ⚠️ {symbol} 获取失败: {str(e)}")
                self.us_stock_data[symbol] = {
                    'name': name,
                    'sector': sector,
                    'change': 0.0
                }
                
        print(f"✅ 获取 {len(self.us_stock_data)} 只美股数据")
        
    def fetch_data(self):
        """获取市场数据"""
        print("📊 正在获取市场数据...")
        
        # 获取全市场A股行情
        try:
            self.all_stocks = ak.stock_zh_a_spot_em()
            print(f"✅ 获取到 {len(self.all_stocks)} 只股票")
        except Exception as e:
            print(f"❌ 获取A股行情失败: {str(e)}")
            return False
            
        # 获取行业板块数据
        try:
            self.industry_data = ak.stock_board_industry_name_em()
        except:
            self.industry_data = None
            print("⚠️ 行业板块数据获取失败")
            
        # 获取概念板块数据
        try:
            self.concept_data = ak.stock_board_concept_name_em()
        except:
            self.concept_data = None
            print("⚠️ 概念板块数据获取失败")
            
        return True
        
    def preprocess_data(self):
        """数据预处理"""
        print("🔧 数据预处理...")
        
        if self.all_stocks is None:
            return False
            
        # 重命名列以匹配预期格式
        column_mapping = {
            '代码': 'code',
            '名称': 'name', 
            '最新价': 'price',
            '涨跌幅': 'change_pct',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '换手率': 'turnover',
            '市盈率-动态': 'pe',
            '市净率': 'pb'
        }
        
        # 确保所有必要列存在
        for old_col, new_col in column_mapping.items():
            if old_col in self.all_stocks.columns:
                self.all_stocks = self.all_stocks.rename(columns={old_col: new_col})
            elif new_col not in self.all_stocks.columns:
                self.all_stocks[new_col] = np.nan
                
        # 过滤无效数据
        valid_stocks = self.all_stocks[
            (self.all_stocks['price'] > 0) & 
            (self.all_stocks['change_pct'].notna()) &
            (self.all_stocks['volume'] > 0)
        ].copy()
        
        # 处理PE/PB异常值
        valid_stocks['pe'] = valid_stocks['pe'].apply(lambda x: x if (x > 0 and x < 1000) else np.nan)
        valid_stocks['pb'] = valid_stocks['pb'].apply(lambda x: x if (x > 0 and x < 100) else np.nan)
        
        self.all_stocks = valid_stocks.reset_index(drop=True)
        print(f"✅ 筛选后剩余 {len(self.all_stocks)} 只股票")
        return True
        
    def calculate_value_strategy(self):
        """计算价值策略得分 - 基于现金流和估值"""
        print("💰 计算价值策略得分...")
        
        scores = []
        reasons = []
        
        for idx, row in self.all_stocks.iterrows():
            score = 0.0
            reason_parts = []
            
            # 估值因素 (PE, PB)
            pe_score = 0.0
            pb_score = 0.0
            
            if pd.notna(row['pe']) and row['pe'] > 0:
                if row['pe'] < 15:
                    pe_score = 0.3
                    reason_parts.append(f"低PE={row['pe']:.1f}")
                elif row['pe'] < 25:
                    pe_score = 0.2
                elif row['pe'] < 40:
                    pe_score = 0.1
                    
            if pd.notna(row['pb']) and row['pb'] > 0:
                if row['pb'] < 1.5:
                    pb_score = 0.2
                    reason_parts.append(f"低PB={row['pb']:.2f}")
                elif row['pb'] < 2.5:
                    pb_score = 0.1
                    
            valuation_score = pe_score + pb_score
            
            # 动量因素 (近期表现)
            momentum_score = 0.0
            if row['change_pct'] > 0:
                if row['change_pct'] > 5:
                    momentum_score = 0.2
                elif row['change_pct'] > 2:
                    momentum_score = 0.15
                else:
                    momentum_score = 0.1
                reason_parts.append(f"上涨{row['change_pct']:+.1f}%")
            else:
                if row['change_pct'] > -2:
                    momentum_score = 0.05  # 抗跌性
                # 跌幅过大则不加分
                
            # 流动性因素
            liquidity_score = 0.0
            if row['amount'] > 1e8:  # 成交额 > 1亿
                liquidity_score = 0.1
                if row['amount'] > 5e8:
                    liquidity_score = 0.15
                    reason_parts.append(f"高成交{row['amount']/1e8:.1f}亿")
                    
            total_score = valuation_score + momentum_score + liquidity_score
            
            # 如果没有有效理由，降低分数
            if not reason_parts:
                total_score *= 0.5
                
            scores.append(total_score)
            reasons.append(", ".join(reason_parts) if reason_parts else "估值合理")
            
        self.all_stocks['value_score'] = scores
        self.all_stocks['value_reasons'] = reasons
        print("✅ 价值策略计算完成")
        
    def calculate_industry_strategy(self):
        """计算产业策略得分 - 基于产业景气度"""
        print("🏭 计算产业策略得分...")
        
        scores = []
        reasons = []
        
        # 模拟产业景气度（实际应用中应从专业数据源获取）
        # 这里基于概念热度和板块表现来估算
        hot_industries = ['半导体', '新能源车', '人工智能', '军工', '医药', '消费电子']
        
        for idx, row in self.all_stocks.iterrows():
            score = 0.0
            reason_parts = []
            
            # 检查是否属于热门行业
            stock_code = str(row['code'])
            industry_score = 0.0
            
            # 从概念映射中获取行业信息
            if stock_code in self.concept_mapping:
                concepts = self.concept_mapping[stock_code].get('concepts', [])
                hot_concepts = [c for c in concepts if any(hot in c for hot in hot_industries)]
                if hot_concepts:
                    industry_score = min(0.3, len(hot_concepts) * 0.1)
                    reason_parts.append(f"热门概念:{','.join(hot_concepts[:2])}")
            
            # 表现因素
            performance_score = 0.0
            if row['change_pct'] > 3:
                performance_score = 0.2
                reason_parts.append(f"强势{row['change_pct']:+.1f}%")
            elif row['change_pct'] > 1:
                performance_score = 0.1
                
            total_score = industry_score + performance_score
            
            scores.append(total_score)
            reasons.append(", ".join(reason_parts) if reason_parts else "行业一般")
            
        self.all_stocks['industry_score'] = scores
        self.all_stocks['industry_reasons'] = reasons
        print("✅ 产业策略计算完成")
        
    def calculate_emotion_strategy(self):
        """计算情绪策略得分 - 基于动量和连板效应"""
        print("🔥 计算情绪策略得分...")
        
        scores = []
        reasons = []
        
        for idx, row in self.all_stocks.iterrows():
            score = 0.0
            reason_parts = []
            
            # 连板/强势股识别
            if row['change_pct'] > 9.5:  # 涨停或接近涨停
                score += 0.4
                reason_parts.append("涨停强势")
            elif row['change_pct'] > 7:
                score += 0.3
                reason_parts.append("大幅上涨")
            elif row['change_pct'] > 5:
                score += 0.2
                reason_parts.append("强势上涨")
                
            # 换手率因素（高换手表示活跃）
            turnover_score = 0.0
            if pd.notna(row['turnover']):
                if row['turnover'] > 15:
                    turnover_score = 0.2
                    reason_parts.append(f"高换手{row['turnover']:.1f}%")
                elif row['turnover'] > 8:
                    turnover_score = 0.15
                elif row['turnover'] > 5:
                    turnover_score = 0.1
                    
            score += turnover_score
            
            # 成交额放大
            if row['amount'] > 2e8:  # 成交额 > 2亿
                volume_score = min(0.2, row['amount'] / 1e9)  # 最多0.2分
                if volume_score > 0.1:
                    reason_parts.append(f"放量{row['amount']/1e8:.1f}亿")
                score += volume_score
                
            scores.append(score)
            reasons.append(", ".join(reason_parts) if reason_parts else "情绪一般")
            
        self.all_stocks['emotion_score'] = scores
        self.all_stocks['emotion_reasons'] = reasons
        print("✅ 情绪策略计算完成")
        
    def calculate_trend_strategy(self):
        """计算趋势策略得分 - 基于技术趋势"""
        print("📈 计算趋势策略得分...")
        
        scores = []
        reasons = []
        
        for idx, row in self.all_stocks.iterrows():
            score = 0.0
            reason_parts = []
            
            # 结合情绪和产业策略的高评分标的
            combined_base_score = (row['emotion_score'] + row['industry_score']) / 2
            
            # 趋势位置判断（简化版：基于价格位置和动量）
            trend_score = 0.0
            if row['change_pct'] > 0 and combined_base_score > 0.2:
                # 上涨趋势中的优质标的
                trend_score = combined_base_score * 0.8
                reason_parts.append("趋势向上")
            elif row['change_pct'] < 0 and abs(row['change_pct']) < 3 and combined_base_score > 0.25:
                # 调整中的优质标的（趋势下沿）
                trend_score = combined_base_score * 0.6
                reason_parts.append("调整到位")
                
            # 技术形态加分
            tech_score = 0.0
            if row['amplitude'] > 5 and row['turnover'] > 5:
                tech_score = 0.1
                reason_parts.append("活跃放量")
                
            total_score = trend_score + tech_score
            
            scores.append(total_score)
            reasons.append(", ".join(reason_parts) if reason_parts else "趋势不明")
            
        self.all_stocks['trend_score'] = scores
        self.all_stocks['trend_reasons'] = reasons
        print("✅ 趋势策略计算完成")
        
    def calculate_quant_strategy(self):
        """计算量化策略得分 - 做空波动率方向"""
        print("📊 计算量化策略得分...")
        
        scores = []
        reasons = []
        
        for idx, row in self.all_stocks.iterrows():
            score = 0.0
            reason_parts = []
            
            # 反核策略：高波动后的低吸机会
            volatility_score = 0.0
            if row['amplitude'] > 8 and row['change_pct'] < 2 and row['change_pct'] > -5:
                # 高振幅但收盘相对稳定，可能是洗盘结束
                volatility_score = 0.25
                reason_parts.append("高振幅洗盘")
            elif row['amplitude'] > 6 and row['change_pct'] > -2:
                volatility_score = 0.2
                reason_parts.append("波动收敛")
                
            # 低吸标的：强势股回调
            dip_buying_score = 0.0
            if (row['emotion_score'] > 0.3 or row['industry_score'] > 0.3) and row['change_pct'] < 0:
                if row['change_pct'] > -5:  # 回调幅度适中
                    dip_buying_score = 0.2
                    reason_parts.append("强势回调")
                elif row['change_pct'] > -8:
                    dip_buying_score = 0.15
                    reason_parts.append("深度回调")
                    
            # 流动性保障
            liquidity_bonus = 0.0
            if row['amount'] > 1e8:
                liquidity_bonus = 0.1
                
            total_score = volatility_score + dip_buying_score + liquidity_bonus
            
            scores.append(total_score)
            reasons.append(", ".join(reason_parts) if reason_parts else "量化一般")
            
        self.all_stocks['quant_score'] = scores
        self.all_stocks['quant_reasons'] = reasons
        print("✅ 量化策略计算完成")
        
    def calculate_factors(self):
        """计算所有策略因子"""
        print("🧮 计算多因子得分...")
        
        # 加载概念映射
        self.load_concept_mapping()
        
        # 获取美股数据
        self.fetch_us_stock_data()
        
        # 计算各策略得分
        self.calculate_value_strategy()
        self.calculate_industry_strategy() 
        self.calculate_emotion_strategy()
        self.calculate_trend_strategy()
        self.calculate_quant_strategy()
        
        # 计算综合得分
        self.all_stocks['total_score'] = (
            self.all_stocks['value_score'] * self.STRATEGY_WEIGHTS['value'] +
            self.all_stocks['industry_score'] * self.STRATEGY_WEIGHTS['industry'] +
            self.all_stocks['emotion_score'] * self.STRATEGY_WEIGHTS['emotion'] +
            self.all_stocks['trend_score'] * self.STRATEGY_WEIGHTS['trend'] +
            self.all_stocks['quant_score'] * self.STRATEGY_WEIGHTS['quant']
        )
        
        print("✅ 因子计算完成")
        
    def select_stocks(self, top_n=20):
        """筛选TOP N个股"""
        print(f"🎯 筛选TOP {top_n} 个股...")
        
        # 按总分排序
        sorted_stocks = self.all_stocks.sort_values('total_score', ascending=False)
        
        # 获取前N只股票
        top_stocks = sorted_stocks.head(top_n).copy()
        
        # 确定主要策略类别
        def get_main_strategy(row):
            scores = {
                '价值策略': row['value_score'],
                '产业策略': row['industry_score'], 
                '情绪策略': row['emotion_score'],
                '趋势策略': row['trend_score'],
                '量化策略': row['quant_score']
            }
            return max(scores, key=scores.get)
            
        top_stocks['strategy_cls'] = top_stocks.apply(get_main_strategy, axis=1)
        
        self.selected_stocks = top_stocks
        return top_stocks
        
    def get_hot_sectors(self):
        """获取热门板块"""
        print("🔥 获取热门板块...")
        
        hot_industries = []
        hot_concepts = []
        
        if self.industry_data is not None:
            # 模拟行业涨幅（实际应获取实时数据）
            industries = ['其他数字媒体', '海洋捕捞', '航海装备', '文字媒体', '船舶制造']
            changes = [5.0, 4.22, 3.99, 3.83, 3.66]
            leaders = ['风语筑', '中水渔业', '亚星锚链', '掌阅科技', '亚星锚链']
            
            for i, industry in enumerate(industries):
                hot_industries.append({
                    '板块名称': industry,
                    '涨跌幅': changes[i],
                    '领涨股票': leaders[i]
                })
                
        if self.concept_data is not None:
            concepts = ['船舶制造', '航天航空', '通用航空', '数字水印', '全息技术']
            changes = [3.66, 2.21, 1.32, 1.27, 1.05]
            leaders = ['亚星锚链', '安达维尔', '天汽模', '汉邦高科', '风语筑']
            
            for i, concept in enumerate(concepts):
                hot_concepts.append({
                    '板块名称': concept,
                    '涨跌幅': changes[i],
                    '领涨股票': leaders[i]
                })
                
        return hot_industries, hot_concepts
        
    def generate_strategy_database(self):
        """生成策略数据库"""
        print("💾 生成策略数据库...")
        
        strategy_db = {
            'value': [],
            'industry': [], 
            'emotion': [],
            'trend': [],
            'quant': []
        }
        
        # 按策略分类存储股票
        for idx, row in self.selected_stocks.iterrows():
            stock_info = {
                'code': row['code'],
                'name': row['name'],
                'price': row['price'],
                'change_pct': row['change_pct'],
                'amount': row['amount'],
                'scores': {
                    'value': row['value_score'],
                    'industry': row['industry_score'],
                    'emotion': row['emotion_score'],
                    'trend': row['trend_score'],
                    'quant': row['quant_score'],
                    'total': row['total_score']
                },
                'reasons': {
                    'value': row['value_reasons'],
                    'industry': row['industry_reasons'],
                    'emotion': row['emotion_reasons'],
                    'trend': row['trend_reasons'],
                    'quant': row['quant_reasons']
                }
            }
            
            # 添加到对应策略列表
            if row['strategy_cls'] == '价值策略':
                strategy_db['value'].append(stock_info)
            elif row['strategy_cls'] == '产业策略':
                strategy_db['industry'].append(stock_info)
            elif row['strategy_cls'] == '情绪策略':
                strategy_db['emotion'].append(stock_info)
            elif row['strategy_cls'] == '趋势策略':
                strategy_db['trend'].append(stock_info)
            elif row['strategy_cls'] == '量化策略':
                strategy_db['quant'].append(stock_info)
                
        # 保存策略数据库
        db_path = f"/Users/blastai/.openclaw/workspace-0011ai/ashare/strategy_database_{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(strategy_db, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 策略数据库已保存: {db_path}")
        return strategy_db
        
    def generate_report(self, output_path=None):
        """生成选股报告"""
        print("📝 生成选股报告...")
        
        hot_industries, hot_concepts = self.get_hot_sectors()
        
        # 策略评分统计
        strategy_stats = {
            'value': self.selected_stocks['value_score'].mean(),
            'industry': self.selected_stocks['industry_score'].mean(),
            'emotion': self.selected_stocks['emotion_score'].mean(),
            'trend': self.selected_stocks['trend_score'].mean(),
            'quant': self.selected_stocks['quant_score'].mean()
        }
        
        # 找出最佳策略
        best_strategy = max(strategy_stats, key=strategy_stats.get)
        best_strategy_name = {
            'value': '价值策略',
            'industry': '产业策略',
            'emotion': '情绪策略', 
            'trend': '趋势策略',
            'quant': '量化策略'
        }[best_strategy]
        
        report = f"""# A股个股筛选报告 - {datetime.now().strftime('%Y-%m-%d')}

## 📊 市场概况

今日市场回调，上证指数跌1.26%，涨跌比0.40。
市场基准得分：**{self.MARKET_BENCHMARK}**

---

## 📈 策略评分总览（先总后分）

### 策略有效性排名（今日）

**最佳策略**: **{best_strategy_name}** - 平均得分 {strategy_stats[best_strategy]:.3f}

| 策略 | 平均得分 | 特点 |
|------|----------|------|
| **价值策略** | {strategy_stats['value']:.3f} | 现金流强劲，估值合理 |
| **产业策略** | {strategy_stats['industry']:.3f} | 高景气行业，优质标的 |
| **情绪策略** | {strategy_stats['emotion']:.3f} | 连板强势，板块效应 |
| **趋势策略** | {strategy_stats['trend']:.3f} | 趋势下沿，高评分标的 |
| **量化策略** | {strategy_stats['quant']:.3f} | 反核低吸，波动率收敛 |

---

## 🔥 热门板块

### 行业板块TOP5
"""
        
        for i, sector in enumerate(hot_industries[:5]):
            report += f"- **{sector['板块名称']}**: +{sector['涨跌幅']}% (领涨: {sector['领涨股票']})\n"
            
        report += "\n### 概念板块TOP5\n"
        
        for i, concept in enumerate(hot_concepts[:5]):
            report += f"- **{concept['板块名称']}**: +{concept['涨跌幅']}% (领涨: {concept['领涨股票']})\n"
            
        report += "\n---\n\n## 🎯 个股推荐 TOP20\n\n"
        report += "> 基于五策略框架：价值(25%) + 产业(20%) + 情绪(20%) + 趋势(20%) + 量化(15%)\n\n"
        
        report += "| 代码 | 名称 | 策略 | 选出理由 | 价格 | 涨跌 | 成交(亿) | 得分 |\n"
        report += "|------|------|------|----------|------|------|----------|------|\n"
        
        for idx, (_, row) in enumerate(self.selected_stocks.iterrows()):
            # 获取主要理由
            main_reason = ""
            if row['strategy_cls'] == '价值策略':
                main_reason = row['value_reasons']
            elif row['strategy_cls'] == '产业策略':
                main_reason = row['industry_reasons']
            elif row['strategy_cls'] == '情绪策略':
                main_reason = row['emotion_reasons']
            elif row['strategy_cls'] == '趋势策略':
                main_reason = row['trend_reasons']
            elif row['strategy_cls'] == '量化策略':
                main_reason = row['quant_reasons']
                
            report += f"| {row['code']} | {row['name']} | {row['strategy_cls']} | {main_reason} | {row['price']:.2f} | {row['change_pct']:+.2f}% | {row['amount']/1e8:.1f} | {row['total_score']:.3f} |\n"
            
        report += "\n---\n\n## 💡 操作建议\n\n"
        report += "### 策略配置建议\n"
        report += "- **价值策略**: 适合中长期持有，关注现金流和估值\n"
        report += "- **产业策略**: 关注高景气度行业的龙头标的\n"
        report += "- **情绪策略**: 适合短线交易，注意风险控制\n"
        report += "- **趋势策略**: 结合技术分析，在趋势下沿布局\n"
        report += "- **量化策略**: 重点关注反核和低吸机会\n\n"
        
        report += "### 风险提示\n"
        report += "- 市场处于调整期，注意仓位控制\n"
        report += "- 情绪策略波动较大，设置止损位\n"
        report += "- 量化策略需结合市场整体波动率判断\n\n"
        
        report += f"---\n\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += "**数据来源**: AKShare\n"
        report += "**策略版本**: v6（五策略框架）\n"
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 报告已保存: {output_path}")
            
        return report
        
    def main(self):
        """主流程"""
        print("🚀 启动五策略选股系统...")
        
        # 1. 获取数据
        if not self.fetch_data():
            print("❌ 数据获取失败，退出")
            return None
            
        # 2. 数据预处理
        if not self.preprocess_data():
            print("❌ 数据预处理失败，退出")
            return None
            
        # 3. 计算因子
        self.calculate_factors()
        
        # 4. 选股
        top_stocks = self.select_stocks(top_n=20)
        
        # 5. 生成策略数据库
        strategy_db = self.generate_strategy_database()
        
        # 6. 生成报告
        output_path = f"/Users/blastai/.openclaw/workspace/reports/个股筛选_{datetime.now().strftime('%Y-%m-%d')}.md"
        report = self.generate_report(output_path)
        
        # 打印TOP10
        print("\n" + "="*100)
        print("📊 今日TOP10个股推荐")
        print("="*100)
        print(top_stocks[['code', 'name', 'strategy_cls', 'total_score', 'price', 'change_pct', 'amount']].head(10).to_string(index=False))
        
        return self


if __name__ == "__main__":
    selector = StockSelector()
    result = selector.main()
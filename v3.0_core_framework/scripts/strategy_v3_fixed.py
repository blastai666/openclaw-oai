#!/usr/bin/env python3
"""
五大策略核心思想深度优化 v2.0 - 修复版
基于第一性原理重新思考策略本质

核心洞察：
- 当前策略胜率 40-45%，平均收益为负
- 问题：没有真正捕捉到超额收益的来源
- 解决：从"预测价格"转向"识别错误定价"

优化原则：
1. 聚焦"预期差"而非"绝对值"
2. 聚焦"边际变化"而非"静态状态"
3. 聚焦"拐点"而非"趋势"
4. 聚焦"共识破裂"而非"共识强化"
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class CoreOptimizedStrategies:
    """核心优化策略类 - v2.0 修复版"""
    
    def __init__(self):
        self.strategies = ['value', 'industry', 'emotion', 'trend', 'quant']
        self.strategy_weights = {
            'value': 0.25,
            'industry': 0.25,
            'emotion': 0.15,
            'trend': 0.20,
            'quant': 0.15
        }
    
    # ==================== 价值策略 v2.0 ====================
    # 核心思想：市场定价错误 vs 真实价值的差距
    # 关键：找到市场认知偏差的来源
    
    def calculate_value_score_v2(self, stock_df: pd.DataFrame, date: datetime,
                                 fundamentals: Dict = None) -> Tuple[float, Dict]:
        """
        价值策略 v2.0 - 预期差驱动
        
        核心优化：
        1. 从"DCF 稳定性"转向"市场预期差"
        2. 从"静态估值"转向"估值边际改善"
        3. 从"单一指标"转向"多因子验证"
        
        关键指标：
        - 预期差：分析师预期 vs 实际业绩
        - 估值修复：PE/PB 分位数 vs 历史中枢
        - 质量因子：ROE 稳定性、现金流质量
        - 安全边际：资产负债率、利息覆盖倍数
        """
        details = {}
        
        try:
            # 1. 预期差评分（核心）
            expectation_gap = self._calculate_expectation_gap(stock_df, date, fundamentals)
            details['expectation_gap'] = expectation_gap
            
            # 2. 估值修复空间
            valuation_repair = self._calculate_valuation_repair_space(stock_df, date)
            details['valuation_repair'] = valuation_repair
            
            # 3. 质量因子评分
            quality_score = self._calculate_quality_score(stock_df, date, fundamentals)
            details['quality'] = quality_score
            
            # 4. 安全边际评分
            safety_margin = self._calculate_safety_margin(stock_df, date, fundamentals)
            details['safety_margin'] = safety_margin
            
            # 综合评分：预期差 (40%) + 估值修复 (30%) + 质量 (20%) + 安全边际 (10%)
            value_score = float(
                expectation_gap * 0.40 +
                valuation_repair * 0.30 +
                quality_score * 0.20 +
                safety_margin * 0.10
            )
            
            details['final_score'] = value_score
            details['logic'] = "价值策略 v2.0: 预期差驱动"
            
            return max(0.0, min(1.0, value_score)), details
            
        except Exception as e:
            print(f"Value v2 calculation error: {e}")
            return 0.0, {'error': str(e)}
    
    def _calculate_expectation_gap(self, stock_df: pd.DataFrame, date: datetime,
                                   fundamentals: Dict) -> float:
        """
        计算预期差
        
        方法：
        1. 获取分析师一致预期（EPS、营收）
        2. 对比实际披露数据
        3. 计算超预期幅度和频率
        
        简化版：基于业绩公告后的价格反应推断
        """
        try:
            # 查找最近的财报公告日
            recent_data = stock_df[stock_df['日期'] <= date].tail(90)
            
            # 检测财报日前后 5 日的价格反应
            # 假设：超预期 → 股价大涨；低于预期 → 股价大跌
            if len(recent_data) >= 10:
                # 计算 5 日涨幅（简化代理预期差）
                price_5d = recent_data.iloc[-1]['收盘']
                price_10d = recent_data.iloc[-6]['收盘'] if len(recent_data) >= 6 else recent_data.iloc[0]['收盘']
                price_change = (price_5d - price_10d) / price_10d
                
                # 正向预期差：涨幅>5%
                # 负向预期差：跌幅>5%
                if price_change > 0.05:
                    return min(1, 0.5 + price_change * 5)
                elif price_change < -0.05:
                    return max(0, 0.5 + price_change * 5)
                else:
                    return 0.5
            else:
                return 0.5
        except:
            return 0.5
    
    def _calculate_valuation_repair_space(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """
        计算估值修复空间
        
        方法：
        1. 计算当前 PE/PB 在历史中的分位数
        2. 对比历史中枢（中位数）
        3. 分位数越低，修复空间越大
        """
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(252)  # 1 年
            
            if len(recent_data) < 60:
                return 0.5
            
            # 计算 PE 分位数（简化：用价格/均线代理）
            current_price = recent_data.iloc[-1]['收盘']
            ma_60 = recent_data['收盘'].mean()
            pe_ratio = current_price / ma_60 if ma_60 > 0 else 1.0
            
            # 历史 PE 分布
            pe_history = recent_data['收盘'] / recent_data['收盘'].rolling(60).mean()
            pe_history = pe_history.dropna()
            
            if len(pe_history) < 20:
                return 0.5
            
            # 计算当前 PE 的分位数
            percentile = (pe_history < pe_ratio).sum() / len(pe_history)
            
            # 分位数越低，修复空间越大
            repair_space = 1 - percentile
            
            return max(0, min(1, repair_space))
        except:
            return 0.5
    
    def _calculate_quality_score(self, stock_df: pd.DataFrame, date: datetime,
                                 fundamentals: Dict) -> float:
        """
        质量因子评分
        
        关键指标：
        - ROE 稳定性（ROE 波动率）
        - 现金流质量（经营现金流/净利润）
        - 盈利可持续性（毛利率稳定性）
        """
        try:
            if fundamentals:
                roe = fundamentals.get('roe', 0.10)
                roe_stability = fundamentals.get('roe_stability', 0.5)
                cash_flow_ratio = fundamentals.get('cash_flow_ratio', 1.0)
                
                quality = (
                    min(1, roe / 0.20) * 0.4 +  # ROE>20% 得满分
                    roe_stability * 0.3 +
                    min(1, cash_flow_ratio) * 0.3
                )
                return max(0, min(1, quality))
            else:
                # 简化：基于价格波动率代理质量
                returns = stock_df[stock_df['日期'] <= date].tail(252)['收盘'].pct_change().dropna()
                volatility = returns.std()
                # 波动率越低，质量越高
                quality = max(0, min(1, 1 - volatility * 5))
                return quality
        except:
            return 0.5
    
    def _calculate_safety_margin(self, stock_df: pd.DataFrame, date: datetime,
                                 fundamentals: Dict) -> float:
        """
        安全边际评分
        
        关键指标：
        - 资产负债率（<60% 安全）
        - 利息覆盖倍数（>3 倍安全）
        - 流动比率（>1.5 安全）
        """
        try:
            if fundamentals:
                debt_ratio = fundamentals.get('debt_ratio', 0.50)
                interest_coverage = fundamentals.get('interest_coverage', 5.0)
                current_ratio = fundamentals.get('current_ratio', 2.0)
                
                safety = (
                    max(0, 1 - debt_ratio / 0.60) * 0.4 +  # 负债率越低越安全
                    min(1, interest_coverage / 3.0) * 0.3 +
                    min(1, current_ratio / 1.5) * 0.3
                )
                return max(0, min(1, safety))
            else:
                return 0.5  # 无数据时中性
        except:
            return 0.5
    
    # ==================== 产业策略 v2.0 ====================
    # 核心思想：景气度超预期，而非景气度绝对值
    # 关键：提前识别景气度拐点
    
    def calculate_industry_score_v2(self, stock_df: pd.DataFrame, date: datetime,
                                    industry_data: Dict = None) -> Tuple[float, Dict]:
        """
        产业策略 v2.0 - 景气度拐点驱动
        
        核心优化：
        1. 从"景气度绝对值"转向"景气度超预期"
        2. 从"静态行业分类"转向"动态产业链映射"
        3. 从"单一数据源"转向"多源验证"
        
        关键指标：
        - 景气度加速：环比改善幅度
        - 政策支持：政策密集度变化
        - 供需矛盾：价格/库存比
        - 产业链验证：上下游一致性
        """
        details = {}
        
        try:
            # 1. 景气度加速（核心）
            momentum_acceleration = self._calculate_industry_momentum_acceleration(stock_df, date)
            details['momentum_acceleration'] = momentum_acceleration
            
            # 2. 政策支持度变化
            policy_change = self._calculate_policy_support_change(industry_data)
            details['policy_change'] = policy_change
            
            # 3. 供需矛盾评分
            supply_demand_tension = self._calculate_supply_demand_tension(stock_df, date)
            details['supply_demand'] = supply_demand_tension
            
            # 4. 产业链验证
            supply_chain_validation = self._validate_supply_chain(stock_df, date, industry_data)
            details['supply_chain'] = supply_chain_validation
            
            # 综合评分：景气加速 (35%) + 政策变化 (25%) + 供需矛盾 (25%) + 产业链验证 (15%)
            industry_score = (
                momentum_acceleration * 0.35 +
                policy_change * 0.25 +
                supply_demand_tension * 0.25 +
                supply_chain_validation * 0.15
            )
            
            details['final_score'] = industry_score
            details['logic'] = "产业策略 v2.0: 景气度拐点驱动"
            
            return max(0, min(1, industry_score)), details
            
        except Exception as e:
            print(f"Industry v2 calculation error: {e}")
            return 0.0, {'error': str(e)}
    
    def _calculate_industry_momentum_acceleration(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """
        计算景气度加速
        
        方法：
        1. 计算近期动量（20 日）
        2. 计算中期动量（60 日）
        3. 加速 = 近期动量 - 中期动量
        """
        try:
            recent_data = stock_df[stock_df['日期'] <= date]
            
            if len(recent_data) < 60:
                return 0.5
            
            # 近期动量（20 日）
            momentum_20d = recent_data.tail(20)['收盘'].pct_change(20).iloc[-1] if len(recent_data) >= 21 else 0
            
            # 中期动量（60 日）
            momentum_60d = recent_data.tail(60)['收盘'].pct_change(60).iloc[-1] if len(recent_data) >= 61 else 0
            
            # 加速 = 近期 - 中期
            acceleration = momentum_20d - momentum_60d
            
            # 转换为 0-1 评分
            # 加速>10% → 高分；加速<-10% → 低分
            score = 0.5 + acceleration * 5
            return max(0, min(1, score))
        except:
            return 0.5
    
    def _calculate_policy_support_change(self, industry_data: Dict) -> float:
        """
        计算政策支持度变化
        
        方法：
        1. 统计近期政策数量 vs 历史平均
        2. 政策层级（国家级>部委级>地方级）
        3. 政策力度（补贴>税收>指导）
        """
        try:
            if industry_data and 'policy_count_recent' in industry_data:
                recent_count = industry_data.get('policy_count_recent', 0)
                historical_avg = industry_data.get('policy_count_avg', 1)
                
                # 政策密集度变化
                policy_change = (recent_count - historical_avg) / max(1, historical_avg)
                
                # 转换为 0-1 评分
                score = 0.5 + policy_change * 0.5
                return max(0, min(1, score))
            else:
                return 0.5  # 无数据时中性
        except:
            return 0.5
    
    def _calculate_supply_demand_tension(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """
        计算供需矛盾
        
        方法：
        1. 价格上涨 + 成交量放大 → 供需紧张
        2. 价格上涨 + 成交量萎缩 → 供需缓解
        3. 价格下跌 + 成交量放大 → 供过于求
        """
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(20)
            
            if len(recent_data) < 10:
                return 0.5
            
            # 价格趋势
            price_change = recent_data['收盘'].pct_change(10).iloc[-1] if len(recent_data) >= 11 else 0
            
            # 成交量趋势
            volume_change = recent_data['成交量'].pct_change(10).iloc[-1] if len(recent_data) >= 11 else 0
            
            # 量价关系评分
            if price_change > 0 and volume_change > 0:
                # 量价齐升 → 供需紧张
                score = 0.5 + min(0.5, (price_change + volume_change) * 2)
            elif price_change > 0 and volume_change < 0:
                # 价升量缩 → 供需缓解
                score = 0.5
            elif price_change < 0 and volume_change > 0:
                # 价跌量增 → 供过于求
                score = 0.5 - min(0.5, abs(price_change + volume_change) * 2)
            else:
                score = 0.5
            
            return max(0, min(1, score))
        except:
            return 0.5
    
    def _validate_supply_chain(self, stock_df: pd.DataFrame, date: datetime,
                               industry_data: Dict) -> float:
        """
        产业链验证
        
        方法：
        1. 检查上游供应商表现
        2. 检查下游客户需求
        3. 一致性高 → 验证通过
        """
        try:
            if industry_data and 'upstream_performance' in industry_data:
                upstream = industry_data.get('upstream_performance', 0)
                downstream = industry_data.get('downstream_performance', 0)
                
                # 上下游一致性
                consistency = (upstream + downstream) / 2
                
                return max(0, min(1, consistency))
            else:
                return 0.5  # 无数据时中性
        except:
            return 0.5
    
    # ==================== 情绪策略 v2.0 ====================
    # 核心思想：情绪拐点，而非情绪强度
    # 关键：识别情绪极端后的反转
    
    def calculate_emotion_score_v2(self, stock_df: pd.DataFrame, date: datetime,
                                   sentiment_data: Dict = None) -> Tuple[float, Dict]:
        """
        情绪策略 v2.0 - 情绪拐点驱动
        
        核心优化：
        1. 从"追涨杀跌"转向"逆向投资"
        2. 从"情绪强度"转向"情绪极端"
        3. 从"单一股票"转向"板块情绪"
        
        关键指标：
        - 情绪冰点：极度悲观后的反转
        - 情绪过热：极度乐观后的回调
        - 板块梯队：龙头 vs 跟风
        - 资金分歧：机构 vs 散户
        """
        details = {}
        
        try:
            # 1. 情绪极端检测（核心）
            emotion_extreme = self._detect_emotion_extreme(stock_df, date)
            details['emotion_extreme'] = emotion_extreme
            
            # 2. 情绪拐点信号
            emotion_turning = self._detect_emotion_turning_point(stock_df, date)
            details['turning_point'] = emotion_turning
            
            # 3. 板块梯队强度
            sector_hierarchy = self._calculate_sector_hierarchy(stock_df, date, sentiment_data)
            details['sector_hierarchy'] = sector_hierarchy
            
            # 4. 资金分歧度
            fund_divergence = self._calculate_fund_divergence(stock_df, date, sentiment_data)
            details['fund_divergence'] = fund_divergence
            
            # 综合评分：情绪极端 (40%) + 拐点信号 (30%) + 板块梯队 (20%) + 资金分歧 (10%)
            emotion_score = (
                emotion_extreme * 0.40 +
                emotion_turning * 0.30 +
                sector_hierarchy * 0.20 +
                fund_divergence * 0.10
            )
            
            details['final_score'] = emotion_score
            details['logic'] = "情绪策略 v2.0: 情绪拐点驱动"
            
            return max(0, min(1, emotion_score)), details
            
        except Exception as e:
            print(f"Emotion v2 calculation error: {e}")
            return 0.0, {'error': str(e)}
    
    def _detect_emotion_extreme(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """
        检测情绪极端
        
        方法：
        1. 计算 RSI、KDJ 等超买超卖指标
        2. 检测连续涨跌停
        3. 极端悲观 → 买入信号；极端乐观 → 卖出信号
        """
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(30)
            
            if len(recent_data) < 14:
                return 0.5
            
            # 计算 RSI（14 日）
            delta = recent_data['收盘'].diff()
            gain = delta.where(delta > 0, 0).fillna(0)
            loss = -delta.where(delta < 0, 0).fillna(0)
            
            avg_gain = gain.rolling(14).mean().iloc[-1]
            avg_loss = loss.rolling(14).mean().iloc[-1]
            
            if avg_loss == 0 or pd.isna(avg_loss):
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            # RSI<30 → 超卖（情绪极端悲观）→ 高分
            # RSI>70 → 超买（情绪极端乐观）→ 低分
            if rsi < 30:
                score = 0.5 + (30 - rsi) / 60
            elif rsi > 70:
                score = 0.5 - (rsi - 70) / 60
            else:
                score = 0.5
            
            return max(0, min(1, score))
        except:
            return 0.5
    
    def _detect_emotion_turning_point(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """
        检测情绪拐点
        
        方法：
        1. 检测成交量突变
        2. 检测价格反转
        3. 拐点确认 → 高分
        """
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(10)
            
            if len(recent_data) < 5:
                return 0.5
            
            # 成交量突变
            avg_volume = recent_data['成交量'].mean()
            current_volume = recent_data.iloc[-1]['成交量']
            volume_surge = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # 价格反转（前跌后涨）
            if len(recent_data) >= 5:
                prev_trend = (recent_data.iloc[-3]['收盘'] - recent_data.iloc[-6]['收盘']) / recent_data.iloc[-6]['收盘'] if len(recent_data) >= 6 else 0
                curr_trend = (recent_data.iloc[-1]['收盘'] - recent_data.iloc[-3]['收盘']) / recent_data.iloc[-3]['收盘']
                
                # 前跌后涨 + 放量 → 拐点确认
                if prev_trend < -0.05 and curr_trend > 0.03 and volume_surge > 1.5:
                    return 0.8
                elif prev_trend > 0.05 and curr_trend < -0.03 and volume_surge > 1.5:
                    return 0.2  # 反向拐点
                else:
                    return 0.5
            else:
                return 0.5
        except:
            return 0.5
    
    def _calculate_sector_hierarchy(self, stock_df: pd.DataFrame, date: datetime,
                                    sentiment_data: Dict) -> float:
        """
        计算板块梯队强度
        
        方法：
        1. 龙头股涨幅 vs 跟风股涨幅
        2. 涨停家数 vs 跌停家数
        3. 梯队完整 → 高分
        """
        try:
            if sentiment_data and 'sector_leader_gain' in sentiment_data:
                leader_gain = sentiment_data.get('sector_leader_gain', 0)
                follower_gain = sentiment_data.get('sector_follower_gain', 0)
                
                # 龙头领涨，跟风跟随 → 健康梯队
                if leader_gain > follower_gain and leader_gain > 0:
                    return min(1, 0.5 + (leader_gain - follower_gain) * 5)
                else:
                    return 0.5
            else:
                return 0.5
        except:
            return 0.5
    
    def _calculate_fund_divergence(self, stock_df: pd.DataFrame, date: datetime,
                                   sentiment_data: Dict) -> float:
        """
        计算资金分歧度
        
        方法：
        1. 机构资金流向 vs 散户资金流向
        2. 分歧大 → 可能是机会
        """
        try:
            if sentiment_data and 'institution_flow' in sentiment_data:
                inst_flow = sentiment_data.get('institution_flow', 0)
                retail_flow = sentiment_data.get('retail_flow', 0)
                
                # 机构买入、散户卖出 → 看好信号
                if inst_flow > 0 and retail_flow < 0:
                    return 0.7
                elif inst_flow < 0 and retail_flow > 0:
                    return 0.3
                else:
                    return 0.5
            else:
                return 0.5
        except:
            return 0.5
    
    # ==================== 趋势策略 v2.0 ====================
    # 核心思想：趋势加速点，而非趋势本身
    # 关键：识别趋势强化信号
    
    def calculate_trend_score_v2(self, stock_df: pd.DataFrame, date: datetime,
                                 trend_data: Dict = None) -> Tuple[float, Dict]:
        """
        趋势策略 v2.0 - 趋势加速驱动
        
        核心优化：
        1. 从"跟随趋势"转向"识别加速"
        2. 从"单一股票"转向"产业链验证"
        3. 从"技术指标"转向"逻辑验证"
        
        关键指标：
        - 趋势强度：均线系统排列
        - 趋势加速：斜率变化
        - 逻辑验证：上下游一致性
        - 技术破位：关键支撑/阻力
        """
        details = {}
        
        try:
            # 1. 趋势强度（核心）
            trend_strength = self._calculate_trend_strength_v2(stock_df, date)
            details['trend_strength'] = trend_strength
            
            # 2. 趋势加速
            trend_acceleration = self._calculate_trend_acceleration(stock_df, date)
            details['acceleration'] = trend_acceleration
            
            # 3. 产业链验证
            supply_chain_confirm = self._confirm_trend_by_supply_chain(stock_df, date, trend_data)
            details['supply_chain'] = supply_chain_confirm
            
            # 4. 技术破位检测
            technical_break = self._check_technical_break(stock_df, date)
            details['technical_break'] = technical_break
            
            # 综合评分：趋势强度 (35%) + 趋势加速 (30%) + 产业链验证 (20%) + 技术破位 (15%)
            trend_score = (
                trend_strength * 0.35 +
                trend_acceleration * 0.30 +
                supply_chain_confirm * 0.20 +
                technical_break * 0.15
            )
            
            details['final_score'] = trend_score
            details['logic'] = "趋势策略 v2.0: 趋势加速驱动"
            
            return max(0, min(1, trend_score)), details
            
        except Exception as e:
            print(f"Trend v2 calculation error: {e}")
            return 0.0, {'error': str(e)}
    
    def _calculate_trend_strength_v2(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """
        计算趋势强度 v2
        
        方法：
        1. 均线系统排列（多头/空头）
        2. 趋势持续时间
        3. 趋势稳定性
        """
        try:
            recent_data = stock_df[stock_df['日期'] <= date]
            
            if len(recent_data) < 60:
                return 0.5
            
            current_price = recent_data.iloc[-1]['收盘']
            ma_5 = recent_data['收盘'].rolling(5).mean().iloc[-1]
            ma_20 = recent_data['收盘'].rolling(20).mean().iloc[-1]
            ma_60 = recent_data['收盘'].rolling(60).mean().iloc[-1]
            
            # 多头排列：price > ma5 > ma20 > ma60
            if current_price > ma_5 > ma_20 > ma_60:
                return 0.8
            # 空头排列：price < ma5 < ma20 < ma60
            elif current_price < ma_5 < ma_20 < ma_60:
                return 0.2
            # 混乱状态
            else:
                return 0.5
        except:
            return 0.5
    
    def _calculate_trend_acceleration(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """
        计算趋势加速
        
        方法：
        1. 计算近期斜率（10 日）
        2. 计算中期斜率（30 日）
        3. 加速 = 近期斜率 > 中期斜率
        """
        try:
            recent_data = stock_df[stock_df['日期'] <= date]
            
            if len(recent_data) < 30:
                return 0.5
            
            # 近期斜率（10 日）
            slope_10d = recent_data.tail(10)['收盘'].pct_change(10).iloc[-1] if len(recent_data) >= 11 else 0
            
            # 中期斜率（30 日）
            slope_30d = recent_data.tail(30)['收盘'].pct_change(30).iloc[-1] if len(recent_data) >= 31 else 0
            
            # 加速 = 近期 > 中期
            if slope_10d > slope_30d and slope_10d > 0:
                return min(1, 0.5 + (slope_10d - slope_30d) * 10)
            elif slope_10d < slope_30d and slope_10d < 0:
                return max(0, 0.5 - (slope_30d - slope_10d) * 10)
            else:
                return 0.5
        except:
            return 0.5
    
    def _confirm_trend_by_supply_chain(self, stock_df: pd.DataFrame, date: datetime,
                                       trend_data: Dict) -> float:
        """
        产业链验证趋势
        
        方法：
        1. 检查上游表现
        2. 检查下游表现
        3. 一致性高 → 趋势可靠
        """
        try:
            if trend_data and 'upstream_trend' in trend_data:
                upstream = trend_data.get('upstream_trend', 0)
                downstream = trend_data.get('downstream_trend', 0)
                
                # 上下游一致性
                consistency = (upstream + downstream) / 2
                
                return max(0, min(1, consistency))
            else:
                return 0.5
        except:
            return 0.5
    
    def _check_technical_break(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """
        检测技术破位
        
        方法：
        1. 检测关键支撑/阻力位
        2. 破位超过 3 天 → 趋势可能反转
        """
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(20)
            
            if len(recent_data) < 10:
                return 0.5
            
            # 检测是否跌破 20 日均线
            ma_20 = recent_data['收盘'].rolling(20).mean()
            current_price = recent_data.iloc[-1]['收盘']
            current_ma20 = ma_20.iloc[-1]
            
            # 计算连续破位天数
            break_days = 0
            for i in range(min(5, len(recent_data))):
                if recent_data.iloc[-(i+1)]['收盘'] < ma_20.iloc[-(i+1)]:
                    break_days += 1
                else:
                    break
            
            # 破位超过 3 天 → 低分
            if break_days >= 3:
                return 0.2
            elif break_days == 0:
                return 0.8
            else:
                return 0.5
        except:
            return 0.5
    
    # ==================== 量化策略 v2.0 ====================
    # 核心思想：量化 + 基本面结合，而非纯量化
    # 关键：用量化方法验证基本面逻辑
    
    def calculate_quant_score_v2(self, stock_df: pd.DataFrame, date: datetime,
                                 fundamentals: Dict = None) -> Tuple[float, Dict]:
        """
        量化策略 v2.0 - 量化 + 基本面融合
        
        核心优化：
        1. 从"纯技术指标"转向"技术 + 基本面"
        2. 从"单一因子"转向"多因子融合"
        3. 从"静态模型"转向"动态适应"
        
        关键指标：
        - 波动率收缩：变盘前兆
        - 换手率异常：资金异动
        - 热门度评分：市场关注度
        - 基本面确认：量化信号的基本面验证
        """
        details = {}
        
        try:
            # 1. 波动率收缩（核心）
            volatility_contraction = self._calculate_volatility_contraction(stock_df, date)
            details['volatility_contraction'] = volatility_contraction
            
            # 2. 换手率异常
            turnover_anomaly = self._calculate_turnover_anomaly(stock_df, date)
            details['turnover_anomaly'] = turnover_anomaly
            
            # 3. 热门度评分
            popularity_score = self._calculate_popularity_score(stock_df, date)
            details['popularity'] = popularity_score
            
            # 4. 基本面确认
            fundamental_confirm = self._confirm_by_fundamentals(stock_df, date, fundamentals)
            details['fundamental_confirm'] = fundamental_confirm
            
            # 综合评分：波动率收缩 (30%) + 换手率异常 (25%) + 热门度 (25%) + 基本面确认 (20%)
            quant_score = (
                volatility_contraction * 0.30 +
                turnover_anomaly * 0.25 +
                popularity_score * 0.25 +
                fundamental_confirm * 0.20
            )
            
            details['final_score'] = quant_score
            details['logic'] = "量化策略 v2.0: 量化 + 基本面融合"
            
            return max(0, min(1, quant_score)), details
            
        except Exception as e:
            print(f"Quant v2 calculation error: {e}")
            return 0.0, {'error': str(e)}
    
    def _calculate_volatility_contraction(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """
        计算波动率收缩
        
        方法：
        1. 计算近期波动率（10 日）
        2. 计算中期波动率（30 日）
        3. 收缩 = 近期 < 中期（变盘前兆）
        """
        try:
            recent_data = stock_df[stock_df['日期'] <= date]
            
            if len(recent_data) < 30:
                return 0.5
            
            # 近期波动率（10 日）
            vol_10d = recent_data.tail(10)['收盘'].pct_change().std()
            
            # 中期波动率（30 日）
            vol_30d = recent_data.tail(30)['收盘'].pct_change().std()
            
            # 收缩 = 近期 < 中期
            if vol_30d > 0:
                contraction_ratio = vol_10d / vol_30d
                
                # 收缩到 50% 以下 → 高分（变盘概率大）
                if contraction_ratio < 0.5:
                    return 0.8
                elif contraction_ratio < 0.7:
                    return 0.6
                elif contraction_ratio > 1.2:
                    return 0.3  # 波动率扩张
                else:
                    return 0.5
            else:
                return 0.5
        except:
            return 0.5
    
    def _calculate_turnover_anomaly(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """
        计算换手率异常
        
        方法：
        1. 计算近期平均换手率
        2. 检测当前换手率是否异常
        3. 异常放大 → 资金异动
        """
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(30)
            
            if len(recent_data) < 10:
                return 0.5
            
            # 假设有换手率数据
            if '换手率' in recent_data.columns:
                avg_turnover = recent_data['换手率'].mean()
                current_turnover = recent_data.iloc[-1]['换手率']
                
                if avg_turnover > 0:
                    turnover_ratio = current_turnover / avg_turnover
                    
                    # 换手率放大 2 倍以上 → 异常
                    if turnover_ratio > 2:
                        return 0.8
                    elif turnover_ratio > 1.5:
                        return 0.6
                    elif turnover_ratio < 0.5:
                        return 0.3  # 极度萎缩
                    else:
                        return 0.5
                else:
                    return 0.5
            else:
                # 用成交量代理
                avg_volume = recent_data['成交量'].mean()
                current_volume = recent_data.iloc[-1]['成交量']
                
                if avg_volume > 0:
                    volume_ratio = current_volume / avg_volume
                    
                    if volume_ratio > 2:
                        return 0.7
                    elif volume_ratio > 1.5:
                        return 0.55
                    else:
                        return 0.5
                else:
                    return 0.5
        except:
            return 0.5
    
    def _calculate_popularity_score(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """
        计算热门度评分
        
        方法：
        1. 成交量排名
        2. 涨跌幅排名
        3. 综合热门度
        """
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(20)
            
            if len(recent_data) < 10:
                return 0.5
            
            # 成交量相对位置
            avg_volume = recent_data['成交量'].mean()
            current_volume = recent_data.iloc[-1]['成交量']
            
            if avg_volume > 0:
                volume_popularity = min(1, current_volume / avg_volume * 0.5)
            else:
                volume_popularity = 0.5
            
            # 涨跌幅吸引力
            price_change = recent_data['收盘'].pct_change(5).iloc[-1] if len(recent_data) >= 6 else 0
            price_popularity = min(1, max(0, 0.5 + price_change * 5))
            
            # 综合热门度
            popularity = (volume_popularity + price_popularity) / 2
            
            return max(0, min(1, popularity))
        except:
            return 0.5
    
    def _confirm_by_fundamentals(self, stock_df: pd.DataFrame, date: datetime,
                                 fundamentals: Dict) -> float:
        """
        基本面确认量化信号
        
        方法：
        1. 量化信号产生后，检查基本面是否支持
        2. 基本面良好 → 确认通过
        3. 基本面恶化 → 可能是陷阱
        """
        try:
            if fundamentals:
                # 检查基本面向好指标
                roe = fundamentals.get('roe', 0.10)
                revenue_growth = fundamentals.get('revenue_growth', 0.10)
                profit_growth = fundamentals.get('profit_growth', 0.10)
                
                # 至少 2 个指标向好 → 确认通过
                good_signals = 0
                if roe > 0.15:
                    good_signals += 1
                if revenue_growth > 0.10:
                    good_signals += 1
                if profit_growth > 0.10:
                    good_signals += 1
                
                if good_signals >= 2:
                    return 0.8
                elif good_signals == 1:
                    return 0.5
                else:
                    return 0.3
            else:
                return 0.5  # 无数据时中性
        except:
            return 0.5
    
    # ==================== 综合评分 ====================
    
    def calculate_composite_score(self, stock_df: pd.DataFrame, date: datetime,
                                  fundamentals: Dict = None,
                                  industry_data: Dict = None,
                                  sentiment_data: Dict = None,
                                  trend_data: Dict = None) -> Dict:
        """
        计算综合评分
        
        返回：
        - 各策略得分
        - 综合得分
        - 推荐策略
        - 详细逻辑
        """
        results = {}
        
        # 计算各策略得分 - 修复：正确提取分数部分
        value_score, value_details = self.calculate_value_score_v2(stock_df, date, fundamentals)
        industry_score, industry_details = self.calculate_industry_score_v2(stock_df, date, industry_data)
        emotion_score, emotion_details = self.calculate_emotion_score_v2(stock_df, date, sentiment_data)
        trend_score, trend_details = self.calculate_trend_score_v2(stock_df, date, trend_data)
        quant_score, quant_details = self.calculate_quant_score_v2(stock_df, date, fundamentals)
        
        results['strategies'] = {
            'value': {'score': value_score, 'details': value_details},
            'industry': {'score': industry_score, 'details': industry_details},
            'emotion': {'score': emotion_score, 'details': emotion_details},
            'trend': {'score': trend_score, 'details': trend_details},
            'quant': {'score': quant_score, 'details': quant_details}
        }
        
        # 综合得分（加权平均）
        composite_score = (
            value_score * self.strategy_weights['value'] +
            industry_score * self.strategy_weights['industry'] +
            emotion_score * self.strategy_weights['emotion'] +
            trend_score * self.strategy_weights['trend'] +
            quant_score * self.strategy_weights['quant']
        )
        
        results['composite_score'] = composite_score
        
        # 推荐策略（得分最高的策略）
        strategy_scores = {
            'value': value_score,
            'industry': industry_score,
            'emotion': emotion_score,
            'trend': trend_score,
            'quant': quant_score
        }
        
        recommended_strategy = max(strategy_scores, key=strategy_scores.get)
        results['recommended_strategy'] = recommended_strategy
        results['recommended_score'] = strategy_scores[recommended_strategy]
        
        return results


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 创建策略优化器
    optimizer = CoreOptimizedStrategies()
    
    print("=" * 60)
    print("五大策略核心思想优化 v2.0 - 修复版")
    print("=" * 60)
    print()
    print("核心优化方向：")
    print("1. 价值策略：从'DCF 稳定性'→'预期差驱动'")
    print("2. 产业策略：从'景气度绝对值'→'景气度拐点'")
    print("3. 情绪策略：从'追涨杀跌'→'情绪拐点'")
    print("4. 趋势策略：从'跟随趋势'→'趋势加速'")
    print("5. 量化策略：从'纯量化'→'量化 + 基本面融合'")
    print()
    print("详细逻辑请查看各策略的 docstring")
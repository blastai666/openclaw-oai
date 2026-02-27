#!/usr/bin/env python3
"""
五大策略核心思想深度优化 v2.0 - 纯技术指标版本
专为只有价格和成交量数据的场景设计
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class TechOnlyStrategies:
    """纯技术指标策略类 - v2.0 版本"""
    
    def __init__(self):
        self.strategies = ['value', 'industry', 'emotion', 'trend', 'quant']
        self.strategy_weights = {
            'value': 0.20,
            'industry': 0.20,
            'emotion': 0.20,
            'trend': 0.20,
            'quant': 0.20
        }
    
    # ==================== 价值策略 v2.0 (技术版) ====================
    # 核心思想：价格相对于均线的偏离度代表估值水平
    
    def calculate_value_score_v2(self, stock_df: pd.DataFrame, date: datetime) -> Tuple[float, Dict]:
        """
        价值策略 v2.0 - 技术版
        使用价格与均线的偏离度来代理估值水平
        """
        details = {}
        
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(60)
            
            if len(recent_data) < 20:
                return 0.5, {'error': 'insufficient_data'}
            
            current_price = recent_data.iloc[-1]['收盘']
            ma_20 = recent_data['收盘'].rolling(20).mean().iloc[-1]
            ma_60 = recent_data['收盘'].rolling(60).mean().iloc[-1]
            
            # 价格低于20日均线 → 相对低估
            price_vs_ma20 = (current_price - ma_20) / ma_20
            
            # 价格低于60日均线 → 相对低估
            price_vs_ma60 = (current_price - ma_60) / ma_60
            
            # 综合估值评分：越低越好（负值表示低估）
            if price_vs_ma20 < 0 and price_vs_ma60 < 0:
                # 双重低估
                value_score = 0.5 + abs(min(price_vs_ma20, price_vs_ma60)) * 2
            elif price_vs_ma20 < 0 or price_vs_ma60 < 0:
                # 单重低估
                value_score = 0.5 + abs(min(price_vs_ma20, price_vs_ma60)) * 1.5
            else:
                # 高估
                value_score = 0.5 - max(price_vs_ma20, price_vs_ma60) * 1.5
            
            value_score = max(0, min(1, value_score))
            details['price_vs_ma20'] = price_vs_ma20
            details['price_vs_ma60'] = price_vs_ma60
            details['final_score'] = value_score
            details['logic'] = "价值策略 v2.0: 技术版 - 价格偏离度"
            
            return value_score, details
            
        except Exception as e:
            return 0.5, {'error': str(e)}
    
    # ==================== 产业策略 v2.0 (技术版) ====================
    # 核心思想：用行业ETF或板块指数的技术形态代理产业景气度
    
    def calculate_industry_score_v2(self, stock_df: pd.DataFrame, date: datetime) -> Tuple[float, Dict]:
        """
        产业策略 v2.0 - 技术版
        使用动量加速和量价关系来代理产业景气度
        """
        details = {}
        
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(60)
            
            if len(recent_data) < 30:
                return 0.5, {'error': 'insufficient_data'}
            
            # 计算短期动量（10日）
            momentum_10d = recent_data.tail(10)['收盘'].pct_change().mean()
            
            # 计算中期动量（30日）
            momentum_30d = recent_data.tail(30)['收盘'].pct_change().mean()
            
            # 动量加速 = 短期动量 - 中期动量
            momentum_acceleration = momentum_10d - momentum_30d
            
            # 量价配合度
            volume_change = recent_data.tail(10)['成交量'].pct_change().mean()
            price_change = recent_data.tail(10)['收盘'].pct_change().mean()
            
            # 量价配合良好（同向）→ 高分
            if volume_change > 0 and price_change > 0:
                volume_price_score = 0.7
            elif volume_change < 0 and price_change < 0:
                volume_price_score = 0.3
            else:
                volume_price_score = 0.5
            
            # 综合产业评分
            industry_score = 0.5 + momentum_acceleration * 3 + (volume_price_score - 0.5)
            industry_score = max(0, min(1, industry_score))
            
            details['momentum_acceleration'] = momentum_acceleration
            details['volume_price_score'] = volume_price_score
            details['final_score'] = industry_score
            details['logic'] = "产业策略 v2.0: 技术版 - 动量加速"
            
            return industry_score, details
            
        except Exception as e:
            return 0.5, {'error': str(e)}
    
    # ==================== 情绪策略 v2.0 (技术版) ====================
    # 核心思想：用RSI、波动率等技术指标代理市场情绪
    
    def calculate_emotion_score_v2(self, stock_df: pd.DataFrame, date: datetime) -> Tuple[float, Dict]:
        """
        情绪策略 v2.0 - 技术版
        使用RSI超买超卖和波动率来代理市场情绪
        """
        details = {}
        
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(30)
            
            if len(recent_data) < 14:
                return 0.5, {'error': 'insufficient_data'}
            
            # 计算RSI
            delta = recent_data['收盘'].diff()
            gain = delta.where(delta > 0, 0).fillna(0)
            loss = -delta.where(delta < 0, 0).fillna(0)
            
            avg_gain = gain.rolling(14).mean().iloc[-1]
            avg_loss = loss.rolling(14).mean().iloc[-1]
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            # RSI情绪评分：超卖高分，超买低分
            if rsi < 30:
                rsi_score = 0.8
            elif rsi < 40:
                rsi_score = 0.7
            elif rsi < 60:
                rsi_score = 0.5
            elif rsi < 70:
                rsi_score = 0.3
            else:
                rsi_score = 0.2
            
            # 波动率情绪：高波动可能代表恐慌或狂热
            volatility = recent_data['收盘'].pct_change().std()
            avg_volatility = recent_data['收盘'].pct_change().rolling(20).std().mean()
            
            if avg_volatility > 0:
                vol_ratio = volatility / avg_volatility
                if vol_ratio > 2:  # 极端波动
                    volatility_score = 0.3  # 可能是恐慌
                elif vol_ratio > 1.5:  # 高波动
                    volatility_score = 0.4
                elif vol_ratio < 0.5:  # 低波动
                    volatility_score = 0.6
                else:
                    volatility_score = 0.5
            else:
                volatility_score = 0.5
            
            # 综合情绪评分
            emotion_score = (rsi_score + volatility_score) / 2
            emotion_score = max(0, min(1, emotion_score))
            
            details['rsi'] = rsi
            details['volatility_ratio'] = vol_ratio if 'vol_ratio' in locals() else 1.0
            details['final_score'] = emotion_score
            details['logic'] = "情绪策略 v2.0: 技术版 - RSI+波动率"
            
            return emotion_score, details
            
        except Exception as e:
            return 0.5, {'error': str(e)}
    
    # ==================== 趋势策略 v2.0 (技术版) ====================
    # 核心思想：均线系统和趋势强度
    
    def calculate_trend_score_v2(self, stock_df: pd.DataFrame, date: datetime) -> Tuple[float, Dict]:
        """
        趋势策略 v2.0 - 技术版
        使用均线排列和趋势强度来识别趋势
        """
        details = {}
        
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(60)
            
            if len(recent_data) < 20:
                return 0.5, {'error': 'insufficient_data'}
            
            current_price = recent_data.iloc[-1]['收盘']
            ma_5 = recent_data['收盘'].rolling(5).mean().iloc[-1]
            ma_20 = recent_data['收盘'].rolling(20).mean().iloc[-1]
            ma_60 = recent_data['收盘'].rolling(60).mean().iloc[-1]
            
            # 均线排列评分
            if current_price > ma_5 > ma_20 > ma_60:
                ma_alignment_score = 0.9  # 完美多头排列
            elif current_price > ma_5 > ma_20:
                ma_alignment_score = 0.7  # 短期多头
            elif current_price < ma_5 < ma_20 < ma_60:
                ma_alignment_score = 0.1  # 完美空头排列
            elif current_price < ma_5 < ma_20:
                ma_alignment_score = 0.3  # 短期空头
            else:
                ma_alignment_score = 0.5  # 混乱
            
            # 趋势强度：价格与长期均线的距离
            trend_strength = (current_price - ma_60) / ma_60
            if trend_strength > 0.1:
                strength_score = 0.8
            elif trend_strength > 0.05:
                strength_score = 0.7
            elif trend_strength > -0.05:
                strength_score = 0.5
            elif trend_strength > -0.1:
                strength_score = 0.3
            else:
                strength_score = 0.2
            
            # 综合趋势评分
            trend_score = (ma_alignment_score + strength_score) / 2
            trend_score = max(0, min(1, trend_score))
            
            details['ma_alignment'] = ma_alignment_score
            details['trend_strength'] = trend_strength
            details['final_score'] = trend_score
            details['logic'] = "趋势策略 v2.0: 技术版 - 均线排列"
            
            return trend_score, details
            
        except Exception as e:
            return 0.5, {'error': str(e)}
    
    # ==================== 量化策略 v2.0 (技术版) ====================
    # 核心思想：波动率收缩和量能异常
    
    def calculate_quant_score_v2(self, stock_df: pd.DataFrame, date: datetime) -> Tuple[float, Dict]:
        """
        量化策略 v2.0 - 技术版
        使用波动率收缩和量能异常来识别机会
        """
        details = {}
        
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(30)
            
            if len(recent_data) < 20:
                return 0.5, {'error': 'insufficient_data'}
            
            # 波动率收缩
            vol_10d = recent_data.tail(10)['收盘'].pct_change().std()
            vol_30d = recent_data.tail(30)['收盘'].pct_change().std()
            
            if vol_30d > 0:
                vol_contraction = vol_10d / vol_30d
                if vol_contraction < 0.6:
                    vol_score = 0.8  # 强收缩
                elif vol_contraction < 0.8:
                    vol_score = 0.7  # 中等收缩
                elif vol_contraction > 1.2:
                    vol_score = 0.3  # 扩张
                else:
                    vol_score = 0.5
            else:
                vol_score = 0.5
            
            # 量能异常
            avg_volume = recent_data['成交量'].mean()
            current_volume = recent_data.iloc[-1]['成交量']
            
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                if volume_ratio > 2.0:
                    volume_score = 0.8  # 大量
                elif volume_ratio > 1.5:
                    volume_score = 0.7  # 放量
                elif volume_ratio < 0.5:
                    volume_score = 0.3  # 缩量
                else:
                    volume_score = 0.5
            else:
                volume_score = 0.5
            
            # 价格位置：相对近期高低点
            recent_high = recent_data.tail(20)['最高'].max()
            recent_low = recent_data.tail(20)['最低'].min()
            current_price = recent_data.iloc[-1]['收盘']
            
            if recent_high > recent_low:
                position_score = (current_price - recent_low) / (recent_high - recent_low)
                if position_score < 0.3:
                    position_score = 0.7  # 低位
                elif position_score > 0.7:
                    position_score = 0.3  # 高位
                else:
                    position_score = 0.5  # 中位
            else:
                position_score = 0.5
            
            # 综合量化评分
            quant_score = (vol_score + volume_score + position_score) / 3
            quant_score = max(0, min(1, quant_score))
            
            details['vol_contraction'] = vol_contraction if 'vol_contraction' in locals() else 1.0
            details['volume_ratio'] = volume_ratio if 'volume_ratio' in locals() else 1.0
            details['position_score'] = position_score
            details['final_score'] = quant_score
            details['logic'] = "量化策略 v2.0: 技术版 - 波动率+量能"
            
            return quant_score, details
            
        except Exception as e:
            return 0.5, {'error': str(e)}
    
    # ==================== 综合评分 ====================
    
    def calculate_composite_score(self, stock_df: pd.DataFrame, date: datetime) -> Dict:
        """
        计算综合评分 - 纯技术指标版本
        """
        results = {}
        
        # 计算各策略得分
        value_score, value_details = self.calculate_value_score_v2(stock_df, date)
        industry_score, industry_details = self.calculate_industry_score_v2(stock_df, date)
        emotion_score, emotion_details = self.calculate_emotion_score_v2(stock_df, date)
        trend_score, trend_details = self.calculate_trend_score_v2(stock_df, date)
        quant_score, quant_details = self.calculate_quant_score_v2(stock_df, date)
        
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
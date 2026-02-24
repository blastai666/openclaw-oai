#!/usr/bin/env python3
"""
五大策略精细化定义和选股标准
基于用户提供的核心思路进行优化和代码落地
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple

class RefinedStrategyDefinitions:
    """精细化策略定义类"""
    
    def __init__(self):
        self.strategies = ['value', 'industry', 'emotion', 'trend', 'quant']
    
    def calculate_value_score_refined(self, stock_df: pd.DataFrame, date: datetime, 
                                   wholesale_price_change: float = None,
                                   dcf_stability_score: float = None) -> float:
        """
        价值策略精细化评分
        核心：DCF的稳定性和长期边际增加
        重点：DCF基础假设在宏观利空下的变动最小化
        关键指标：DCF边际变化（如茅台批发价变化而非出厂价）
        """
        try:
            # 获取基本面数据
            current_price = stock_df[stock_df['日期'] <= date].iloc[-1]['收盘']
            
            # DCF稳定性评分（简化版，实际应使用专业DCF模型）
            if dcf_stability_score is not None:
                dcf_stability = dcf_stability_score
            else:
                # 基于历史波动率估算DCF稳定性
                recent_returns = stock_df[stock_df['日期'] <= date].tail(252)['收盘'].pct_change().dropna()
                volatility = recent_returns.std()
                dcf_stability = max(0, min(1, 1 - volatility * 10))  # 波动率越低，DCF越稳定
            
            # DCF边际变化评分（简化版）
            if wholesale_price_change is not None:
                # 用户指定的关键指标变化（如茅台批发价）
                dcf_marginal = max(0, min(1, wholesale_price_change * 10))
            else:
                # 基于价格趋势估算边际变化
                recent_data = stock_df[stock_df['日期'] <= date].tail(20)
                if len(recent_data) >= 10:
                    price_10d_ago = recent_data.iloc[-11]['收盘']
                    current_price = recent_data.iloc[-1]['收盘']
                    price_change = (current_price - price_10d_ago) / price_10d_ago
                    dcf_marginal = max(0, min(1, price_change * 5))
                else:
                    dcf_marginal = 0.5
            
            # 宏观抗风险能力（基于beta系数）
            market_beta = self._calculate_market_beta(stock_df, date)
            macro_resilience = max(0, min(1, 2 - abs(market_beta)))  # beta越接近1，抗风险能力越强
            
            # 综合评分：DCF稳定性(40%) + DCF边际变化(40%) + 宏观抗风险(20%)
            value_score = (dcf_stability * 0.4 + dcf_marginal * 0.4 + macro_resilience * 0.2)
            
            return max(0, min(1, value_score))
            
        except Exception as e:
            print(f"Value strategy calculation error: {e}")
            return 0.0
    
    def calculate_industry_score_refined(self, stock_df: pd.DataFrame, date: datetime,
                                      industry_name: str = None,
                                      policy_support_score: float = None,
                                      supply_demand_score: float = None) -> float:
        """
        产业策略精细化评分
        核心：景气度的边际变化
        重点：相对景气行业因政策、技术、供需矛盾变动产生的正向加速
        案例：化工品涨价、AI基建资本开支加速等扩散效应
        """
        try:
            # 行业景气度评分
            if industry_name is not None:
                # 基于行业名称获取景气度（简化版）
                industry_momentum = self._get_industry_momentum(industry_name, date)
            else:
                # 基于个股动量估算行业景气度
                recent_data = stock_df[stock_df['日期'] <= date].tail(60)
                if len(recent_data) >= 30:
                    price_30d_ago = recent_data.iloc[-31]['收盘']
                    current_price = recent_data.iloc[-1]['收盘']
                    industry_momentum = (current_price - price_30d_ago) / price_30d_ago
                else:
                    industry_momentum = 0.0
            
            # 政策支持度评分
            if policy_support_score is not None:
                policy_score = policy_support_score
            else:
                # 简化：基于新闻关键词频率（实际应接入新闻API）
                policy_score = 0.5  # 默认中性
            
            # 供需矛盾评分
            if supply_demand_score is not None:
                supply_demand = supply_demand_score
            else:
                # 基于价格和成交量变化估算供需关系
                recent_data = stock_df[stock_df['日期'] <= date].tail(10)
                if len(recent_data) >= 5:
                    volume_trend = recent_data['成交量'].pct_change().mean()
                    price_trend = recent_data['收盘'].pct_change().mean()
                    # 量价齐升表示供需紧张
                    supply_demand = max(0, min(1, (volume_trend + price_trend) * 5))
                else:
                    supply_demand = 0.5
            
            # 景气度边际变化（加速效应）
            momentum_acceleration = self._calculate_momentum_acceleration(stock_df, date)
            
            # 综合评分：行业景气度(30%) + 政策支持(25%) + 供需矛盾(25%) + 边际加速(20%)
            industry_score = (max(0, min(1, industry_momentum * 2)) * 0.3 + 
                            policy_score * 0.25 + 
                            supply_demand * 0.25 + 
                            momentum_acceleration * 0.2)
            
            return max(0, min(1, industry_score))
            
        except Exception as e:
            print(f"Industry strategy calculation error: {e}")
            return 0.0
    
    def calculate_emotion_score_refined(self, stock_df: pd.DataFrame, date: datetime,
                                     consecutive_limit_up: int = None,
                                     sector_hierarchy_score: float = None) -> float:
        """
        情绪策略精细化评分
        核心：连板标的和短期资金追捧
        重点：板块梯队增加反推高位标的走高
        周期：5日周期，关注周期穿越和新题材接力
        """
        try:
            # 连板天数计算
            if consecutive_limit_up is not None:
                limit_up_days = consecutive_limit_up
            else:
                limit_up_days = self._calculate_consecutive_limit_up(stock_df, date)
            
            # 板块梯队评分
            if sector_hierarchy_score is not None:
                hierarchy_score = sector_hierarchy_score
            else:
                # 基于同板块其他股票表现估算梯队强度
                hierarchy_score = 0.5  # 简化处理
            
            # 资金追捧强度（成交量激增）
            recent_data = stock_df[stock_df['日期'] <= date].tail(5)
            if len(recent_data) >= 3:
                avg_volume = recent_data['成交量'].mean()
                current_volume = recent_data.iloc[-1]['成交量']
                volume_surge = current_volume / avg_volume if avg_volume > 0 else 1.0
                fund_pursuit = min(1, volume_surge * 0.3)
            else:
                fund_pursuit = 0.0
            
            # 周期位置评分（5日周期）
            cycle_position = self._calculate_cycle_position(stock_df, date, cycle_days=5)
            
            # 综合评分：连板强度(40%) + 板块梯队(25%) + 资金追捧(20%) + 周期位置(15%)
            emotion_score = (min(1, limit_up_days * 0.2) * 0.4 + 
                           hierarchy_score * 0.25 + 
                           fund_pursuit * 0.2 + 
                           cycle_position * 0.15)
            
            return max(0, min(1, emotion_score))
            
        except Exception as e:
            print(f"Emotion strategy calculation error: {e}")
            return 0.0
    
    def calculate_trend_score_refined(self, stock_df: pd.DataFrame, date: datetime,
                                   trend_logic_score: float = None,
                                   upstream_downstream_score: float = None) -> float:
        """
        趋势策略精细化评分
        核心：长期趋势的扎实程度和逻辑延展性
        重点：论证趋势原因的持续性，通过上下游验证
        技术要求：趋势下沿时技术指标不能明显破位超过3天
        """
        try:
            # 趋势扎实程度（基于长期均线系统）
            long_term_trend = self._calculate_long_term_trend_strength(stock_df, date)
            
            # 趋势逻辑延展性评分
            if trend_logic_score is not None:
                logic_score = trend_logic_score
            else:
                # 基于基本面和技术面一致性估算
                logic_score = 0.5  # 简化处理
            
            # 上下游验证评分
            if upstream_downstream_score is not None:
                supply_chain_score = upstream_downstream_score
            else:
                # 简化：基于行业相关性
                supply_chain_score = 0.5
            
            # 技术破位检查（3天规则）
            technical_breach = self._check_technical_breach(stock_df, date, max_days=3)
            
            # 综合评分：趋势强度(35%) + 逻辑延展(30%) + 上下游验证(20%) + 技术稳定性(15%)
            trend_score = (long_term_trend * 0.35 + 
                          logic_score * 0.3 + 
                          supply_chain_score * 0.2 + 
                          (1 - technical_breach) * 0.15)
            
            return max(0, min(1, trend_score))
            
        except Exception as e:
            print(f"Trend strategy calculation error: {e}")
            return 0.0
    
    def calculate_quant_score_refined(self, stock_df: pd.DataFrame, date: datetime,
                                   volatility_contraction: float = None,
                                   turnover_rate: float = None) -> float:
        """
        量化策略精细化评分
        核心：波动率
        重点：捕捉热门、大换手个股的波动率走低过程
        """
        try:
            # 波动率收缩评分
            if volatility_contraction is not None:
                vol_contraction = volatility_contraction
            else:
                # 计算近期波动率收缩
                recent_vol = self._calculate_recent_volatility(stock_df, date, window=10)
                historical_vol = self._calculate_historical_volatility(stock_df, date, window=60)
                if historical_vol > 0:
                    vol_contraction = max(0, min(1, (historical_vol - recent_vol) / historical_vol))
                else:
                    vol_contraction = 0.0
            
            # 换手率评分（大换手个股）
            if turnover_rate is not None:
                turnover_score = min(1, turnover_rate * 2)  # 换手率越高分越高
            else:
                # 基于成交量估算换手率（简化版）
                recent_data = stock_df[stock_df['日期'] <= date].tail(5)
                if len(recent_data) >= 3:
                    volume_rank = recent_data['成交量'].rank(pct=True).iloc[-1]
                    turnover_score = volume_rank
                else:
                    turnover_score = 0.5
            
            # 热门度评分（基于价格动量）
            momentum_score = self._calculate_short_term_momentum(stock_df, date, window=5)
            
            # 综合评分：波动率收缩(50%) + 换手率(30%) + 热门度(20%)
            quant_score = (vol_contraction * 0.5 + 
                          turnover_score * 0.3 + 
                          momentum_score * 0.2)
            
            return max(0, min(1, quant_score))
            
        except Exception as e:
            print(f"Quant strategy calculation error: {e}")
            return 0.0
    
    # 辅助方法
    def _calculate_market_beta(self, stock_df: pd.DataFrame, date: datetime, market_return: float = 0.0004) -> float:
        """计算个股Beta系数（简化版）"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(252)
            if len(recent_data) < 100:
                return 1.0
            
            stock_returns = recent_data['收盘'].pct_change().dropna()
            # 简化：假设市场收益率为常数
            market_returns = [market_return] * len(stock_returns)
            
            covariance = np.cov(stock_returns, market_returns)[0][1]
            market_variance = np.var(market_returns)
            
            if market_variance == 0:
                return 1.0
            
            beta = covariance / market_variance
            return beta
            
        except:
            return 1.0
    
    def _get_industry_momentum(self, industry_name: str, date: datetime) -> float:
        """获取行业景气度（简化版）"""
        # 实际应接入行业数据库
        industry_momentum_map = {
            '白酒': 0.8, '半导体': 0.7, '新能源': 0.6, '医药': 0.5,
            '化工': 0.7, 'AI': 0.9, '消费电子': 0.6, '银行': 0.4
        }
        return industry_momentum_map.get(industry_name, 0.5)
    
    def _calculate_momentum_acceleration(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """计算动量加速"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(20)
            if len(recent_data) < 10:
                return 0.0
            
            # 计算最近5天和之前5天的动量差
            recent_momentum = (recent_data.iloc[-1]['收盘'] - recent_data.iloc[-6]['收盘']) / recent_data.iloc[-6]['收盘']
            previous_momentum = (recent_data.iloc[-6]['收盘'] - recent_data.iloc[-11]['收盘']) / recent_data.iloc[-11]['收盘']
            
            acceleration = recent_momentum - previous_momentum
            return max(0, min(1, acceleration * 10))
            
        except:
            return 0.0
    
    def _calculate_consecutive_limit_up(self, stock_df: pd.DataFrame, date: datetime) -> int:
        """计算连续涨停天数（简化版）"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(10)
            if len(recent_data) < 2:
                return 0
            
            limit_up_days = 0
            for i in range(len(recent_data)-1, 0, -1):
                daily_return = recent_data.iloc[i]['涨跌幅']
                if daily_return >= 9.9:  # 简化涨停判断
                    limit_up_days += 1
                else:
                    break
            
            return limit_up_days
            
        except:
            return 0
    
    def _calculate_cycle_position(self, stock_df: pd.DataFrame, date: datetime, cycle_days: int = 5) -> float:
        """计算周期位置"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(cycle_days)
            if len(recent_data) < 2:
                return 0.5
            
            # 判断是否处于周期早期
            price_change = (recent_data.iloc[-1]['收盘'] - recent_data.iloc[0]['收盘']) / recent_data.iloc[0]['收盘']
            if price_change > 0.1:  # 已经大幅上涨
                return 0.3  # 周期后期
            elif price_change > 0.03:  # 温和上涨
                return 0.6  # 周期中期
            else:
                return 0.8  # 周期早期
                
        except:
            return 0.5
    
    def _calculate_long_term_trend_strength(self, stock_df: pd.DataFrame, date: datetime) -> float:
        """计算长期趋势强度"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(200)
            if len(recent_data) < 50:
                return 0.0
            
            # 200日均线趋势
            ma200 = recent_data['收盘'].rolling(200).mean().iloc[-1]
            current_price = recent_data.iloc[-1]['收盘']
            trend_strength = (current_price - ma200) / ma200
            
            return max(0, min(1, trend_strength * 2))
            
        except:
            return 0.0
    
    def _check_technical_breach(self, stock_df: pd.DataFrame, date: datetime, max_days: int = 3) -> float:
        """检查技术破位（3天规则）"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(10)
            if len(recent_data) < 5:
                return 0.0
            
            # 检查是否跌破关键支撑位（简化：20日均线）
            ma20 = recent_data['收盘'].rolling(20).mean()
            current_price = recent_data.iloc[-1]['收盘']
            ma20_current = ma20.iloc[-1]
            
            if current_price < ma20_current * 0.95:  # 跌破5%
                # 检查破位持续天数
                breach_days = 0
                for i in range(len(recent_data)-1, max(-1, len(recent_data)-max_days-1), -1):
                    price = recent_data.iloc[i]['收盘']
                    ma20_val = ma20.iloc[i] if i < len(ma20) else ma20_current
                    if price < ma20_val * 0.95:
                        breach_days += 1
                    else:
                        break
                
                # 破位天数越多，评分越低
                return min(1, breach_days / max_days)
            else:
                return 0.0
                
        except:
            return 0.0
    
    def _calculate_recent_volatility(self, stock_df: pd.DataFrame, date: datetime, window: int = 10) -> float:
        """计算近期波动率"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(window)
            if len(recent_data) < 5:
                return 0.0
            
            returns = recent_data['收盘'].pct_change().dropna()
            return returns.std()
            
        except:
            return 0.0
    
    def _calculate_historical_volatility(self, stock_df: pd.DataFrame, date: datetime, window: int = 60) -> float:
        """计算历史波动率"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(window)
            if len(recent_data) < 20:
                return 0.0
            
            returns = recent_data['收盘'].pct_change().dropna()
            return returns.std()
            
        except:
            return 0.0
    
    def _calculate_short_term_momentum(self, stock_df: pd.DataFrame, date: datetime, window: int = 5) -> float:
        """计算短期动量"""
        try:
            recent_data = stock_df[stock_df['日期'] <= date].tail(window)
            if len(recent_data) < 2:
                return 0.0
            
            momentum = (recent_data.iloc[-1]['收盘'] - recent_data.iloc[0]['收盘']) / recent_data.iloc[0]['收盘']
            return max(0, min(1, momentum * 5))
            
        except:
            return 0.0

# 测试函数
def test_refined_strategies():
    """测试精细化策略定义"""
    refined = RefinedStrategyDefinitions()
    
    # 创建测试数据
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    test_data = pd.DataFrame({
        '日期': dates,
        '开盘': np.random.randn(100).cumsum() + 100,
        '收盘': np.random.randn(100).cumsum() + 100,
        '最高': np.random.randn(100).cumsum() + 105,
        '最低': np.random.randn(100).cumsum() + 95,
        '成交量': np.random.randint(1000000, 10000000, 100),
        '成交额': np.random.randint(100000000, 1000000000, 100),
        '振幅': np.random.rand(100) * 5,
        '涨跌幅': np.random.randn(100) * 2,
        '涨跌额': np.random.randn(100) * 2,
        '换手率': np.random.rand(100) * 10
    })
    
    test_date = dates[-1]
    
    # 测试各策略评分
    value_score = refined.calculate_value_score_refined(test_data, test_date)
    industry_score = refined.calculate_industry_score_refined(test_data, test_date, industry_name='白酒')
    emotion_score = refined.calculate_emotion_score_refined(test_data, test_date)
    trend_score = refined.calculate_trend_score_refined(test_data, test_date)
    quant_score = refined.calculate_quant_score_refined(test_data, test_date)
    
    print("=== 精细化策略评分测试 ===")
    print(f"价值策略: {value_score:.3f}")
    print(f"产业策略: {industry_score:.3f}")
    print(f"情绪策略: {emotion_score:.3f}")
    print(f"趋势策略: {trend_score:.3f}")
    print(f"量化策略: {quant_score:.3f}")

if __name__ == "__main__":
    test_refined_strategies()
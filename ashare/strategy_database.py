#!/usr/bin/env python3
"""
策略数据库管理模块
- 为五类策略建立独立的数据库
- 支持策略评分、历史记录和回测
"""

import json
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

class StrategyDatabase:
    """策略数据库管理类"""
    
    def __init__(self, base_path: str = "/Users/blastai/.openclaw/workspace-0011ai/ashare/strategy_db"):
        self.base_path = base_path
        self.strategies = ['value', 'industry', 'emotion', 'trend', 'quant']
        self._init_database()
    
    def _init_database(self):
        """初始化策略数据库目录结构"""
        os.makedirs(self.base_path, exist_ok=True)
        
        for strategy in self.strategies:
            strategy_path = os.path.join(self.base_path, strategy)
            os.makedirs(strategy_path, exist_ok=True)
            
            # 创建策略配置文件
            config = {
                'name': strategy,
                'description': self._get_strategy_description(strategy),
                'factors': self._get_strategy_factors(strategy),
                'weight': 0.2,  # 初始权重
                'last_updated': None
            }
            
            config_path = os.path.join(strategy_path, 'config.json')
            if not os.path.exists(config_path):
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
    
    def _get_strategy_description(self, strategy: str) -> str:
        """获取策略描述"""
        descriptions = {
            'value': '价值策略：基于绝对现金流和低位估值溢价进行打分排序',
            'industry': '产业策略：基于产业景气度，寻找高景气行业中表现好的标的',
            'emotion': '情绪策略：结合动量和趋势，通过连板和板块效应突破标的',
            'trend': '趋势策略：结合情绪和产业策略中走势具备明显趋势且处于趋势下沿的高评分标的',
            'quant': '量化策略：做空波动率方向，主要针对反核和情绪策略中的低吸标的'
        }
        return descriptions.get(strategy, f'{strategy}策略')
    
    def _get_strategy_factors(self, strategy: str) -> List[str]:
        """获取策略因子列表"""
        factors = {
            'value': ['cash_flow', 'pe_ratio', 'pb_ratio', 'dividend_yield', 'roe'],
            'industry': ['industry_momentum', 'sector_ranking', 'policy_support', 'growth_rate'],
            'emotion': ['momentum_score', 'volume_surge', 'limit_up_count', 'sector_effect'],
            'trend': ['trend_strength', 'support_level', 'moving_averages', 'breakout_potential'],
            'quant': ['volatility_score', 'mean_reversion', 'contrarian_signal', 'low_absorption']
        }
        return factors.get(strategy, [])
    
    def save_stock_scores(self, strategy: str, stock_scores: Dict[str, Any], date: str = None):
        """保存股票策略评分"""
        if strategy not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        scores_path = os.path.join(self.base_path, strategy, f'scores_{date}.json')
        with open(scores_path, 'w', encoding='utf-8') as f:
            json.dump(stock_scores, f, ensure_ascii=False, indent=2)
        
        # 更新最后更新时间
        config_path = os.path.join(self.base_path, strategy, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config['last_updated'] = date
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def load_stock_scores(self, strategy: str, date: str = None) -> Dict[str, Any]:
        """加载股票策略评分"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        scores_path = os.path.join(self.base_path, strategy, f'scores_{date}.json')
        if os.path.exists(scores_path):
            with open(scores_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    
    def get_strategy_config(self, strategy: str) -> Dict[str, Any]:
        """获取策略配置"""
        config_path = os.path.join(self.base_path, strategy, 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    
    def update_strategy_weight(self, strategy: str, weight: float):
        """更新策略权重"""
        config_path = os.path.join(self.base_path, strategy, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config['weight'] = weight
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def get_all_strategies_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有策略状态"""
        status = {}
        for strategy in self.strategies:
            config = self.get_strategy_config(strategy)
            status[strategy] = {
                'name': config.get('name', strategy),
                'description': config.get('description', ''),
                'weight': config.get('weight', 0.2),
                'last_updated': config.get('last_updated', 'Never'),
                'factors': config.get('factors', [])
            }
        return status

# 测试函数
def test_strategy_database():
    """测试策略数据库功能"""
    db = StrategyDatabase()
    
    # 测试保存评分
    test_scores = {
        '600000': {'score': 0.85, 'rank': 1, 'factors': {'cash_flow': 0.9, 'pe_ratio': 0.8}},
        '600001': {'score': 0.78, 'rank': 2, 'factors': {'cash_flow': 0.85, 'pe_ratio': 0.7}}
    }
    
    db.save_stock_scores('value', test_scores, '2026-02-22')
    
    # 测试加载评分
    loaded_scores = db.load_stock_scores('value', '2026-02-22')
    print("Loaded scores:", loaded_scores)
    
    # 测试策略状态
    status = db.get_all_strategies_status()
    print("Strategy status:", status)

if __name__ == "__main__":
    test_strategy_database()
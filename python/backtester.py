import pandas as pd
from data_loader import load_data
from stat_engine import calc_all_stats

class BacktestSystem:
    def __init__(self, data_path: str):
        # 1. Load Data
        import logging
        logging.info(f"正在加载数据: {data_path}")
        
        # 优化：Load -> Sort -> Check if stats exist -> Calc Stats if needed
        self.raw_df = load_data(data_path)
        self.raw_df = self.raw_df.sort_values(by='date', ascending=True).reset_index(drop=True)
        
        # 检查是否已经包含统计列（避免重复计算）
        # 检查几个关键的统计列是否存在
        required_stat_cols = ['om_color_0', 'om_color_1', 'freq_color_0_100']
        has_stats = all(col in self.raw_df.columns for col in required_stat_cols)
        
        if has_stats:
            logging.info("检测到数据中已包含统计列，跳过重新计算")
            # 分离原始数据和统计数据
            stat_cols = [col for col in self.raw_df.columns if col.startswith('om_') or col.startswith('freq_')]
            self.stats_df = self.raw_df[stat_cols]
            # 保留原始列
            base_cols = [col for col in self.raw_df.columns if not col.startswith('om_') and not col.startswith('freq_')]
            self.raw_df = self.raw_df[base_cols]
            self.full_df = pd.concat([self.raw_df, self.stats_df], axis=1)
        else:
            logging.info("数据中不包含统计列，开始计算...")
            self.stats_df = calc_all_stats(self.raw_df)
            self.full_df = pd.concat([self.raw_df, self.stats_df], axis=1)
            logging.info("统计列计算完成")
        
        self.period_map = {str(p): i for i, p in enumerate(self.raw_df['period'])}
        
        # Optimization: Convert to records for fast iteration
        self.records = self.full_df.to_dict('records')
        
        logging.info(f"数据加载完成，共 {len(self.raw_df)} 条记录")
        
        # Cache for strategy execution
        self.cached_config = None
        self.cached_states = {} # period -> detailed_state
        self.cached_summary = None

    def _run_full_simulation(self, config):
        """
        Runs the full simulation for the given config and caches the state for EVERY period.
        """
        import time
        start_time = time.time()
        
        if self.cached_config == config and self.cached_states:
             return # Already cached
             
        entry_config = config.get('entry', {})
        money_config = config.get('money', {})
        odds_config = config.get('odds', None)  # 赔率配置（可选）
        
        logging.info(f"[Backtest Config] Odds: {odds_config}")
        
        initial_capital = 10000.0
        capital = initial_capital
        trades = []
        equity_curve = []
        
        current_bet = None 
        mar_step = 0
        
        # We will store state keyed by period string
        # State includes: capital_before, capital_after, current_bet_info, last_trade_result
        states = {}
        
        win_count = 0
        loss_count = 0
        
        # Initialize state for the very first period (no betting possible yet)
        if not self.records:
            return

        first_period = str(self.records[0]['period'])
        states[first_period] = {
            "capital": capital,
            "accumulated_profit": 0,
            "win_rate": 0,
            "total_trades": 0,
            "betting": None, # {target: "...", amount: 10}
            "result": None   # {profit: 10, is_hit: True}
        }

        # Optimization: Iterate over pre-converted records
        for i in range(1, len(self.records)):
            row = self.records[i]
            prev_row = self.records[i-1]
            period = str(row['period'])
            
            # Info for this period
            period_bet_info = None
            period_trade_result = None
            
            # 1. Check active bet result
            if current_bet:
                actual_val = row.get(f"sp_{current_bet['target_dim']}")
                # Ensure type match if needed, but dict values should be correct types from to_dict
                is_hit = (actual_val == current_bet['target_val'])
                
                profit = 0
                if is_hit:
                    odds = self._get_odds(current_bet['target_dim'], odds_config)
                    profit = current_bet['amount'] * (odds - 1)
                    capital += profit
                    
                    period_trade_result = {
                        "is_hit": True,
                        "profit": round(profit, 2),
                        "amount": current_bet['amount']
                    }
                    trades.append(period_trade_result)
                    win_count += 1
                    
                    current_bet = None # Stop Profit
                    mar_step = 0
                else:
                    profit = -current_bet['amount']
                    capital += profit
                    
                    period_trade_result = {
                        "is_hit": False,
                        "profit": round(profit, 2),
                        "amount": current_bet['amount']
                    }
                    trades.append(period_trade_result)
                    loss_count += 1
                    
                    # Martingale
                    if money_config.get('mode') == 'martingale':
                        multipliers = money_config.get('params', {}).get('multipliers', [])
                        mar_step += 1
                        if mar_step < len(multipliers):
                            next_amount = money_config['params']['baseBet'] * multipliers[mar_step]
                            current_bet['amount'] = next_amount
                        else:
                            current_bet = None # Stop Loss (Max Level)
                            mar_step = 0
            
            # 2. If no active bet, check entry (for NEXT period)
            # The bet decided here will be placed for period i+1, so we record it as 'pending' for i?
            # Actually, the UI usually shows "What are we betting ON THIS PERIOD".
            # If current_bet is NOT None at this point, it means we are CARRYING OVER a bet to the next period.
            # If current_bet IS None, we look for a NEW bet.
            
            if current_bet is None:
                if self._check_entry(prev_row, entry_config):
                    cond = entry_config['conditions'][0]
                    dim = cond['dimension']
                    val = self._get_target_info(dim, cond['value'])
                    amount = money_config.get('params', {}).get('baseBet', 10)
                    
                    current_bet = {
                        "target_dim": dim,
                        "target_val": val,
                        "amount": amount
                    }
                    mar_step = 0
            
            # Record state currently
            # Note: 'current_bet' now represents what is active for the NEXT period (or carried over).
            # But for display, if we are at period T, users want to know:
            # - Did we win/lose locally at T? (period_trade_result)
            # - What is our accumulated status at T?
            # - What are we betting for T+1? (current_bet)
            
            total_trades = win_count + loss_count
            win_rate = win_count / total_trades if total_trades > 0 else 0
            
            bet_display = None
            if current_bet:
                 # Translate internal val back to display? Or just keep simple
                 # We can store raw for now
                 bet_display = {
                     "target": f"{current_bet['target_dim']}:{current_bet['target_val']}", 
                     "amount": current_bet['amount'],
                     "step": mar_step
                 }

            states[period] = {
                "capital": round(capital, 2),
                "accumulated_profit": round(capital - initial_capital, 2),
                "win_rate": round(win_rate, 4),
                "total_trades": total_trades,
                "betting": bet_display,
                "result": period_trade_result
            }
            
            if i % 10 == 0 or i == len(self.records) - 1:
                equity_curve.append({"period": period, "capital": round(capital, 2)})
        
        elapsed = time.time() - start_time
        import logging
        logging.info(f"Backtest simulation completed in {elapsed:.4f}s")
        
        self.cached_config = config
        self.cached_states = states
        self.cached_summary = {
            "initial_capital": initial_capital,
            "final_capital": round(capital, 2),
            "total_profit": round(capital - initial_capital, 2),
            "total_trades": len(trades),
            "win_rate": round(sum(1 for t in trades if t['is_hit']) / len(trades), 4) if trades else 0,
            "trades": trades[-50:],
            "curve": equity_curve
        }

    def _get_signal_evaluation(self, config, prev_idx):
        prev_row = self.full_df.iloc[prev_idx]
        entry_config = config.get('entry', {})
        triggered, details = self._check_entry_detailed(prev_row, entry_config)
        return {
            "triggered": bool(triggered),
            "conditions": details
        }
    
    def get_data_stats(self):
        """
        返回已加载数据的元数据。
        """
        periods = self.raw_df['period'].astype(str).tolist()
        if not periods:
            return {"count": 0, "min_period": None, "max_period": None}
            
        return {
            "count": len(periods),
            "min_period": periods[0],
            "max_period": periods[-1],
            "periods": periods,
            "dates": self.raw_df['date'].dt.strftime('%Y-%m-%d').tolist() 
        }

    def _get_target_info(self, dim, val):
        # 将前端值映射到后端索引
        if dim == 'color':
            m = {'red': 0, 'blue': 1, 'green': 2}
            return m.get(val, 0)
        if dim == 'size':
            return 1 if val == 'big' else 0
        if dim == 'parity':
            return 1 if val == 'odd' else 0
        if dim == 'zodiac':
            names = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
            if val in names:
                return names.index(val)
        if dim == 'tail':
            return int(val)
        return val

    def _check_condition(self, row, cond):
        ctype = cond.get('type')
        dim = cond.get('dimension')
        
        # 从行中获取实际值
        val_name = None
        if ctype == 'omission':
            target_idx = self._get_target_info(dim, cond.get('value'))
            val_name = f"om_{dim}_{target_idx}"
        elif ctype == 'window_stat':
            target_idx = self._get_target_info(dim, cond.get('value'))
            val_name = f"freq_{dim}_{target_idx}_100" # 暂简化为 100 窗口
            
        if val_name and val_name in row:
            actual = row[val_name]
            op = cond.get('operator')
            threshold = cond.get('threshold')
            passed = False
            if op == '>=': passed = actual >= threshold
            elif op == '<=': passed = actual <= threshold
            elif op == '==': passed = actual == threshold
            elif op == '>': passed = actual > threshold
            elif op == '<': passed = actual < threshold
            
            return bool(passed), {
                "desc": f"{dim} {ctype}",
                "actual": float(actual),
                "threshold": float(threshold),
                "operator": op,
                "passed": bool(passed)
            }
        return False, {"desc": "Unknown Condition", "passed": False}

    def _check_entry(self, row, config):
        # Legacy support for backtest run (returns boolean)
        triggered, _ = self._check_entry_detailed(row, config)
        return triggered

    def _check_entry_detailed(self, row, config):
        conditions = config.get('conditions', [])
        if not conditions: return False, []
        
        op = config.get('logicOperator', 'AND')
        results = [self._check_condition(row, c) for c in conditions]
        # results is list of (bool, dict)
        
        passed_list = [r[0] for r in results]
        details_list = [r[1] for r in results]
        
        triggered = False
        if op == 'AND': triggered = all(passed_list)
        if op == 'OR': triggered = any(passed_list)
        
        return triggered, details_list

    def _get_odds(self, dim, odds_config=None):
        """
        获取赔率。如果有配置则使用配置值，否则使用默认值。
        odds_config: { playType: 'special_color', odds: 2.8, ... }
        """
        import logging
        # 如果有配置赔率且玩法类型匹配，使用配置值
        if odds_config:
            play_type = odds_config.get('playType', '')
            # logic to map dimension to playType
            type_map = {
                'color': 'special_color',
                'zodiac': 'special_zodiac',
                'size': 'special_size',
                'parity': 'special_parity',
                'number': 'special_number',
                'tail': 'special_tail'
            }
            mapped_type = type_map.get(dim)
            if mapped_type == play_type:
                custom = float(odds_config.get('odds', 2.0))
                logging.info(f"[Odds] MATCH: dim={dim}, odds={custom}")
                return custom
            else:
                logging.info(f"[Odds] SKIP: dim={dim}({mapped_type}) != config={play_type}")
                pass

        
        # 默认赔率（含本金）
        if dim == 'color': return 2.8
        if dim == 'zodiac': return 11.0
        if dim == 'size' or dim == 'parity': return 1.9
        if dim == 'tail': return 9.8 # 默认尾数赔率
        return 2.0

    def get_replay_state(self, period: str, strategy_config: dict = None):
        """
        Get state for replay. 
        If strategy_config is provided, we ensure the simulation is run/cached for that strategy,
        then pull the specific state for the period.
        """
        import logging
        logging.info(f"获取回放状态: period={period}")
        
        if period not in self.period_map:
            raise ValueError(f"期数 {period} 未找到。")
            
        idx = self.period_map[period]
        row = self.full_df.iloc[idx]
        
        # 1. Base Data
        result = {
            "period": row['period'],
            "date": row['date'].strftime('%Y-%m-%d'),
            "special": int(row['special']),
            "color": int(row['sp_color']),
            "zodiac": int(row['sp_zodiac']),
            "numbers": [int(row[f'n{i}']) for i in range(1, 7)]
        }
        
        stats = {
            "omission": {},
            "freq_100": {}
        }
        
        # 安全地访问统计列，如果不存在则使用默认值
        try:
            for c in [0, 1, 2]:
                stats["omission"][f"color_{c}"] = int(row.get(f"om_color_{c}", 0))
                stats["freq_100"][f"color_{c}"] = int(row.get(f"freq_color_{c}_100", 0))
            for z in range(12):
                stats["omission"][f"zodiac_{z}"] = int(row.get(f"om_zodiac_{z}", 0))
                stats["freq_100"][f"zodiac_{z}"] = int(row.get(f"freq_zodiac_{z}_100", 0))
                
            # Add new stats: Size, Parity, Tail
            for s in [0, 1]:
                stats["omission"][f"size_{s}"] = int(row.get(f"om_size_{s}", 0))
                stats["freq_100"][f"size_{s}"] = int(row.get(f"freq_size_{s}_100", 0))
                
            for p in [0, 1]:
                stats["omission"][f"parity_{p}"] = int(row.get(f"om_parity_{p}", 0))
                stats["freq_100"][f"parity_{p}"] = int(row.get(f"freq_parity_{p}_100", 0))

            for t in range(10):
                stats["omission"][f"tail_{t}"] = int(row.get(f"om_tail_{t}", 0))
                stats["freq_100"][f"tail_{t}"] = int(row.get(f"freq_tail_{t}_100", 0))
        except Exception as e:
            logging.error(f"读取统计列时出错: {e}")
            logging.error(f"可用列: {list(row.index)}")
            # 继续执行，使用空的统计数据

        # 2. Strategy Data
        accumulated_stats = None
        betting_status = None
        signal_evaluation = None
        
        if strategy_config:
            # Ensure simulation is run
            self._run_full_simulation(strategy_config)
            
            # Fetch state from cache
            state_data = self.cached_states.get(str(period))
            
            if state_data:
                accumulated_stats = {
                    "capital": state_data['capital'],
                    "profit": state_data['accumulated_profit'],
                    "win_rate": state_data['win_rate'],
                    "total_trades": state_data['total_trades']
                }
                
                # Check previous period's betting to see what we did THIS period (result)
                # state_data['result'] is the result of the bet placed in PREV period, resolved in THIS period.
                last_result = state_data['result']
                
                # state_data['betting'] is the bet placed in THIS period for the NEXT period.
                next_bet = state_data['betting']
                
                betting_status = {
                    "last_result": last_result, # {is_hit, profit, amount}
                    "next_bet": next_bet        # {target, amount, step}
                }
                
            # Signal Evaluation (Condition Details)
            # This logic mimics whether we WOULD enter if we were starting fresh, 
            # or simply explains the entry conditions for the next bet.
            if idx > 0:
                 signal_evaluation = self._get_signal_evaluation(strategy_config, idx - 1)

        return {
            "period": period,
            "result": result,
            "stats": stats,
            "accumulated_stats": accumulated_stats,
            "betting_status": betting_status,
            "signal_evaluation": signal_evaluation
        }

    def run_backtest(self, config: dict):
        self._run_full_simulation(config)
        return self.cached_summary

if __name__ == "__main__":
    import sys
    path = r'f:\demo\mark-six\app\data\history.feather'
    bs = BacktestSystem(path)

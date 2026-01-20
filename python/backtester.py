import pandas as pd
import logging
import sys
from data_loader import load_data
from stat_engine import calc_all_stats

class BacktestSystem:
    def __init__(self, data_path: str):
        # 1. Load Data
        logging.info(f"正在加载数据: {data_path}")
        
        # 优化：Load -> Sort -> Check if stats exist -> Calc Stats if needed
        self.raw_df = load_data(data_path)
        self.raw_df = self.raw_df.sort_values(by='date', ascending=True).reset_index(drop=True)
        
        # 检查是否已经包含统计列（避免重复计算）
        # 检查关键的统计列是否存在 (Check for ALL dimensions to ensure completeness)
        required_stat_cols = [
            'om_color_0', 'om_zodiac_0', 
            'om_size_0', 'om_parity_0', 'om_tail_0'
        ]
        # Only check existence, assuming if one exists, the group exists
        has_stats = all(col in self.raw_df.columns for col in required_stat_cols)
        
        if has_stats:
            logging.info("检测到数据中已包含所有统计列，跳过重新计算")
            # 分离原始数据和统计数据
            stat_cols = [col for col in self.raw_df.columns if col.startswith('om_') or col.startswith('freq_')]
            self.stats_df = self.raw_df[stat_cols]
            # 保留原始列
            base_cols = [col for col in self.raw_df.columns if not col.startswith('om_') and not col.startswith('freq_')]
            self.raw_df = self.raw_df[base_cols]
            self.full_df = pd.concat([self.raw_df, self.stats_df], axis=1)
        else:
            logging.info("数据中缺少部分统计列 (可能是旧缓存)，开始重新计算...")
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

    def _determine_target_condition(self, conditions):
        """
        From a list of triggering conditions, determine which one defines the betting target.
        Heuristic: Choose the most specific dimension (Number > Zodiac > Tail > Color > Parity/Size).
        """
        if not conditions:
            return None
            
        dim_priority = {
            'number': 10,
            'zodiac': 8,   # 1/12
            'tail': 7,     # 1/10
            'color': 5,    # 1/3
            'size': 2,     # 1/2
            'parity': 2    # 1/2
        }
        
        best_cond = conditions[0]
        max_p = dim_priority.get(best_cond.get('dimension'), 0)
        
        for cond in conditions[1:]:
            p = dim_priority.get(cond.get('dimension'), 0)
            if p > max_p:
                max_p = p
                best_cond = cond
                
        return best_cond

    def _run_full_simulation(self, config):
        """
        Runs the full simulation for the given config and caches the state for EVERY period.
        """
        import time
        start_time = time.time()
        
        # if self.cached_config == config and self.cached_states:
        #      return # Already cached
             
        entry_config = config.get('entry', {})
        money_config = config.get('money', {})
        odds_config = config.get('odds', None)  # 赔率配置（可选）
        
        logging.info(f"--- Starting Simulation ---")
        logging.info(f"Money Mode: {money_config.get('mode')}")
        logging.info(f"Money Params: {money_config.get('params')}")
        logging.info(f"Odds Config: {odds_config}")
        
        logging.info(f"[Backtest Config] Odds: {odds_config}")
        
        initial_capital = 10000.0
        capital = initial_capital
        trades = []
        equity_curve = []
        
        current_bet = None 
        mar_step = 0
        current_bet = None 
        mar_step = 0
        accumulated_loss = 0
        
        # New Metrics
        max_single_bet = 0
        max_streak_cost = 0
        current_streak_cost = 0
        
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
            period_bet_info = None
            period_trade_result = None
            
            # --- New: Track Metrics BEFORE processing result (so we count Winning bets too) ---
            if current_bet:
                amount = float(current_bet.get('amount', 0))
                max_single_bet = max(max_single_bet, amount)
                max_streak_cost = max(max_streak_cost, current_streak_cost + amount)
            # ----------------------------------------------------------------------------------
            
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
                        "period": period,
                        "is_hit": True,
                        "profit": round(profit, 2),
                        "amount": current_bet['amount']
                    }
                    trades.append(period_trade_result)
                    win_count += 1
                    
                    current_bet = None # Stop Profit
                    mar_step = 0
                    current_bet = None # Stop Profit
                    mar_step = 0
                    accumulated_loss = 0
                    current_streak_cost = 0
                else:
                    profit = -current_bet['amount']
                    capital += profit
                    
                    period_trade_result = {
                        "period": period,
                        "is_hit": False,
                        "profit": round(profit, 2),
                        "amount": current_bet['amount']
                    }
                    trades.append(period_trade_result)
                    loss_count += 1
                    
                    # Update streak cost (for this loss)
                    # Note: accumulated_loss for Loss Recovery mode logic handles sum of previous losses.
                    # But generically for all modes, 'current_streak_cost' tracks money sunk in current losing streak.
                    # It should include the bet just lost.
                    current_streak_cost += current_bet['amount']
                    max_streak_cost = max(max_streak_cost, current_streak_cost)
                    
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
                            
                    # Loss Recovery (Smart Chase)
                    elif money_config.get('mode') == 'loss_recovery':
                        accumulated_loss += float(current_bet['amount'])
                        
                        # Calculate required bet to recover loss + target profit (baseBet)
                        # Formula: Bet = (Loss + Profit) / (Odds - 1)
                        next_odds = self._get_odds(current_bet['target_dim'], odds_config)
                        try:
                            target_profit = float(money_config.get('params', {}).get('baseBet', 10))
                        except:
                            target_profit = 10.0
                        
                        if next_odds > 1:
                            raw_next = (accumulated_loss + target_profit) / (next_odds - 1)
                            # Round to integer or 1 decimal? Usually money is 2 decimals?
                            # Mark Six usually integers? Let's keep 2 decimals for accuracy then maybe UI floors it.
                            next_amount = round(raw_next, 2)
                            
                            # Ensure minimum bet (at least 1 or baseBet?)
                            # Strategy: Should we floor at 1?
                            if next_amount < 1: next_amount = 1.0

                            # Max Bet Check
                            max_bet = money_config.get('params', {}).get('maxBet')
                            if max_bet:
                                try:
                                    max_bet = float(max_bet)
                                    if next_amount > max_bet:
                                        logging.info(f"Loss Recovery Stop Loss: Required {next_amount} > Max {max_bet}")
                                        current_bet = None # Stop Loss
                                        accumulated_loss = 0
                                        next_amount = 0 # for safety
                                except:
                                    pass # Ignore bad max_bet

                            if current_bet:
                                current_bet['amount'] = next_amount
                                logging.info(f"Loss Recalc: Loss={accumulated_loss}, Tgt={target_profit}, Odds={next_odds} -> Next={next_amount}")
                        else:
                            # Should not happen with valid odds, but safety break
                            current_bet = None
                            accumulated_loss = 0

            
            # 2. If no active bet, check entry (for NEXT period)
            # We check the CURRENT period stats (row) to see if we should bet on the NEXT period.
            if current_bet is None:
                if self._check_entry(row, entry_config):
                    # Smartly determine the target condition
                    cond = self._determine_target_condition(entry_config.get('conditions', []))
                    if cond:
                        dim = cond['dimension']
                        val = self._get_target_info(dim, cond['value'])
                        amount = money_config.get('params', {}).get('baseBet', 10)
                        
                        current_bet = {
                            "target_dim": dim,
                            "target_val": val,
                            "amount": amount
                        }
                        # If starting fresh streak
                        if current_streak_cost == 0:
                            current_streak_cost = 0 # Just to be explicit, it's 0 until first loss. 
                            # Wait, max_streak_cost exposure includes the current bet.
                            pass
                            
                        mar_step = 0
            
            # Metrics moved to start of loop to capture all bets
            pass

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
                 next_p_str = "Unknown"
                 if i + 1 < len(self.records):
                     next_p_str = str(self.records[i+1]['period'])
                 
                 # Debug logging
                 if i < 10: # Only log for first few to avoid spam, or specific period
                     logging.info(f"DEBUG: Period={period}, NextPeriod={next_p_str}, Idx={i}, Total={len(self.records)}")

                 bet_display = {
                     "period": next_p_str,
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

        logging.info(f"Backtest simulation completed in {elapsed:.4f}s")
        
        self.cached_config = config
        self.cached_states = states
        self.cached_summary = {
            "initial_capital": initial_capital,
            "final_capital": round(capital, 2),
            "total_profit": round(capital - initial_capital, 2),
            "total_trades": len(trades),
            "win_rate": round(sum(1 for t in trades if t['is_hit']) / len(trades), 4) if trades else 0,
            "max_single_bet": round(max_single_bet, 2),
            "max_streak_cost": round(max_streak_cost, 2),
            "trades": trades[-50:],
            "curve": equity_curve
        }

    def _get_signal_evaluation(self, config, current_idx):
        # View stats of THIS period to see if it triggers entry for next
        row = self.full_df.iloc[current_idx]
        entry_config = config.get('entry', {})
        triggered, details = self._check_entry_detailed(row, entry_config)
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

        # Configure logging to ensure it goes to stderr and doesn't break JSON protocol
        logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='[Backtester] %(message)s')

    def _get_target_info(self, dim, val):
        # Robust mapping of frontend values to backend indices
        # Ensure val is stripped if string
        if isinstance(val, str):
            val = val.strip()

        if dim == 'color':
            m = {'red': 0, 'blue': 1, 'green': 2, '红波': 0, '蓝波': 1, '绿波': 2}
            return m.get(val, 0) # Default to 0? Or raise?
        if dim == 'size':
            return 1 if val in ['big', '大'] else 0
        if dim == 'parity':
            return 1 if val in ['odd', '单'] else 0
        if dim == 'zodiac':
            names = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
            if val in names:
                return names.index(val)
            # Try parsing as integer string?
            if isinstance(val, str) and val.isdigit():
                return int(val)
            if isinstance(val, int):
                return val
        if dim == 'tail':
            if isinstance(val, str):
                if val.endswith('尾'): val = val.replace('尾', '')
                return int(val)
            return int(val)
        return val

    def _check_condition(self, row, cond):
        ctype = cond.get('type')
        dim = cond.get('dimension')
        val = cond.get('value')
        
        # Determine actual value column name
        val_name = None
        target_idx = None
        
        try:
            target_idx = self._get_target_info(dim, val)
        except Exception as e:
            return False, {"desc": f"Map Error: {dim}={val}", "passed": False}

        if ctype == 'omission':
            val_name = f"om_{dim}_{target_idx}"
        elif ctype == 'window_stat':
            val_name = f"freq_{dim}_{target_idx}_100" # Simplified to 100 window
            
        if val_name:
            if val_name in row:
                actual = row[val_name]
                op = cond.get('operator')
                threshold = cond.get('threshold')
                
                # Robust type conversion
                try:
                    actual = float(actual)
                    threshold = float(threshold)
                except:
                    pass

                passed = False
                if op == '>=': passed = actual >= threshold
                elif op == '<=': passed = actual <= threshold
                elif op == '==': passed = actual == threshold
                elif op == '>': passed = actual > threshold
                elif op == '<': passed = actual < threshold
                
                return bool(passed), {
                    "desc": f"{dim} {ctype}",
                    "actual": actual,
                    "threshold": threshold,
                    "operator": op,
                    "passed": bool(passed)
                }
            else:
                # Column missing - critical debug info. 
                # Row can be Series or Dict. keys() works for both Series and Dict (in recent pandas)
                # But to be safe, use logic.
                
                keys = []
                if hasattr(row, 'keys'):
                    keys = row.keys()
                elif hasattr(row, 'index'):
                    keys = row.index
                elif isinstance(row, dict):
                     keys = row.keys()
                     
                available_cols = [c for c in keys if c.startswith(f"om_{dim}")]
                return False, {
                    "desc": f"Missing Col: {val_name}",
                    "passed": False,
                    "actual": "N/A",  # Show N/A so it appears in UI
                    "operator": "?",
                    "threshold": "?"
                }
                
        return False, {"desc": f"Unknown Type: {ctype}", "passed": False}

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
                return custom
            else:
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

        logging.info(f"获取回放状态: period={period}")
        
        if period not in self.period_map:
            raise ValueError(f"期数 {period} 未找到。")
            
        idx = self.period_map[period]
        row = self.full_df.iloc[idx]
        
        # 1. Base Data
        # Map for colors to avoid frontend needing to know fixed colors
        COLOR_LOOKUP = {n: (0 if n in {1, 2, 7, 8, 12, 13, 18, 19, 23, 24, 29, 30, 34, 35, 40, 45, 46} else 
                        1 if n in {3, 4, 9, 10, 14, 15, 20, 25, 26, 31, 36, 37, 41, 42, 47, 48} else 2) 
                        for n in range(1, 50)}

        result = {
            "period": row['period'],
            "date": row['date'].strftime('%Y-%m-%d'),
            "special": int(row['special']),
            "color": int(row['sp_color']),
            "zodiac": int(row['sp_zodiac']),
            "size": int(row['sp_size']),
            "parity": int(row['sp_parity']),
            "numbers": [int(row[f'n{i}']) for i in range(1, 7)],
            "numbers_colors": [COLOR_LOOKUP[int(row[f'n{i}'])] for i in range(1, 7)]
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
            logging.error(f"可用列: {list(row.keys()) if hasattr(row,'keys') else 'NoKeys'}")
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
                    "total_trades": state_data['total_trades'],
                    "max_single_bet": self.cached_summary.get('max_single_bet', 0) if self.cached_summary else 0,
                    "max_streak_cost": self.cached_summary.get('max_streak_cost', 0) if self.cached_summary else 0
                }
                
                # Check previous period's betting to see what we did THIS period (result)
                # state_data['result'] is the result of the bet placed in PREV period, resolved in THIS period.
                last_result = state_data['result']
                
                # state_data['betting'] is the bet placed in THIS period for the NEXT period.
                next_bet = state_data['betting']
                
                # Robustness: Ensure period is set
                if next_bet:
                    if 'period' not in next_bet or next_bet['period'] == 'Unknown':
                        if idx + 1 < len(self.full_df):
                            try:
                                next_bet['period'] = str(self.full_df.iloc[idx+1]['period'])
                            except:
                                pass

                betting_status = {
                    "last_result": last_result, # {is_hit, profit, amount}
                    "next_bet": next_bet        # {target, amount, step}
                }
                
            # Signal Evaluation (Condition Details)
            # This logic mimics whether we WOULD enter if we were starting fresh, 
            # or simply explains the entry conditions for the next bet.
            if idx >= 0:
                 signal_evaluation = self._get_signal_evaluation(strategy_config, idx)

        return {
            "period": period,
            "result": result,
            "stats": stats,
            "accumulated_stats": accumulated_stats,
            "betting_status": betting_status,
            "signal_evaluation": signal_evaluation,
            "history_orders": self.cached_summary.get('trades', [])[-100:] if self.cached_summary else []
        }

    def run_backtest(self, config: dict):
        self._run_full_simulation(config)
        return self.cached_summary

if __name__ == "__main__":
    import sys
    path = r'f:\demo\mark-six\app\data\history.feather'
    bs = BacktestSystem(path)

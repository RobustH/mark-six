import sys
import json
import time
import os
import traceback
from backtester import BacktestSystem

# 全局变量存储回测系统实例
backtest_system = None

import numpy as np
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, (np.bool_, np.bool)):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, 'item'):
            return obj.item()
        return super(NumpyEncoder, self).default(obj)

def log(msg):
    # 将日志输出到 stderr，以免干扰 stdout 的通信
    # Explicitly encode to utf-8 if needed, but stderr usually handles it.
    # On Windows console it might be tricky, but for file redirection/pipe it should be fine.
    try:
        sys.stderr.write(f"[Python] {msg}\n")
        sys.stderr.flush()
    except Exception:
        pass # Ignore logging errors

def handle_load_data(params):
    global backtest_system
    file_path = params.get("file_path", "")
    log(f"Loading data from: {file_path}")
    
    if not os.path.exists(file_path):
        return {"status": "error", "message": "File not found"}
    
    try:
        backtest_system = BacktestSystem(file_path)
        return {
            "status": "success", 
            "message": f"Loaded {len(backtest_system.raw_df)} records",
            "count": len(backtest_system.raw_df)
        }
    except Exception as e:
        log(f"Failed to load data: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        return {"status": "error", "message": f"Data Load Error: {str(e)}"}

def handle_run_backtest(params):
    global backtest_system
    if not backtest_system:
         return {"status": "error", "message": "Data not loaded"}
         
    log("Running backtest strategy...")
    strategy_config = params # params is the config object directly? Or params['entry'] etc.
    # Check wrapper from frontend
    
    try:
        result = backtest_system.run_backtest(strategy_config)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        log(f"Backtest error: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        return {"status": "error", "message": str(e)}

def handle_get_replay_state(params):
    global backtest_system
    if not backtest_system:
         return {"status": "error", "message": "Data not loaded"}
         
    period = params.get("period")
    strategy_config = params.get("strategy_config")
    
    try:
        state = backtest_system.get_replay_state(period, strategy_config)
        return {
            "status": "success",
            "data": state 
        }
    except Exception as e:
        log(f"Replay Error: {e}")
        traceback.print_exc(file=sys.stderr)
        return {"status": "error", "message": str(e)}

def handle_get_data_stats(params):
    global backtest_system
    if not backtest_system:
         return {"status": "error", "message": "Data not loaded"}
         
    try:
        stats = backtest_system.get_data_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def process_command(line):
    try:
        data = json.loads(line)
        cmd = data.get("cmd")
        params = data.get("params", {})
        req_id = data.get("request_id")
        
        log(f"Received command: {cmd}")
        
        response_payload = None
        status = "ok"
        message = ""
        
        if cmd == "load_data":
            res = handle_load_data(params)
            if res['status'] == 'error':
                status = 'error'
                message = res['message']
            else:
                response_payload = res 
                
        elif cmd == "run_backtest":
            res = handle_run_backtest(params)
            if res['status'] == 'error':
                 status = 'error'
                 message = res['message']
            else:
                 response_payload = res.get('result')

        elif cmd == "get_replay_state":
            res = handle_get_replay_state(params)
            if res['status'] == 'error':
                 status = 'error'
                 message = res['message']
            else:
                 response_payload = res.get('data')

        elif cmd == "get_data_stats":
            res = handle_get_data_stats(params)
            if res['status'] == 'error':
                 status = 'error'
                 message = res['message']
            else:
                 response_payload = res.get('data')

        else:
            status = "error"
            message = f"Unknown command: {cmd}"
            
        # Construct Flat Response for python.ts
        response = {
            "request_id": req_id,
            "status": status,
            "message": message,
            "data": response_payload
        }
        
        # 打印 JSON 到 stdout，供 Rust 端读取
        print(json.dumps(response, cls=NumpyEncoder))
        sys.stdout.flush()
        
    except json.JSONDecodeError:
        log("Invalid JSON received")
    except Exception as e:
        log(f"Error processing command: {str(e)}")
        traceback.print_exc(file=sys.stderr)

def main():
    # Force UTF-8 for stdin/stdout to handle Chinese characters correctly on Windows
    if sys.platform.startswith('win'):
        try:
            sys.stdin.reconfigure(encoding='utf-8')
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception as e:
            # Fallback or older python version
            pass

    log("Mark Six Python Engine Started (Real Backend)")
    log(f"CWD: {os.getcwd()}")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if line:
                process_command(line)
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"Fatal loop error: {e}")
            break

if __name__ == "__main__":
    main()

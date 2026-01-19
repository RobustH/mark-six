import sys
import json
import time
import os
import traceback

# 尝试导入数据处理库，如果不存在则使用模拟数据或基础功能
try:
    import pandas as pd
except ImportError:
    pd = None

def log(msg):
    # 将日志输出到 stderr，以免干扰 stdout 的通信
    sys.stderr.write(f"[Python] {msg}\n")
    sys.stderr.flush()

def handle_load_data(params):
    file_path = params.get("file_path", "")
    log(f"Loading data from: {file_path}")
    
    if not os.path.exists(file_path):
        return {"status": "error", "message": "File not found"}
    
    # 这里可以添加实际的加载逻辑，例如使用 pandas 读取 feather 或 csv
    if pd and file_path.endswith(".feather"):
        try:
            df = pd.read_feather(file_path)
            return {
                "status": "success", 
                "message": f"Loaded {len(df)} records",
                "preview": df.head().to_dict(orient="records")
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return {"status": "success", "message": "Mock load success"}

def handle_run_backtest(params):
    log("Running backtest strategy...")
    strategy_config = params.get("strategy_config", {})
    
    # 模拟回测过程
    time.sleep(1) # 模拟计算耗时
    
    return {
        "status": "success",
        "result": {
            "total_trades": 100,
            "win_rate": 0.55,
            "total_profit": 1200
        }
    }

def handle_get_replay_state(params):
    return {
        "status": "success",
        "state": {
            "current_period": "2024001",
            "is_playing": False,
            "speed": 1.0
        }
    }

def handle_get_data_stats(params):
    return {
        "status": "success",
        "stats": {
            "omission": {},
            "hot_cold": {}
        }
    }

def process_command(line):
    try:
        data = json.loads(line)
        cmd = data.get("cmd")
        params = data.get("params", {})
        req_id = data.get("request_id")
        
        log(f"Received command: {cmd}")
        
        response_data = None
        
        if cmd == "load_data":
            response_data = handle_load_data(params)
        elif cmd == "run_backtest":
            response_data = handle_run_backtest(params)
        elif cmd == "get_replay_state":
            response_data = handle_get_replay_state(params)
        elif cmd == "get_data_stats":
            response_data = handle_get_data_stats(params)
        else:
            response_data = {"status": "error", "message": f"Unknown command: {cmd}"}
            
        # 构造标准响应格式
        response = {
            "request_id": req_id,
            "type": "response", # 标识这是通过 IPC 返回的响应
            "data": response_data
        }
        
        # 打印 JSON 到 stdout，供 Rust 端读取
        print(json.dumps(response))
        sys.stdout.flush()
        
    except json.JSONDecodeError:
        log("Invalid JSON received")
    except Exception as e:
        log(f"Error processing command: {str(e)}")
        traceback.print_exc(file=sys.stderr)

def main():
    log("Mark Six Python Engine Started")
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

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
    sys.stderr.write(f"[Python] {msg}\n")
    sys.stderr.flush()

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
            "data": state  # The frontend expects 'data' prop directly for this command response wrapper? 
                           # Actually python.ts returns 'data' field of response.
                           # Let's check python.ts: 
                           # const res = await callPython('get_replay_state', params);
                           # if (res && res.status === 'ok') { currentState.value = res.data; }
                           # So we should return { status: 'success', data: ... }
                           # My unified handler below wraps it: { request_id:..., type:..., data: response_data }
                           # So response_data SHOULD be just the payload?
                           # No. python.ts `resp = JSON.parse(trimmed)`. 
                           # Wait. `invoke` in Rust returns `Result<Value, String>`.
                           # The Rust command reads line from stdout.
                           # The `python-response` event payload IS the line from stdout.
                           # `python.ts`: const resp = JSON.parse(line).
                           # resp struct: { status, data, message, request_id }
                           # So my response_data here must CONFORM to that struct partially?
                           # No. `process_command` wraps `response_data` into `data` field?
                           # Let's look at `process_command` in original main.py:
                           # response = { "request_id": req_id, "type": "response", "data": response_data }
                           # THIS is what `python.ts` parses? 
                           # No, `python.ts`: `interface PythonResponse { status: ..., data: ... }`
                           # Actually `python.ts` parses the line directly. 
                           # The `python-response` event is just the string line.
                           # So the JSON printed by Python MUST MATCH `PythonResponse` interface.
                           # status: 'ok'|'error'
                           
                           # The original `main.py` wrapper:
                           # response = { "request_id": req_id, "type": "response", "data": response_data }
                           # BUT `python.ts` expects `resp.request_id` at top level.
                           # And `resp.status`.
                           # So `response_data` (which has "status") is nested in "data"? 
                           # or is the "data" field in `python.ts` actually the `response_data`?
                           
                           # Let's re-read python.ts handle loop:
                           # const resp = JSON.parse(trimmed) as PythonResponse;
                           # if (resp.request_id ...)
                           
                           # So the JSON printed by Python MUST be:
                           # { "request_id": "...", "status": "ok", "data": { ... } }
                           
                           # But `process_command` in `main.py` was doing:
                           # response = { "request_id": ..., "type": ..., "data": response_data }
                           # And `response_data` returned by handle functions was { "status": "success", "result": ... }
                           
                           # This implies `python.ts` might be mismatching or I misread `python.ts`.
                           # checking python.ts again.
                           # interface PythonResponse { status, data, message, request_id }
                           # The parsed object `resp` is expected to have these properties directly.
                           
                           # SO, the wrapper in `main.py` WAS constructing:
                           # { "request_id": ..., "type": ..., "data": { "status": "success", ... } }
                           
                           # IF python.ts reads `resp.status`, it would be undefined!
                           # UNLESS `resp` IS `response_data` merged with `request_id`.
                           
                           # Let's check `python.ts` again.
                           # `if (resp.request_id && pendingRequests.has(resp.request_id))`
                           # If the top level JSON is { "data": { "status":... } }, then `resp.status` is undefined.
                           
                           # Logic check:
                           # If I change `process_command` to flatten the structure, it will work.
                           # { "request_id": "...", "status": "ok", "data": { ... } }
                           
                           # So, I will modify `process_command` to be compatible with `python.ts`.
                           # I will ensure `handle_*` returns `data` (dict) or raises Error.
                           # And `process_command` constructs the final JSON.
                           
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
                response_payload = res # .get('message') or preview? 
                # python.ts expects 'data' prop.
                # handle_load_data returns { status, message, preview/count }
                # Let's allow handle functions to return the full Dict, and we merge it?
                # Or we standardize handle functions to return `data` or raise Exception.
                pass
                
        elif cmd == "run_backtest":
            res = handle_run_backtest(params)
             # handle returns { status, result }
            if res['status'] == 'error':
                 status = 'error'
                 message = res['message']
            else:
                 response_payload = res.get('result')

        elif cmd == "get_replay_state":
            res = handle_get_replay_state(params)
            # handle returns { status, data }
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
        # python.ts checks: status (ok/error), data, message, request_id
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

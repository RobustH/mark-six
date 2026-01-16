import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';

export interface PythonResponse {
    status: 'ok' | 'error' | 'warn';
    data?: any;
    message?: string;
    request_id?: string;
}

// 简单的请求追踪器
const pendingRequests = new Map<string, { resolve: (val: any) => void; reject: (reason: any) => void; timer: any }>();

// 初始化监听器
let isInitialized = false;
export async function initPythonListener() {
    if (isInitialized) return;

    await listen<string>('python-response', (event) => {
        try {
            // 注意：Python 可能在一次 Stdout 中输出多行 JSON，或者部分行不是 JSON
            const lines = event.payload.split('\n');
            for (const line of lines) {
                const trimmed = line.trim();
                if (!trimmed || !trimmed.startsWith('{')) continue;

                try {
                    const resp = JSON.parse(trimmed) as PythonResponse;
                    if (resp.request_id && pendingRequests.has(resp.request_id)) {
                        const { resolve, timer } = pendingRequests.get(resp.request_id)!;
                        clearTimeout(timer);
                        pendingRequests.delete(resp.request_id);
                        resolve(resp);
                    }
                } catch (jsonErr) {
                    console.warn('忽略非 JSON 输出:', trimmed);
                }
            }
        } catch (e) {
            console.error('监听器处理错误:', e);
        }
    });

    isInitialized = true;
}

function generateId() {
    return Math.random().toString(36).substr(2, 9);
}

/**
 * 调用 Python 指令并等待其Stdout返回对应的 JSON 结果
 */
export async function callPython(cmd: string, params: any = {}): Promise<PythonResponse> {
    await initPythonListener();

    const requestId = generateId();

    return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
            if (pendingRequests.has(requestId)) {
                pendingRequests.delete(requestId);
                reject(new Error(`指令 ${cmd} 请求超时 (15s)`));
            }
        }, 15000);

        pendingRequests.set(requestId, { resolve, reject, timer });

        // 统一使用 payload 包装器，以匹配 Rust 端的 Value 类型接收
        let invokeCmd = cmd;
        if (cmd === 'load_data') invokeCmd = 'load_data_source';
        else if (cmd === 'run_backtest') invokeCmd = 'run_backtest_simulation';

        const payload = { ...params, request_id: requestId };

        invoke(invokeCmd, { payload })
            .catch(e => {
                clearTimeout(timer);
                pendingRequests.delete(requestId);
                reject(e);
            });
    });
}

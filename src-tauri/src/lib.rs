use std::sync::Arc;
use tokio::sync::Mutex;
use serde_json::Value;
use tauri_plugin_shell::process::CommandChild;

mod data_manager;

pub struct PythonState {
    pub stdin: Option<CommandChild>,
}

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
async fn run_backtest_simulation(
    state: tauri::State<'_, Arc<Mutex<PythonState>>>,
    payload: Value,
) -> Result<Value, String> {
    let mut state = state.lock().await;
    
    if state.stdin.is_none() {
        return Err("Python 引擎未运行".to_string());
    }

    let child = state.stdin.as_mut().unwrap();
    let req_id = payload.get("request_id").cloned();
    
    let cmd = serde_json::json!({
        "cmd": "run_backtest",
        "params": payload,
        "request_id": req_id
    });

    let cmd_str = cmd.to_string() + "\n";
    child.write(cmd_str.as_bytes()).map_err(|e: tauri_plugin_shell::Error| e.to_string())?;

    Ok(serde_json::json!({ "status": "sent" }))
}

#[tauri::command]
async fn load_data_source(
    state: tauri::State<'_, Arc<Mutex<PythonState>>>,
    payload: Value,
) -> Result<Value, String> {
    let mut state = state.lock().await;
    if let Some(child) = state.stdin.as_mut() {
        let req_id = payload.get("request_id").cloned();
        let file_path = payload.get("file_path").and_then(|v: &Value| v.as_str()).unwrap_or("");
        
        let cmd = serde_json::json!({
            "cmd": "load_data",
            "params": { "file_path": file_path },
            "request_id": req_id
        });
        let cmd_str = cmd.to_string() + "\n";
        child.write(cmd_str.as_bytes()).map_err(|e: tauri_plugin_shell::Error| e.to_string())?;
        Ok(serde_json::json!({ "status": "sent" }))
    } else {
        Err("Python 引擎未就绪".into())
    }
}

#[tauri::command]
async fn get_replay_state(
    state: tauri::State<'_, Arc<Mutex<PythonState>>>,
    payload: Value,
) -> Result<Value, String> {
    let mut state = state.lock().await;
    if let Some(child) = state.stdin.as_mut() {
        let req_id = payload.get("request_id").cloned();
        let period = payload.get("period").and_then(|v: &Value| v.as_str()).unwrap_or("");
        let strategy_config = payload.get("strategy_config").cloned();

        let cmd = serde_json::json!({
            "cmd": "get_replay_state",
            "params": { 
                "period": period,
                "strategy_config": strategy_config
            },
            "request_id": req_id
        });
        let cmd_str = cmd.to_string() + "\n";
        child.write(cmd_str.as_bytes()).map_err(|e: tauri_plugin_shell::Error| e.to_string())?;
        Ok(serde_json::json!({ "status": "sent" }))
    } else {
        Err("Python 引擎未就绪".into())
    }
}

#[tauri::command]
async fn get_data_stats(
    state: tauri::State<'_, Arc<Mutex<PythonState>>>,
    payload: Value,
) -> Result<Value, String> {
    let mut state = state.lock().await;
    if let Some(child) = state.stdin.as_mut() {
        let req_id = payload.get("request_id").cloned();
        let cmd = serde_json::json!({
            "cmd": "get_data_stats",
            "request_id": req_id
        });
        let cmd_str = cmd.to_string() + "\n";
        child.write(cmd_str.as_bytes()).map_err(|e: tauri_plugin_shell::Error| e.to_string())?;
        Ok(serde_json::json!({ "status": "sent" }))
    } else {
        Err("Python 引擎未就绪".into())
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let python_state = Arc::new(Mutex::new(PythonState { stdin: None }));

    let migrations = vec![
        tauri_plugin_sql::Migration {
            version: 1,
            description: "创建 entry_rules 表",
            sql: "CREATE TABLE IF NOT EXISTS entry_rules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                conditions TEXT NOT NULL,
                logicOperator TEXT NOT NULL,
                createTime INTEGER NOT NULL,
                updateTime INTEGER NOT NULL
            );",
            kind: tauri_plugin_sql::MigrationKind::Up,
        },
        tauri_plugin_sql::Migration {
            version: 2,
            description: "创建 money_rules 表",
            sql: "CREATE TABLE IF NOT EXISTS money_rules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                mode TEXT NOT NULL,
                params TEXT NOT NULL,
                createTime INTEGER NOT NULL,
                updateTime INTEGER NOT NULL
            );",
            kind: tauri_plugin_sql::MigrationKind::Up,
        },
        tauri_plugin_sql::Migration {
            version: 3,
            description: "创建 strategies 表",
            sql: "CREATE TABLE IF NOT EXISTS strategies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                entryRuleId TEXT NOT NULL,
                moneyRuleId TEXT NOT NULL,
                createTime INTEGER NOT NULL,
                updateTime INTEGER NOT NULL
            );",
            kind: tauri_plugin_sql::MigrationKind::Up,
        }
    ];

    tauri::Builder::default()
        .manage(python_state)
        .plugin(tauri_plugin_sql::Builder::default().add_migrations("sqlite:mark_six.db", migrations).build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            data_manager::import_excel,
            data_manager::get_historical_data,
            data_manager::get_historical_years,
            run_backtest_simulation,
            load_data_source,
            get_replay_state,
            get_data_stats
        ])
        .run(tauri::generate_context!())
        .expect("运行 tauri 应用时出错");
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

use std::sync::Arc;
use tokio::sync::Mutex;
use serde_json::Value;
use std::path::PathBuf;
use tauri::Manager;
use tauri::Emitter;

mod data_manager;

use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::{CommandEvent, CommandChild};

pub struct PythonState {
    pub child: Option<CommandChild>,
}

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
async fn run_backtest_simulation(
    state: tauri::State<'_, Arc<Mutex<PythonState>>>,
    payload: Value,
) -> Result<Value, String> {
    let mut state = state.lock().await;
    
    if state.child.is_none() {
        return Err("Python 引擎未运行".to_string());
    }

    let child = state.child.as_mut().unwrap();
    let req_id = payload.get("request_id").cloned();
    
    let cmd = serde_json::json!({
        "cmd": "run_backtest",
        "params": payload,
        "request_id": req_id
    });

    let cmd_str = cmd.to_string() + "\n";
    child.write(cmd_str.as_bytes()).map_err(|e| e.to_string())?;

    Ok(serde_json::json!({ "status": "sent" }))
}

#[tauri::command]
async fn load_data_source(
    state: tauri::State<'_, Arc<Mutex<PythonState>>>,
    payload: Value,
) -> Result<Value, String> {
    let mut state = state.lock().await;
    if let Some(child) = state.child.as_mut() {
        let req_id = payload.get("request_id").cloned();
        let file_path = payload.get("file_path").and_then(|v: &Value| v.as_str()).unwrap_or("");
        
        let data_dir = data_manager::get_project_data_dir().map_err(|e| e.to_string())?;
        let final_path = if file_path.is_empty() || file_path == "all" {
             let p = data_dir.join("history").join("all.feather");
             if p.exists() {
                 p.to_string_lossy().to_string()
             } else {
                 data_dir.join("history.feather").to_string_lossy().to_string()
             }
        } else {
             let year_path = data_dir.join("history").join(format!("{}.feather", file_path));
             if year_path.exists() {
                 year_path.to_string_lossy().to_string()
             } else {
                 file_path.to_string()
             }
        };

        let cmd = serde_json::json!({
            "cmd": "load_data",
            "params": { "file_path": final_path },
            "request_id": req_id
        });
        let cmd_str = cmd.to_string() + "\n";
        child.write(cmd_str.as_bytes()).map_err(|e| e.to_string())?;
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
    if let Some(child) = state.child.as_mut() {
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
        child.write(cmd_str.as_bytes()).map_err(|e| e.to_string())?;
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
    if let Some(child) = state.child.as_mut() {
        let req_id = payload.get("request_id").cloned();
        let cmd = serde_json::json!({
            "cmd": "get_data_stats",
            "request_id": req_id
        });
        let cmd_str = cmd.to_string() + "\n";
        child.write(cmd_str.as_bytes()).map_err(|e| e.to_string())?;
        Ok(serde_json::json!({ "status": "sent" }))
    } else {
        Err("Python 引擎未就绪".into())
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let python_state = Arc::new(Mutex::new(PythonState { child: None }));

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
        },
        tauri_plugin_sql::Migration {
            version: 4,
            description: "创建 odds_profiles 表",
            sql: "CREATE TABLE IF NOT EXISTS odds_profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                playType TEXT NOT NULL,
                odds REAL NOT NULL,
                rebate REAL,
                maxPayout REAL,
                version TEXT NOT NULL,
                validFrom TEXT,
                validTo TEXT,
                createTime INTEGER NOT NULL,
                updateTime INTEGER NOT NULL
            );",
            kind: tauri_plugin_sql::MigrationKind::Up,
        },
        tauri_plugin_sql::Migration {
            version: 5,
            description: "为 strategies 表添加 oddsProfileId 列",
            sql: "ALTER TABLE strategies ADD COLUMN oddsProfileId TEXT;",
            kind: tauri_plugin_sql::MigrationKind::Up,
        }
    ];

    tauri::Builder::default()
        .manage(python_state)
        .plugin(tauri_plugin_sql::Builder::default().add_migrations("sqlite:mark_six.db", migrations).build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let app_handle = app.handle().clone();
            
            // Start Sidecar
            let sidecar = app.shell().sidecar("mark-six-engine").unwrap();
            let (mut rx, child) = sidecar.spawn().expect("failed to spawn sidecar");

            tauri::async_runtime::spawn(async move {
                // Store child in state
                let state = app_handle.state::<Arc<Mutex<PythonState>>>();
                {
                    let mut state_guard = state.lock().await;
                    state_guard.child = Some(child);
                }

                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            let s = String::from_utf8_lossy(&line);
                            let _ = app_handle.emit("python-response", s.to_string());
                        }
                        CommandEvent::Stderr(line) => {
                            let s = String::from_utf8_lossy(&line);
                            eprintln!("PYTHON STDERR: {}", s);
                        }
                        _ => {}
                    }
                }
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            greet,
            data_manager::import_excel,
            data_manager::get_historical_data,
            data_manager::get_historical_years,
            data_manager::get_statistics,
            run_backtest_simulation,
            load_data_source,
            get_replay_state,
            get_data_stats,
            data_manager::fetch_historical_data
        ])
        .run(tauri::generate_context!())
        .expect("运行 tauri 应用时出错");
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

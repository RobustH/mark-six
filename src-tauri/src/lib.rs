use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandEvent;

// Defines the Python script path. 
// Ideally should be dynamic or relative to resource path, but hardcoded for MVP efficiency.
const PYTHON_SCRIPT: &str = r"f:/demo/mark-six/python/main.py";

#[tauri::command]
async fn run_backtest_simulation(app: tauri::AppHandle, payload: serde_json::Value) -> Result<serde_json::Value, String> {
    run_python_command(&app, "run_backtest", payload).await
}

#[tauri::command]
async fn get_replay_state(app: tauri::AppHandle, period: String) -> Result<serde_json::Value, String> {
    let payload = serde_json::json!({ "period": period });
    run_python_command(&app, "get_replay_state", payload).await
}

#[tauri::command]
async fn get_data_stats(app: tauri::AppHandle) -> Result<serde_json::Value, String> {
    run_python_command(&app, "get_data_stats", serde_json::json!({})).await
}

async fn run_python_command(app: &tauri::AppHandle, cmd: &str, params: serde_json::Value) -> Result<serde_json::Value, String> {
    let input_json = serde_json::json!({
        "cmd": cmd,
        "params": params
    });
    let input_str = input_json.to_string();

    let (mut rx, mut child) = app.shell()
        .command("python")
        .args([PYTHON_SCRIPT])
        .spawn()
        .map_err(|e| e.to_string())?;

    // Write input + newline
    let data = format!("{}\n", input_str);
    child.write(data.as_bytes()).map_err(|e| e.to_string())?;

    // Read response
    let mut response = String::new();
    let mut found_response = false;

    // Use a loop to read events
    while let Some(event) = rx.recv().await {
        match event {
            CommandEvent::Stdout(line) => {
                let s = String::from_utf8_lossy(&line);
                response.push_str(&s);
                // Check if we have a complete JSON object (heuristic or newline)
                // Our python script prints JSON + flush.
                // It usually comes in one chunk or line.
                // Let's assume one line for now.
                if response.trim().ends_with('}') {
                    found_response = true;
                    // Kill child as we are done with this one-off request
                    let _ = child.kill(); 
                    break;
                }
            }
            CommandEvent::Stderr(line) => {
                let s = String::from_utf8_lossy(&line);
                println!("Python Stderr: {}", s);
            }
            CommandEvent::Terminated(_) => {
                break;
            }
            _ => {}
        }
    }
    
    if !found_response && response.is_empty() {
        return Err("No response from Python script".into());
    }

    // Attempt to parse
    // The response might contain extra newlines
    let trimmed = response.trim();
    
    // Log for debug
    println!("Python Response: {}", trimmed);

    serde_json::from_str(trimmed).map_err(|e| format!("Failed to parse JSON: {} | Content: {}", e, trimmed))
}

#[tauri::command]
async fn load_data_source(app: tauri::AppHandle, filePath: String) -> Result<serde_json::Value, String> {
    let payload = serde_json::json!({ "file_path": filePath });
    // Use "load_data" command string as expected by main.py
    run_python_command(&app, "load_data", payload).await
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![greet, run_backtest_simulation, get_replay_state, load_data_source, get_data_stats])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

// Keep the existing greet function
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

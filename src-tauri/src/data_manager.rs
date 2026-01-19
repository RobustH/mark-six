use calamine::{Reader, Xlsx, open_workbook, Data, XlsxError};
use polars::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct HistoricalRecord {
    pub period: String,
    pub date: String,
    pub n1: i32,
    pub n2: i32,
    pub n3: i32,
    pub n4: i32,
    pub n5: i32,
    pub n6: i32,
    pub special: i32,
}

fn get_zodiac(num: i32) -> &'static str {
    let zodiacs = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"];
    zodiacs[((num - 1) % 12) as usize]
}

fn get_color(num: i32) -> &'static str {
    // 六合彩颜色规则：红、蓝、绿
    let red = [1, 2, 7, 8, 12, 13, 18, 19, 23, 24, 29, 30, 34, 35, 40, 45, 46];
    let blue = [3, 4, 9, 10, 14, 15, 20, 25, 26, 31, 36, 37, 41, 42, 47, 48];
    if red.contains(&num) { "red" }
    else if blue.contains(&num) { "blue" }
    else { "green" }
}

fn is_odd(num: i32) -> bool {
    num % 2 == 1
}

fn get_project_data_dir() -> Result<PathBuf, String> {
    let exe_path = std::env::current_exe().map_err(|e| e.to_string())?;
    let exe_dir = exe_path.parent().ok_or("无法获取可执行文件目录")?;
    
    // 在开发模式下，我们需要向上找到项目根目录
    let mut current = exe_dir;
    for _ in 0..5 {
        let data_dir = current.join("data");
        if data_dir.exists() {
            return Ok(data_dir);
        }
        current = current.parent().ok_or("无法找到项目根目录")?;
    }
    
    // 如果找不到，就在当前目录创建
    let data_dir = exe_dir.join("data");
    Ok(data_dir)
}

#[tauri::command]
pub async fn import_excel(_app_handle: tauri::AppHandle, file_path: String) -> Result<String, String> {
    let mut workbook: Xlsx<_> = open_workbook(&file_path).map_err(|e: XlsxError| e.to_string())?;
    
    let mut year_records: HashMap<String, Vec<HistoricalRecord>> = HashMap::new();
    let sheet_names = workbook.sheet_names().to_vec();

    for sheet_name in sheet_names {
        if let Ok(range) = workbook.worksheet_range(&sheet_name) {
            for row in range.rows().skip(1) {
                if row.len() < 20 { continue; }
                
                let period_date_str = row[0].to_string();
                let parts: Vec<&str> = period_date_str.split_whitespace().collect();
                if parts.len() < 2 { continue; }
                
                let period = parts[0].replace("期", "");
                let date = parts[1].to_string();
                
                // Extract year from date (YYYY-MM-DD)
                let year = date.split('-').next().unwrap_or("").to_string();
                if year.is_empty() || year.len() != 4 { continue; }

                let get_int = |cell: &Data| -> i32 {
                    match cell {
                        Data::Float(f) => *f as i32,
                        Data::Int(i) => *i as i32,
                        Data::String(s) => s.parse().unwrap_or(0),
                        _ => 0,
                    }
                };

                let record = HistoricalRecord {
                    period,
                    date,
                    n1: get_int(&row[1]),
                    n2: get_int(&row[4]),
                    n3: get_int(&row[7]),
                    n4: get_int(&row[10]),
                    n5: get_int(&row[13]),
                    n6: get_int(&row[16]),
                    special: get_int(&row[19]),
                };
                
                year_records.entry(year).or_default().push(record);
            }
        }
    }

    if year_records.is_empty() {
        return Err("未找到有效数据记录".to_string());
    }

    let data_dir = get_project_data_dir()?;
    let history_dir = data_dir.join("history");
    std::fs::create_dir_all(&history_dir).map_err(|e| e.to_string())?;

    let mut total_records = 0;
    let mut years_imported = Vec::new();

    for (year, mut records) in year_records {
        // Sort records by date descending
        records.sort_by(|a, b| b.date.cmp(&a.date));
        
        let periods: Vec<String> = records.iter().map(|r| r.period.clone()).collect();
        let dates: Vec<String> = records.iter().map(|r| r.date.clone()).collect();
        let n1: Vec<i32> = records.iter().map(|r| r.n1).collect();
        let n1_zodiac: Vec<String> = records.iter().map(|r| get_zodiac(r.n1).to_string()).collect();
        let n1_color: Vec<String> = records.iter().map(|r| get_color(r.n1).to_string()).collect();
        let n1_odd: Vec<bool> = records.iter().map(|r| is_odd(r.n1)).collect();
        
        let n2: Vec<i32> = records.iter().map(|r| r.n2).collect();
        let n2_zodiac: Vec<String> = records.iter().map(|r| get_zodiac(r.n2).to_string()).collect();
        let n2_color: Vec<String> = records.iter().map(|r| get_color(r.n2).to_string()).collect();
        let n2_odd: Vec<bool> = records.iter().map(|r| is_odd(r.n2)).collect();
        
        let n3: Vec<i32> = records.iter().map(|r| r.n3).collect();
        let n3_zodiac: Vec<String> = records.iter().map(|r| get_zodiac(r.n3).to_string()).collect();
        let n3_color: Vec<String> = records.iter().map(|r| get_color(r.n3).to_string()).collect();
        let n3_odd: Vec<bool> = records.iter().map(|r| is_odd(r.n3)).collect();
        
        let n4: Vec<i32> = records.iter().map(|r| r.n4).collect();
        let n4_zodiac: Vec<String> = records.iter().map(|r| get_zodiac(r.n4).to_string()).collect();
        let n4_color: Vec<String> = records.iter().map(|r| get_color(r.n4).to_string()).collect();
        let n4_odd: Vec<bool> = records.iter().map(|r| is_odd(r.n4)).collect();
        
        let n5: Vec<i32> = records.iter().map(|r| r.n5).collect();
        let n5_zodiac: Vec<String> = records.iter().map(|r| get_zodiac(r.n5).to_string()).collect();
        let n5_color: Vec<String> = records.iter().map(|r| get_color(r.n5).to_string()).collect();
        let n5_odd: Vec<bool> = records.iter().map(|r| is_odd(r.n5)).collect();
        
        let n6: Vec<i32> = records.iter().map(|r| r.n6).collect();
        let n6_zodiac: Vec<String> = records.iter().map(|r| get_zodiac(r.n6).to_string()).collect();
        let n6_color: Vec<String> = records.iter().map(|r| get_color(r.n6).to_string()).collect();
        let n6_odd: Vec<bool> = records.iter().map(|r| is_odd(r.n6)).collect();
        
        let special: Vec<i32> = records.iter().map(|r| r.special).collect();
        let special_zodiac: Vec<String> = records.iter().map(|r| get_zodiac(r.special).to_string()).collect();
        let special_color: Vec<String> = records.iter().map(|r| get_color(r.special).to_string()).collect();
        let special_odd: Vec<bool> = records.iter().map(|r| is_odd(r.special)).collect();

        let mut df = df!(
            "period" => periods,
            "date" => dates,
            "n1" => n1,
            "n1_zodiac" => n1_zodiac,
            "n1_color" => n1_color,
            "n1_odd" => n1_odd,
            "n2" => n2,
            "n2_zodiac" => n2_zodiac,
            "n2_color" => n2_color,
            "n2_odd" => n2_odd,
            "n3" => n3,
            "n3_zodiac" => n3_zodiac,
            "n3_color" => n3_color,
            "n3_odd" => n3_odd,
            "n4" => n4,
            "n4_zodiac" => n4_zodiac,
            "n4_color" => n4_color,
            "n4_odd" => n4_odd,
            "n5" => n5,
            "n5_zodiac" => n5_zodiac,
            "n5_color" => n5_color,
            "n5_odd" => n5_odd,
            "n6" => n6,
            "n6_zodiac" => n6_zodiac,
            "n6_color" => n6_color,
            "n6_odd" => n6_odd,
            "special" => special,
            "special_zodiac" => special_zodiac,
            "special_color" => special_color,
            "special_odd" => special_odd,
        ).map_err(|e| e.to_string())?;

        let feather_path = history_dir.join(format!("{}.feather", year));
        let file = std::fs::File::create(&feather_path).map_err(|e| e.to_string())?;
        IpcWriter::new(file).finish(&mut df).map_err(|e| e.to_string())?;
        
        total_records += df.height();
        years_imported.push((year, df));
    }

    // 生成总的 feather 文件
    if !years_imported.is_empty() {
        let mut all_dfs: Vec<DataFrame> = years_imported.iter().map(|(_, df)| df.clone()).collect();
        let mut combined_df = if all_dfs.len() > 1 {
            let mut first = all_dfs.remove(0);
            for next in all_dfs {
                first = first.vstack(&next).map_err(|e| e.to_string())?;
            }
            first
        } else {
            all_dfs[0].clone()
        };
        
        // 去重并按日期降序排序
        combined_df = combined_df.unique_stable(None, UniqueKeepStrategy::First, None).map_err(|e| e.to_string())?;
        combined_df = combined_df.sort(["date"], SortMultipleOptions::default().with_order_descending(true)).map_err(|e| e.to_string())?;
        
        let all_feather_path = history_dir.join("all.feather");
        let file = std::fs::File::create(&all_feather_path).map_err(|e| e.to_string())?;
        IpcWriter::new(file).finish(&mut combined_df).map_err(|e| e.to_string())?;
    }

    let year_names: Vec<String> = years_imported.iter().map(|(y, _)| y.clone()).collect();
    let mut sorted_years = year_names.clone();
    sorted_years.sort_by(|a, b| b.cmp(a));
    Ok(format!("成功从所有子表中导入 {} 条记录，包含年份: {}", total_records, sorted_years.join(", ")))
}

#[tauri::command]
pub async fn get_historical_years(_app_handle: tauri::AppHandle) -> Result<Vec<String>, String> {
    let data_dir = get_project_data_dir()?;
    let history_dir = data_dir.join("history");
    
    if !history_dir.exists() {
        return Ok(Vec::new());
    }

    let mut years = Vec::new();
    let entries = std::fs::read_dir(history_dir).map_err(|e| e.to_string())?;
    for entry in entries {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();
        if path.extension().and_then(|s| s.to_str()) == Some("feather") {
            if let Some(year) = path.file_stem().and_then(|s| s.to_str()) {
                years.push(year.to_string());
            }
        }
    }

    years.sort_by(|a, b| b.cmp(a));
    Ok(years)
}

#[tauri::command]
pub async fn get_historical_data(_app_handle: tauri::AppHandle, year: Option<String>) -> Result<serde_json::Value, String> {
    let data_dir = get_project_data_dir()?;
    
    if let Some(year_str) = year {
        if !year_str.is_empty() && year_str != "全部" {
            let path = data_dir.join("history").join(format!("{}.feather", year_str));
            if !path.exists() {
                return Ok(serde_json::json!([]));
            }
            let file = std::fs::File::open(&path).map_err(|e| e.to_string())?;
            let mut df = IpcReader::new(file).finish().map_err(|e| e.to_string())?;
            return dataframe_to_json(&mut df);
        }
    }

    let history_dir = data_dir.join("history");
    let mut all_dfs = Vec::new();

    if history_dir.exists() {
        let entries = std::fs::read_dir(&history_dir).map_err(|e| e.to_string())?;
        for entry in entries {
            let entry = entry.map_err(|e| e.to_string())?;
            let path = entry.path();
            if path.extension().and_then(|s| s.to_str()) == Some("feather") {
                let file = std::fs::File::open(&path).map_err(|e| e.to_string())?;
                let df = IpcReader::new(file).finish().map_err(|e| e.to_string())?;
                all_dfs.push(df);
            }
        }
    }

    // Include legacy file if it exists
    let old_path = data_dir.join("historical_data.feather");
    if old_path.exists() {
        let file = std::fs::File::open(&old_path).map_err(|e| e.to_string())?;
        let df = IpcReader::new(file).finish().map_err(|e| e.to_string())?;
        all_dfs.push(df);
    }

    if all_dfs.is_empty() {
        return Ok(serde_json::json!([]));
    }

    let mut combined_df = if all_dfs.len() > 1 {
        let mut first = all_dfs.remove(0);
        for next in all_dfs {
            first = first.vstack(&next).map_err(|e| e.to_string())?;
        }
        first
    } else {
        all_dfs[0].clone()
    };

    combined_df = combined_df.unique_stable(None, UniqueKeepStrategy::First, None).map_err(|e| e.to_string())?;
    combined_df = combined_df.sort(["date"], SortMultipleOptions::default().with_order_descending(true)).map_err(|e| e.to_string())?;

    dataframe_to_json(&mut combined_df)
}

fn dataframe_to_json(df: &mut DataFrame) -> Result<serde_json::Value, String> {
    let mut buf = Vec::new();
    JsonWriter::new(&mut buf)
        .with_json_format(JsonFormat::Json)
        .finish(df)
        .map_err(|e| e.to_string())?;

    let value: serde_json::Value = serde_json::from_slice(&buf).map_err(|e| e.to_string())?;
    Ok(value)
}

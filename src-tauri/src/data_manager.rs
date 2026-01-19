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

pub fn get_project_data_dir() -> Result<PathBuf, String> {
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

use reqwest::Client;
use chrono::Datelike;

#[derive(Serialize, Deserialize, Debug)]
pub struct ApiItem {
    #[serde(rename = "Period")]
    pub period: String,
    #[serde(rename = "Date")]
    pub date: String,
    #[serde(rename = "Numbers")]
    pub numbers: Vec<i32>,
}

#[derive(Serialize, Deserialize, Debug)]
struct ApiResponse {
    body: Option<Vec<ApiItem>>,
}

// ... existing helper functions ...

fn process_and_save_data(
    year_records: HashMap<String, Vec<HistoricalRecord>>, 
    data_dir: PathBuf
) -> Result<String, String> {
    let history_dir = data_dir.join("history");
    std::fs::create_dir_all(&history_dir).map_err(|e| e.to_string())?;

    let mut total_records = 0;
    
    // Process each year
    for (year, mut records) in year_records {
        // Sort records by date ascending, then by period ascending
        records.sort_by(|a, b| {
            let date_cmp = a.date.cmp(&b.date);
            if date_cmp == std::cmp::Ordering::Equal {
                a.period.cmp(&b.period)
            } else {
                date_cmp
            }
        });
        
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
            "date" => dates.clone(),
            "year" => dates.iter().map(|d| d.split('-').next().unwrap_or("").to_string()).collect::<Vec<String>>(),
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
    }

    // Regenerate all.feather by reading all individual year files
    let mut all_dfs = Vec::new();
    let entries = std::fs::read_dir(&history_dir).map_err(|e| e.to_string())?;
    let mut year_names = Vec::new();

    for entry in entries {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();
        // Ignore directory itself and non-feather files
        if path.extension().and_then(|s| s.to_str()) == Some("feather") {
            // Important: Exclude all.feather itself and historical_data.feather to avoid duplication/cycles
            if let Some(stem) = path.file_stem().and_then(|s| s.to_str()) {
                if stem == "all" || stem == "historical_data" {
                    continue;
                }
                year_names.push(stem.to_string());
                let file = std::fs::File::open(&path).map_err(|e| e.to_string())?;
                let df = IpcReader::new(file).finish().map_err(|e| e.to_string())?;
                all_dfs.push(df);
            }
        }
    }

    if !all_dfs.is_empty() {
        let mut combined_df = if all_dfs.len() > 1 {
            let mut first = all_dfs.remove(0);
            for next in all_dfs {
                first = first.vstack(&next).map_err(|e| e.to_string())?;
            }
            first
        } else {
            all_dfs[0].clone()
        };
        
        // Deduplicate and sort
        combined_df = combined_df.unique_stable(None, UniqueKeepStrategy::First, None).map_err(|e| e.to_string())?;
        combined_df = combined_df.sort(["date"], SortMultipleOptions::default().with_order_descending(false)).map_err(|e| e.to_string())?;
        
        let all_feather_path = history_dir.join("all.feather");
        let file = std::fs::File::create(&all_feather_path).map_err(|e| e.to_string())?;
        IpcWriter::new(file).finish(&mut combined_df).map_err(|e| e.to_string())?;
    }
    
    year_names.sort_by(|a, b| b.cmp(a));
    Ok(format!("成功处理 {} 条记录，涉及年份: {}", total_records, year_names.join(", ")))
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
    process_and_save_data(year_records, data_dir)
}

#[tauri::command]
pub async fn fetch_historical_data(_app_handle: tauri::AppHandle, years: Option<Vec<String>>) -> Result<String, String> {
    let client = Client::builder()
        .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        .build()
        .map_err(|e| e.to_string())?;

    let years_to_fetch = years.unwrap_or_else(|| {
        let current_year = chrono::Local::now().year();
        // Default to incremental update: fetch only the current year
        vec![current_year.to_string()]
    });

    let mut year_records: HashMap<String, Vec<HistoricalRecord>> = HashMap::new();
    let mut debug_log = String::new();

    for year in years_to_fetch {
        let url = format!("https://tbri9x.xlgwrkd.xyz/api/MarkSix/GetHistory?lotId=20&year={}", year);
        println!("Fetching: {}", url);
        
        match client.get(&url).send().await {
            Ok(resp) => {
                let status = resp.status();
                if !status.is_success() {
                    println!("Request failed for {}: {}", year, status);
                    continue;
                }

                if let Ok(text) = resp.text().await {
                    // Try to parse as Value first to handle flexible types
                    if let Ok(json_val) = serde_json::from_str::<serde_json::Value>(&text) {
                         let items_array = if let Some(body) = json_val.get("body") {
                            body.as_array()
                        } else {
                            json_val.as_array()
                        };

                        if let Some(api_items) = items_array {
                            for item in api_items {
                                // Manual parsing to be safe
                                let raw_period = item.get("Period").and_then(|v| v.as_str()).unwrap_or("").replace("期", "");
                                // Pad period to 3 digits (e.g. "1" -> "001") to ensure correct String sorting
                                let period = if let Ok(p_num) = raw_period.parse::<i32>() {
                                    format!("{:03}", p_num)
                                } else {
                                    raw_period
                                };

                                let mut date = item.get("Date").and_then(|v| v.as_str()).unwrap_or("").to_string();
                                
                                // Fix bad dates (API returns 0001-01-01 for old data)
                                // If date is invalid, set to Jan 1st of that year so at least the year is correct
                                if date.len() < 5 || date.starts_with("0001") {
                                    date = format!("{}-01-01", year);
                                }
                                
                                let numbers_val = item.get("Numbers");
                                let mut numbers = Vec::new();
                                
                                if let Some(nums) = numbers_val {
                                    if let Some(arr) = nums.as_array() {
                                        for n in arr {
                                            if let Some(i) = n.as_i64() {
                                                numbers.push(i as i32);
                                            } else if let Some(s) = n.as_str() {
                                                if let Ok(i) = s.parse::<i32>() {
                                                    numbers.push(i);
                                                }
                                            }
                                        }
                                    } else if let Some(s) = nums.as_str() {
                                        // Handle string case if needed (e.g. "1,2,3")
                                        // Assuming comma separated or similar if it's a string
                                        let re = regex::Regex::new(r"\d+").unwrap(); 
                                        for cap in re.captures_iter(s) {
                                            if let Ok(i) = cap[0].parse::<i32>() {
                                                numbers.push(i);
                                            }
                                        }
                                    }
                                }

                                if numbers.len() < 7 { continue; }
                                
                                let record = HistoricalRecord {
                                    period,
                                    date,
                                    n1: numbers[0],
                                    n2: numbers[1],
                                    n3: numbers[2],
                                    n4: numbers[3],
                                    n5: numbers[4],
                                    n6: numbers[5],
                                    special: numbers[6],
                                };
                                year_records.entry(year.clone()).or_default().push(record);
                            }
                        } else {
                            debug_log.push_str(&format!("Year {}: JSON structure mismatch. ", year));
                        }
                    } else {
                        debug_log.push_str(&format!("Year {}: Failed to parse JSON. ", year));
                    }
                }
            },
            Err(e) => {
                debug_log.push_str(&format!("Year {}: Request error {}. ", year, e));
                continue;
            }
        }
    }

    if year_records.is_empty() {
        return Err(format!("未能获取到任何数据。Debug info: {}", debug_log));
    }

    let data_dir = get_project_data_dir()?;
    process_and_save_data(year_records, data_dir)
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

    years.sort_by(|a, b| a.cmp(b));
    Ok(years)
}

fn load_merged_dataframe(data_dir: &PathBuf, year: Option<String>) -> Result<DataFrame, String> {
    if let Some(year_str) = year {
        if !year_str.is_empty() && year_str != "全部" {
            let path = data_dir.join("history").join(format!("{}.feather", year_str));
            if !path.exists() {
                return Ok(DataFrame::empty());
            }
            let file = std::fs::File::open(&path).map_err(|e| e.to_string())?;
            return IpcReader::new(file).finish().map_err(|e| e.to_string());
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
        return Ok(DataFrame::empty());
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
    
    Ok(combined_df)
}

#[tauri::command]
pub async fn get_historical_data(_app_handle: tauri::AppHandle, year: Option<String>) -> Result<serde_json::Value, String> {
    let data_dir = get_project_data_dir()?;
    let mut df = load_merged_dataframe(&data_dir, year)?;
    dataframe_to_json(&mut df)
}

#[derive(Serialize, Clone)]
pub struct StatItem {
    pub label: String,
    pub current_omission: i32,
    pub max_omission: i32,
    pub frequency: i32,
    pub avg_omission: f64,
}

#[derive(Serialize)]
pub struct StatisticsReport {
    pub special_number: Vec<StatItem>,
    pub special_zodiac: Vec<StatItem>,
    pub special_color: Vec<StatItem>,
    pub special_odd: Vec<StatItem>,
    pub special_size: Vec<StatItem>,
    pub special_tail: Vec<StatItem>,
    pub normal_number: Vec<StatItem>,
}

fn calculate_omission_stats(present_flags: &[bool], total_periods: usize) -> (i32, i32, i32, f64) {
    let frequency = present_flags.iter().filter(|&&x| x).count() as i32;
    
    // 1. Current Omission
    let current_omission = match present_flags.iter().position(|&x| x) {
        Some(idx) => idx as i32,
        None => total_periods as i32,
    };
    
    // 2. Max Omission
    let mut max_omission = 0;
    let mut current_run = 0;
    
    for &hit in present_flags {
        if hit {
            if current_run > max_omission {
                max_omission = current_run;
            }
            current_run = 0;
        } else {
            current_run += 1;
        }
    }
    // Check last run (earliest history)
    if current_run > max_omission {
        max_omission = current_run;
    }
    
    let avg = if frequency > 0 {
        total_periods as f64 / frequency as f64
    } else {
        0.0
    };
    
    (current_omission, max_omission, frequency, avg)
}

#[tauri::command]
pub async fn get_statistics(_app_handle: tauri::AppHandle, year: Option<String>, limit: Option<usize>) -> Result<StatisticsReport, String> {
    let data_dir = get_project_data_dir()?;
    let mut df = load_merged_dataframe(&data_dir, year)?;
    
    if df.height() == 0 {
        return Err("无数据可供分析".to_string());
    }

    // Apply limit if specified (e.g. recent 100 periods)
    // load_merged_dataframe already sorts by date descending, so head(n) gives the most recent n periods.
    if let Some(n) = limit {
        if n > 0 && n < df.height() {
            df = df.head(Some(n));
        }
    }

    let total_periods = df.height();
    
    // Extract Columns
    let special_s = df.column("special").map_err(|e| e.to_string())?.i32().map_err(|e| e.to_string())?;
    let special_zodiac_s = df.column("special_zodiac").map_err(|e| e.to_string())?.str().map_err(|e| e.to_string())?;
    let special_color_s = df.column("special_color").map_err(|e| e.to_string())?.str().map_err(|e| e.to_string())?;
    let special_odd_s = df.column("special_odd").map_err(|e| e.to_string())?.bool().map_err(|e| e.to_string())?;
    
    let n1_s = df.column("n1").map_err(|e| e.to_string())?.i32().map_err(|e| e.to_string())?;
    let n2_s = df.column("n2").map_err(|e| e.to_string())?.i32().map_err(|e| e.to_string())?;
    let n3_s = df.column("n3").map_err(|e| e.to_string())?.i32().map_err(|e| e.to_string())?;
    let n4_s = df.column("n4").map_err(|e| e.to_string())?.i32().map_err(|e| e.to_string())?;
    let n5_s = df.column("n5").map_err(|e| e.to_string())?.i32().map_err(|e| e.to_string())?;
    let n6_s = df.column("n6").map_err(|e| e.to_string())?.i32().map_err(|e| e.to_string())?;

    // Pre-convert to Vecs for faster iteration
    let special_vec: Vec<Option<i32>> = special_s.into_iter().collect();
    let special_zodiac_vec: Vec<Option<&str>> = special_zodiac_s.into_iter().collect();
    let special_color_vec: Vec<Option<&str>> = special_color_s.into_iter().collect();
    let special_odd_vec: Vec<Option<bool>> = special_odd_s.into_iter().collect();
    
    let n1_vec: Vec<Option<i32>> = n1_s.into_iter().collect();
    let n2_vec: Vec<Option<i32>> = n2_s.into_iter().collect();
    let n3_vec: Vec<Option<i32>> = n3_s.into_iter().collect();
    let n4_vec: Vec<Option<i32>> = n4_s.into_iter().collect();
    let n5_vec: Vec<Option<i32>> = n5_s.into_iter().collect();
    let n6_vec: Vec<Option<i32>> = n6_s.into_iter().collect();

    // 1. Special Number Stats (1-49)
    let mut special_stats = Vec::new();
    for num in 1..=49 {
        let flags: Vec<bool> = special_vec.iter().map(|&x| x == Some(num)).collect();
        let (curs, max_o, freq, avg) = calculate_omission_stats(&flags, total_periods);
        special_stats.push(StatItem {
            label: num.to_string(),
            current_omission: curs,
            max_omission: max_o,
            frequency: freq,
            avg_omission: avg,
        });
    }

    // 2. Special Zodiac Stats
    let zodiacs = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"];
    let mut zodiac_stats = Vec::new();
    for z in zodiacs {
        let flags: Vec<bool> = special_zodiac_vec.iter().map(|&x| x == Some(z)).collect();
        let (curs, max_o, freq, avg) = calculate_omission_stats(&flags, total_periods);
        zodiac_stats.push(StatItem {
            label: z.to_string(),
            current_omission: curs,
            max_omission: max_o,
            frequency: freq,
            avg_omission: avg,
        });
    }

    // 3. Special Color Stats
    let colors = ["red", "blue", "green"];
    let mut color_stats = Vec::new();
    for c in colors {
        let flags: Vec<bool> = special_color_vec.iter().map(|&x| x == Some(c)).collect();
        let (curs, max_o, freq, avg) = calculate_omission_stats(&flags, total_periods);
        // Translate color name
        let label = match c {
            "red" => "红波",
            "blue" => "蓝波",
            "green" => "绿波",
            _ => c,
        };
        color_stats.push(StatItem {
            label: label.to_string(),
            current_omission: curs,
            max_omission: max_o,
            frequency: freq,
            avg_omission: avg,
        });
    }

    // 4. Special Odd/Even Stats (Parity)
    let mut odd_stats = Vec::new();
    // Odd
    let odd_flags: Vec<bool> = special_odd_vec.iter().map(|&x| x == Some(true)).collect();
    let (o_curs, o_max, o_freq, o_avg) = calculate_omission_stats(&odd_flags, total_periods);
    odd_stats.push(StatItem {
        label: "单".to_string(),
        current_omission: o_curs,
        max_omission: o_max,
        frequency: o_freq,
        avg_omission: o_avg,
    });
    // Even
    let even_flags: Vec<bool> = special_odd_vec.iter().map(|&x| x == Some(false)).collect();
    let (e_curs, e_max, e_freq, e_avg) = calculate_omission_stats(&even_flags, total_periods);
    odd_stats.push(StatItem {
        label: "双".to_string(),
        current_omission: e_curs,
        max_omission: e_max,
        frequency: e_freq,
        avg_omission: e_avg,
    });
    
    // 5. Special Size Stats (Big/Small)
    // Big >= 25, Small <= 24
    let mut size_stats = Vec::new();
    // Small
    let small_flags: Vec<bool> = special_vec.iter().map(|&x| x.map(|n| n >= 1 && n <= 24).unwrap_or(false)).collect();
    let (s_curs, s_max, s_freq, s_avg) = calculate_omission_stats(&small_flags, total_periods);
    size_stats.push(StatItem { label: "小".to_string(), current_omission: s_curs, max_omission: s_max, frequency: s_freq, avg_omission: s_avg });

    // Big
    let big_flags: Vec<bool> = special_vec.iter().map(|&x| x.map(|n| n >= 25 && n <= 49).unwrap_or(false)).collect();
    let (b_curs, b_max, b_freq, b_avg) = calculate_omission_stats(&big_flags, total_periods);
    size_stats.push(StatItem { label: "大".to_string(), current_omission: b_curs, max_omission: b_max, frequency: b_freq, avg_omission: b_avg });

    // 6. Special Tail Stats (0-9)
    let mut tail_stats = Vec::new();
    for t in 0..=9 {
        let flags: Vec<bool> = special_vec.iter().map(|&x| x.map(|n| n % 10 == t).unwrap_or(false)).collect();
        let (curs, max_o, freq, avg) = calculate_omission_stats(&flags, total_periods);
        tail_stats.push(StatItem {
            label: format!("{}尾", t),
            current_omission: curs,
            max_omission: max_o,
            frequency: freq,
            avg_omission: avg,
        });
    }

    // 7. Normal Number Stats (1-49 in ANY of n1-n6)
    let mut normal_stats = Vec::new();
    for num in 1..=49 {
        let flags: Vec<bool> = (0..total_periods).map(|i| {
             n1_vec[i] == Some(num) || 
             n2_vec[i] == Some(num) || 
             n3_vec[i] == Some(num) || 
             n4_vec[i] == Some(num) || 
             n5_vec[i] == Some(num) || 
             n6_vec[i] == Some(num)
        }).collect();
        
        let (curs, max_o, freq, avg) = calculate_omission_stats(&flags, total_periods);
        normal_stats.push(StatItem {
            label: num.to_string(),
            current_omission: curs,
            max_omission: max_o,
            frequency: freq,
            avg_omission: avg,
        });
    }

    Ok(StatisticsReport {
        special_number: special_stats,
        special_zodiac: zodiac_stats,
        special_color: color_stats,
        special_odd: odd_stats,
        special_size: size_stats,
        special_tail: tail_stats,
        normal_number: normal_stats,
    })
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

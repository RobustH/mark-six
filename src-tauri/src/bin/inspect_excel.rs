use calamine::{Reader, Xlsx, open_workbook};
use std::env;

fn main() {
    let path = "C:/Users/Administrator/Desktop/mark-six/data/2026.xlsx";
    let mut workbook: Xlsx<_> = open_workbook(path).expect("Cannot open file");
    if let Some(Ok(range)) = workbook.worksheet_range_at(0) {
        let headers: Vec<_> = range.rows().next().unwrap().iter().map(|c| c.to_string()).collect();
        println!("Headers: {:?}", headers);
        for row in range.rows().skip(1).take(5) {
            println!("Row: {:?}", row);
        }
    }
}

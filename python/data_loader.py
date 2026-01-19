import pandas as pd
import numpy as np

# --- 常量定义 ---

RED_WAVE = {1, 2, 7, 8, 12, 13, 18, 19, 23, 24, 29, 30, 34, 35, 40, 45, 46}
BLUE_WAVE = {3, 4, 9, 10, 14, 15, 20, 25, 26, 31, 36, 37, 41, 42, 47, 48}
GREEN_WAVE = {5, 6, 11, 16, 17, 21, 22, 27, 28, 32, 33, 38, 39, 43, 44, 49}

WUXING_MAP = {
    0: {1,2,9,10,17,18,25,26,33,34,41,42},      # 金
    1: {3,4,11,12,19,20,27,28,35,36,43,44},      # 木
    2: {5,6,13,14,21,22,29,30,37,38,45,46},      # 水
    3: {7,8,15,16,23,24,31,32,39,40,47,48},      # 火
    4: {49}                                      # 土
}

# 生肖映射参考：0=鼠, 11=猪
# 这通常取决于年份。我们将实施动态检查。
# 标准序列：鼠、牛、虎、兔、龙、蛇、马、羊、猴、鸡、狗、猪
# 每年 01 号对应当年生肖。
# 例如：2024 年是龙年，所以 01 号是龙，02 号是兔（通常是逆序映射）。
# 生肖序列（循环）：鼠(0), 牛(1), 虎(2), 兔(3), 龙(4), 蛇(5), 马(6), 羊(7), 猴(8), 鸡(9), 狗(10), 猪(11)
# 如果年份是龙(4):
# 01 -> 龙(4)
# 02 -> 兔(3)
# ...
# 计算公式：zodiac_idx = (year_zodiac_idx - (number - 1)) % 12
# 验证：
# 01 -> (4 - 0) % 12 = 4 (龙) 正确。
# 02 -> (4 - 1) % 12 = 3 (兔) 正确。
# 13 -> (4 - 12) % 12 = -8 % 12 = 4 (龙) 正确。

# 近年年份对应的 01 号生肖索引 (鼠=0, ..., 龙=4, 蛇=5, 马=6)
YEAR_ZODIAC_MAP = {
    2023: 3, # 兔
    2024: 4, # 龙
    2025: 5, # 蛇
    2026: 6, # 马
}

def get_color_map():
    # 0=红, 1=蓝, 2=绿
    color_map = {}
    for n in range(1, 50):
        if n in RED_WAVE: color_map[n] = 0
        elif n in BLUE_WAVE: color_map[n] = 1
        else: color_map[n] = 2
    return color_map

def get_wuxing_map():
    wx_map = {}
    for k, s in WUXING_MAP.items():
        for n in s:
            wx_map[n] = k
    return wx_map

COLOR_MAP = get_color_map()
WX_MAP = get_wuxing_map()

def load_data(file_path: str) -> pd.DataFrame:
    """加载 feather 数据并注入静态属性"""
    try:
        df = pd.read_feather(file_path)
    except Exception as e:
        raise FileNotFoundError(f"无法读取 feather 文件: {e}")

    # 确保日期列是 datetime 类型
    if not np.issubdtype(df['date'].dtype, np.datetime64):
        df['date'] = pd.to_datetime(df['date'])

    # --- 数据增强 (Enrichment) ---
    
    # 1. 特码属性
    # 波色
    df['sp_color'] = df['special'].map(COLOR_MAP).astype('uint8')
    
    # 五行
    df['sp_wuxing'] = df['special'].map(WX_MAP).fillna(4).astype('uint8') # 缺失则默认为土
    
    # 单双 (0=双, 1=单)
    df['sp_parity'] = (df['special'] % 2).astype('uint8')
    
    # 大小 (0=小 1-24, 1=大 25-49)
    # 根据 PRD 6.2.2: 大(25-49), 小(1-24)
    df['sp_size'] = np.where(df['special'] >= 25, 1, 0).astype('uint8')
    
    # 尾数 (0-9)
    df['sp_tail'] = (df['special'] % 10).astype('uint8')
    
    # 生肖 (基于年份动态计算)
    # 我们假设 'year' 列存在且正确
    
    # 确保 year 列存在
    if 'year' not in df.columns:
        df['year'] = df['date'].dt.year
    else:
        df['year'] = pd.to_numeric(df['year'], errors='coerce').fillna(0).astype('int')

    def calc_zodiac(row):
        try:
            year = int(row['year'])
        except:
            year = 0 # Default fallback
            
        # 基础算法：(year - 2008) % 12
        # 2008 是鼠年(0)。2024 - 2008 = 16 % 12 = 4 (龙)。正确。
        base_zodiac = (year - 2008) % 12
        
        # 计算号码对应的生肖
        # 01 号对应 base_zodiac
        # n 号对应 (base_zodiac - (n - 1)) % 12
        z_idx = (base_zodiac - (row['special'] - 1)) % 12
        return z_idx

    df['sp_zodiac'] = df.apply(calc_zodiac, axis=1).astype('uint8')

    return df

if __name__ == "__main__":
    # 测试代码
    import sys
    # 模拟路径
    path = r'f:\demo\mark-six\app\data\history.feather'
    try:
        df = load_data(path)
        print("数据加载并增强成功。")
        print(df[['period', 'year', 'special', 'sp_zodiac', 'sp_color']].head())
    except Exception as e:
        print(e)

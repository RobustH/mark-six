import pandas as pd
import numpy as np

def calculate_omission(series: pd.Series) -> pd.Series:
    """
    Calculate current omission for a series of values.
    Returns a series where each value represents how many periods since the last occurrence.
    """
    # 1. Create a boolean mask for each unique value (One-Hot-like but for all uniques?)
    # No, that's too heavy.
    # We want: for each row, what is the omission of the CURRENT value? 
    # OR: for each row, what is the omission of TARGET value?
    
    # Actually, for "Replay", we need the omission state of ALL possible values at that time point.
    # But usually, strategies only care about the omission of the specific value they are checking,
    # OR they check "is red wave omission > 10".
    
    # To support O(1) replay, we probably want to pre-calculate omission for ALL dimensions/values.
    # Dimensions: 
    # - Special Number (1-49)
    # - Special Zodiac (0-11)
    # - Special Color (0-2)
    # - Special Parity (0-1)
    # - Special Size (0-1)
    
    # We can create columns like: `omission_sp_color_0` (Red Omission), `omission_sp_color_1` (Blue)...
    pass

def precompute_omissions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorized calculation of omissions for known dimensions.
    Adds columns: `om_color_0`, `om_color_1`, `om_zodiac_0`...
    """
    # Helper to calculate omission for a specific binary condition or value match
    # Algorithm:
    # 1. Identify hits: mask = (df[col] == target)
    # 2. Cumulative count of periods?
    # Better: Groupby cumcount? No.
    # Pandas approach:
    #   groups = mask.cumsum()
    #   omission = df.groupby(groups).cumcount() 
    #   Wait, if hit, omission is 0. If miss, omission increases.
    
    stats_df = pd.DataFrame(index=df.index)
    
    # Dimension: Color (0, 1, 2)
    for val in [0, 1, 2]:
        mask = (df['sp_color'] == val)
        # Reset group on hit
        # groups increments on every hit
        groups = mask.cumsum()
        # cumcount gives 0, 1, 2... within the group.
        # If row is a hit (mask=True), it belongs to the NEW group (k). cumcount is 0.
        # If row is a miss (mask=False), it belongs to group (k). cumcount increments.
        # BUT: mask.cumsum() increments ON the hit row.
        
        # 稳健的方法：
        # 对于每一行，获取最后一次看到该值的索引并向下填充。
        last_seen = pd.Series(np.where(mask, df.index, np.nan), index=df.index).ffill()
        omission = df.index - last_seen
        
        # 处理当前命中情况：如果 mask 为 True，则遗漏为 0。
        # 验证：如果第 5 行命中，last_seen=5，5-5=0。正确。
        # 第 6 行未命中，last_seen=5，6-5=1。正确。
        
        # 将 NaN（从未出现过）填充为 index + 1（自开始以来的遗漏数）
        omission = omission.fillna(pd.Series(df.index + 1, index=df.index))
        stats_df[f'om_color_{val}'] = omission.astype('uint16')


    # 维度：生肖 (0..11)
    for val in range(12):
        mask = (df['sp_zodiac'] == val)
        last_seen = pd.Series(np.where(mask, df.index, np.nan), index=df.index).ffill()
        omission = (df.index - last_seen).fillna(pd.Series(df.index + 1, index=df.index))
        stats_df[f'om_zodiac_{val}'] = omission.astype('uint16')

    # 维度：五行 (0..4) - 暂时跳过，数据中没有此列
    # for val in range(5):
    #     mask = (df['sp_wuxing'] == val)
    #     last_seen = pd.Series(np.where(mask, df.index, np.nan), index=df.index).ffill()
    #     omission = (df.index - last_seen).fillna(pd.Series(df.index + 1, index=df.index))
    #     stats_df[f'om_wuxing_{val}'] = omission.astype('uint16')

    # 维度：大小 (0, 1)
    for val in [0, 1]:
        mask = (df['sp_size'] == val)
        last_seen = pd.Series(np.where(mask, df.index, np.nan), index=df.index).ffill()
        omission = (df.index - last_seen).fillna(pd.Series(df.index + 1, index=df.index))
        stats_df[f'om_size_{val}'] = omission.astype('uint16')

    # 维度：单双 (0, 1)
    for val in [0, 1]:
        mask = (df['sp_parity'] == val)
        last_seen = pd.Series(np.where(mask, df.index, np.nan), index=df.index).ffill()
        omission = (df.index - last_seen).fillna(pd.Series(df.index + 1, index=df.index))
        stats_df[f'om_parity_{val}'] = omission.astype('uint16')

    # 维度：尾数 (0..9)
    for val in range(10):
        mask = (df['sp_tail'] == val)
        last_seen = pd.Series(np.where(mask, df.index, np.nan), index=df.index).ffill()
        omission = (df.index - last_seen).fillna(pd.Series(df.index + 1, index=df.index))
        stats_df[f'om_tail_{val}'] = omission.astype('uint16')
        
    return stats_df

def calc_all_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算所有统计指标的主入口（遗漏、热度等）。
    返回与 df 对齐的 DataFrame，仅包含统计列。
    """
    # 确保索引是递增的整数 (0..N)
    df = df.reset_index(drop=True)
    
    # 1. 遗漏值计算
    om_df = precompute_omissions(df)
    
    # 2. 热度计算 (最近 100 期的频率)
    # 对布尔掩码进行滚动求和
    hot_df = pd.DataFrame(index=df.index)
    
    # 波色热度
    for val in [0, 1, 2]:
        mask = (df['sp_color'] == val).astype(int)
        hot_df[f'freq_color_{val}_100'] = mask.rolling(100, min_periods=1).sum().fillna(0).astype('uint16')
    
    # 生肖热度
    for val in range(12):
        mask = (df['sp_zodiac'] == val).astype(int)
        hot_df[f'freq_zodiac_{val}_100'] = mask.rolling(100, min_periods=1).sum().fillna(0).astype('uint16')
        
    # 五行热度 - 暂时跳过，数据中没有此列
    # for val in range(5):
    #     mask = (df['sp_wuxing'] == val).astype(int)
    #     hot_df[f'freq_wuxing_{val}_100'] = mask.rolling(100, min_periods=1).sum().fillna(0).astype('uint16')

    # 大小热度
    for val in [0, 1]:
        mask = (df['sp_size'] == val).astype(int)
        hot_df[f'freq_size_{val}_100'] = mask.rolling(100, min_periods=1).sum().fillna(0).astype('uint16')

    # 单双热度
    for val in [0, 1]:
        mask = (df['sp_parity'] == val).astype(int)
        hot_df[f'freq_parity_{val}_100'] = mask.rolling(100, min_periods=1).sum().fillna(0).astype('uint16')

    # 尾数热度
    for val in range(10):
        mask = (df['sp_tail'] == val).astype(int)
        hot_df[f'freq_tail_{val}_100'] = mask.rolling(100, min_periods=1).sum().fillna(0).astype('uint16')

    return pd.concat([om_df, hot_df], axis=1)

if __name__ == "__main__":
    from data_loader import load_data
    path = r'f:\demo\mark-six\app\data\history.feather'
    try:
        df = load_data(path)
        stats = calc_all_stats(df)
        print("统计指标计算完成。")
        print(stats.columns.tolist()[:10])
        print(stats.tail())
        
        # 验证逻辑：
        # 检查当值出现时，遗漏值是否重置为 0。
        check = pd.concat([df[['sp_color', 'sp_zodiac']], stats[['om_color_0', 'om_color_1', 'om_zodiac_0']]], axis=1)
        print(check.tail(10))
    except Exception as e:
        print(e)

export type RuleType = 'omission' | 'window_stat' | 'streak';
export type Target = 'special' | 'normal';
export type Dimension = 'number' | 'zodiac' | 'color' | 'wuxing' | 'parity' | 'size' | 'tail';
export type Operator = '>=' | '<=' | '==' | '>' | '<';

export interface Condition {
    id: string; // Unique ID for keying in UI loops
    type: RuleType;
    target: Target;
    dimension: Dimension;
    value: string | number;
    operator: Operator;
    threshold: number;
    window?: number; // Only for window_stat
}

export interface EntryRuleConfig {
    id: string;
    name: string;
    description?: string;
    conditions: Condition[];
    logicOperator: 'AND' | 'OR';
    createTime: number;
    updateTime: number;
}

export type MoneyMode = 'fixed' | 'martingale' | 'paroli' | 'loss_recovery';

export interface MoneyRuleConfig {
    id: string;
    name: string;
    mode: MoneyMode;
    params: {
        baseBet: number;
        multipliers?: number[]; // For martingale sequence e.g. [1, 2, 4, 8]
        maxBet?: number;    // Risk control
        stopLoss?: number;  // Risk control
        takeProfit?: number; // Risk control
    };
    createTime: number;
    updateTime: number;
}

export interface StrategyConfig {
    id: string;
    name: string;
    description?: string;
    entryRuleId: string; // Ref to EntryRuleConfig
    moneyRuleId: string; // Ref to MoneyRuleConfig
    oddsProfileId?: string; // Ref to OddsProfile (optional)
    createTime: number;
    updateTime: number;
}

// 玩法类型枚举 (PRD 6.3)
export type PlayType =
    | 'special_number'   // 特码号码
    | 'special_color'    // 特码波色 (红/蓝/绿)
    | 'special_zodiac'   // 特码生肖
    | 'special_parity'   // 特码单双
    | 'special_size';    // 特码大小

// 赔率配置接口 (PRD 6.4)
export interface OddsProfile {
    id: string;
    name: string;
    playType: PlayType;        // 对应玩法类型
    odds: number;              // 固定赔率
    rebate?: number;           // 返水 (可选)
    maxPayout?: number;        // 封顶收益
    version: string;           // 赔率版本号
    validFrom?: string;        // 生效开始日期 (YYYY-MM-DD)
    validTo?: string;          // 生效结束日期 (YYYY-MM-DD)
    createTime: number;
    updateTime: number;
}

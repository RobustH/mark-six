export type RuleType = 'omission' | 'window_stat' | 'streak';
export type Target = 'special' | 'normal';
export type Dimension = 'number' | 'zodiac' | 'color' | 'wuxing' | 'parity' | 'size';
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

export type MoneyMode = 'fixed' | 'martingale' | 'paroli';

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
    createTime: number;
    updateTime: number;
}

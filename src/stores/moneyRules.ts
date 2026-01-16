import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { MoneyRuleConfig } from '../types/strategy';
import Database from '@tauri-apps/plugin-sql';

export const useMoneyRulesStore = defineStore('moneyRules', () => {
    const rules = ref<MoneyRuleConfig[]>([]);
    let db: Database | null = null;

    // 初始化数据库并从 SQL 加载规则
    const init = async () => {
        if (db) return;
        try {
            db = await Database.load('sqlite:mark_six.db');
            const result = await db.select<any[]>('SELECT * FROM money_rules');
            rules.value = result.map(row => ({
                ...row,
                params: JSON.parse(row.params) // 解析参数 JSON
            }));
        } catch (e) {
            console.error('初始化 Money 数据库失败', e);
        }
    };

    // 生成唯一 ID
    const generateId = () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    };

    const addRule = async (rule: Omit<MoneyRuleConfig, 'id' | 'createTime' | 'updateTime'>) => {
        const newRule: MoneyRuleConfig = {
            ...rule,
            id: generateId(),
            createTime: Date.now(),
            updateTime: Date.now(),
        };

        if (db) {
            await db.execute(
                'INSERT INTO money_rules (id, name, mode, params, createTime, updateTime) VALUES ($1, $2, $3, $4, $5, $6)',
                [newRule.id, newRule.name, newRule.mode, JSON.stringify(newRule.params), newRule.createTime, newRule.updateTime]
            );
        }
        rules.value.push(newRule);
    };

    const updateRule = async (id: string, updatedRule: Partial<Omit<MoneyRuleConfig, 'id' | 'createTime'>>) => {
        const index = rules.value.findIndex((r) => r.id === id);
        if (index !== -1) {
            const newRule = {
                ...rules.value[index],
                ...updatedRule,
                updateTime: Date.now(),
            };

            if (db) {
                await db.execute(
                    'UPDATE money_rules SET name = $1, mode = $2, params = $3, updateTime = $4 WHERE id = $5',
                    [newRule.name, newRule.mode, JSON.stringify(newRule.params), newRule.updateTime, id]
                );
            }
            rules.value[index] = newRule;
        }
    };

    const deleteRule = async (id: string) => {
        const index = rules.value.findIndex((r) => r.id === id);
        if (index !== -1) {
            if (db) {
                await db.execute('DELETE FROM money_rules WHERE id = $1', [id]);
            }
            rules.value.splice(index, 1);
        }
    };

    const getRuleById = (id: string) => {
        return rules.value.find((r) => r.id === id);
    };

    return {
        rules,
        init,
        addRule,
        updateRule,
        deleteRule,
        getRuleById,
    };
});

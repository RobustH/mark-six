import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { EntryRuleConfig } from '../types/strategy';
import Database from '@tauri-apps/plugin-sql';

export const useEntryRulesStore = defineStore('entryRules', () => {
    const rules = ref<EntryRuleConfig[]>([]);
    let db: Database | null = null;

    // 初始化数据库并加载现有规则
    const init = async () => {
        if (db) return;
        try {
            db = await Database.load('sqlite:mark_six.db');
            const result = await db.select<any[]>('SELECT * FROM entry_rules');
            rules.value = result.map(row => ({
                ...row,
                conditions: JSON.parse(row.conditions) // 将 JSON 字符串解析为数组
            }));
        } catch (e) {
            console.error('初始化 Entry 数据库失败', e);
        }
    };

    // 生成唯一 ID
    const generateId = () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    };

    const addRule = async (rule: Omit<EntryRuleConfig, 'id' | 'createTime' | 'updateTime'>) => {
        const newRule: EntryRuleConfig = {
            ...rule,
            id: generateId(),
            createTime: Date.now(),
            updateTime: Date.now(),
        };

        if (db) {
            await db.execute(
                'INSERT INTO entry_rules (id, name, description, conditions, logicOperator, createTime, updateTime) VALUES ($1, $2, $3, $4, $5, $6, $7)',
                [newRule.id, newRule.name, newRule.description || '', JSON.stringify(newRule.conditions), newRule.logicOperator, newRule.createTime, newRule.updateTime]
            );
        }
        rules.value.push(newRule);
    };

    const updateRule = async (id: string, updatedRule: Partial<Omit<EntryRuleConfig, 'id' | 'createTime'>>) => {
        const index = rules.value.findIndex((r) => r.id === id);
        if (index !== -1) {
            const newRule = {
                ...rules.value[index],
                ...updatedRule,
                updateTime: Date.now(),
            };

            if (db) {
                await db.execute(
                    'UPDATE entry_rules SET name = $1, description = $2, conditions = $3, logicOperator = $4, updateTime = $5 WHERE id = $6',
                    [newRule.name, newRule.description || '', JSON.stringify(newRule.conditions), newRule.logicOperator, newRule.updateTime, id]
                );
            }
            rules.value[index] = newRule;
        }
    };

    const deleteRule = async (id: string) => {
        const index = rules.value.findIndex((r) => r.id === id);
        if (index !== -1) {
            if (db) {
                await db.execute('DELETE FROM entry_rules WHERE id = $1', [id]);
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

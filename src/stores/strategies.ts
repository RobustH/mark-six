import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { StrategyConfig } from '../types/strategy';
import Database from '@tauri-apps/plugin-sql';

export const useStrategiesStore = defineStore('strategies', () => {
    const strategies = ref<StrategyConfig[]>([]);
    let db: Database | null = null;

    // 初始化数据库并加载策略
    const init = async () => {
        if (db) return;
        try {
            db = await Database.load('sqlite:mark_six.db');
            const result = await db.select<StrategyConfig[]>('SELECT * FROM strategies');
            strategies.value = result;
        } catch (e) {
            console.error('初始化 Strategies 数据库失败', e);
        }
    };

    // 生成唯一 ID
    const generateId = () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    };

    const addStrategy = async (strategy: Omit<StrategyConfig, 'id' | 'createTime' | 'updateTime'>) => {
        const newStrategy: StrategyConfig = {
            ...strategy,
            id: generateId(),
            createTime: Date.now(),
            updateTime: Date.now(),
        };

        if (db) {
            await db.execute(
                'INSERT INTO strategies (id, name, description, entryRuleId, moneyRuleId, oddsProfileId, createTime, updateTime) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)',
                [newStrategy.id, newStrategy.name, newStrategy.description || '', newStrategy.entryRuleId, newStrategy.moneyRuleId, newStrategy.oddsProfileId || null, newStrategy.createTime, newStrategy.updateTime]
            );
        }
        strategies.value.push(newStrategy);
    };

    const updateStrategy = async (id: string, updated: Partial<Omit<StrategyConfig, 'id' | 'createTime'>>) => {
        const index = strategies.value.findIndex((s) => s.id === id);
        if (index !== -1) {
            const newStrategy = {
                ...strategies.value[index],
                ...updated,
                updateTime: Date.now(),
            };

            if (db) {
                await db.execute(
                    'UPDATE strategies SET name = $1, description = $2, entryRuleId = $3, moneyRuleId = $4, oddsProfileId = $5, updateTime = $6 WHERE id = $7',
                    [newStrategy.name, newStrategy.description || '', newStrategy.entryRuleId, newStrategy.moneyRuleId, newStrategy.oddsProfileId || null, newStrategy.updateTime, id]
                );
            }
            strategies.value[index] = newStrategy;
        }
    };

    const deleteStrategy = async (id: string) => {
        const index = strategies.value.findIndex((s) => s.id === id);
        if (index !== -1) {
            if (db) {
                await db.execute('DELETE FROM strategies WHERE id = $1', [id]);
            }
            strategies.value.splice(index, 1);
        }
    };

    return {
        strategies,
        init,
        addStrategy,
        updateStrategy,
        deleteStrategy
    };
});

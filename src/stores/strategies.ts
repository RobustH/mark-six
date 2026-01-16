import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { StrategyConfig } from '../types/strategy';

export const useStrategiesStore = defineStore('strategies', () => {
    const strategies = ref<StrategyConfig[]>([]);

    const generateId = () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    };

    const addStrategy = (strategy: Omit<StrategyConfig, 'id' | 'createTime' | 'updateTime'>) => {
        const newStrategy: StrategyConfig = {
            ...strategy,
            id: generateId(),
            createTime: Date.now(),
            updateTime: Date.now(),
        };
        strategies.value.push(newStrategy);
    };

    const updateStrategy = (id: string, updated: Partial<Omit<StrategyConfig, 'id' | 'createTime'>>) => {
        const index = strategies.value.findIndex((s) => s.id === id);
        if (index !== -1) {
            strategies.value[index] = {
                ...strategies.value[index],
                ...updated,
                updateTime: Date.now(),
            };
        }
    };

    const deleteStrategy = (id: string) => {
        const index = strategies.value.findIndex((s) => s.id === id);
        if (index !== -1) {
            strategies.value.splice(index, 1);
        }
    };

    return {
        strategies,
        addStrategy,
        updateStrategy,
        deleteStrategy
    };
});

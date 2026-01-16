import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { MoneyRuleConfig } from '../types/strategy';

export const useMoneyRulesStore = defineStore('moneyRules', () => {
    const rules = ref<MoneyRuleConfig[]>([]);

    const generateId = () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    };

    const addRule = (rule: Omit<MoneyRuleConfig, 'id' | 'createTime' | 'updateTime'>) => {
        const newRule: MoneyRuleConfig = {
            ...rule,
            id: generateId(),
            createTime: Date.now(),
            updateTime: Date.now(),
        };
        rules.value.push(newRule);
    };

    const updateRule = (id: string, updatedRule: Partial<Omit<MoneyRuleConfig, 'id' | 'createTime'>>) => {
        const index = rules.value.findIndex((r) => r.id === id);
        if (index !== -1) {
            rules.value[index] = {
                ...rules.value[index],
                ...updatedRule,
                updateTime: Date.now(),
            };
        }
    };

    const deleteRule = (id: string) => {
        const index = rules.value.findIndex((r) => r.id === id);
        if (index !== -1) {
            rules.value.splice(index, 1);
        }
    };

    const getRuleById = (id: string) => {
        return rules.value.find((r) => r.id === id);
    };

    return {
        rules,
        addRule,
        updateRule,
        deleteRule,
        getRuleById,
    };
});

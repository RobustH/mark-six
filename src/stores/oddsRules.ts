import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { OddsProfile, PlayType } from '../types/strategy';
import Database from '@tauri-apps/plugin-sql';

export const useOddsRulesStore = defineStore('oddsRules', () => {
    const profiles = ref<OddsProfile[]>([]);
    let db: Database | null = null;

    // 初始化数据库并加载现有赔率配置
    const init = async () => {
        if (db) return;
        try {
            db = await Database.load('sqlite:mark_six.db');
            const result = await db.select<any[]>('SELECT * FROM odds_profiles');
            profiles.value = result.map(row => ({
                ...row,
                odds: Number(row.odds),
                rebate: row.rebate != null ? Number(row.rebate) : undefined,
                maxPayout: row.maxPayout != null ? Number(row.maxPayout) : undefined,
            }));
        } catch (e) {
            console.error('初始化赔率数据库失败', e);
        }
    };

    // 生成唯一 ID
    const generateId = () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    };

    const addProfile = async (profile: Omit<OddsProfile, 'id' | 'createTime' | 'updateTime'>) => {
        const newProfile: OddsProfile = {
            ...profile,
            id: generateId(),
            createTime: Date.now(),
            updateTime: Date.now(),
        };

        if (db) {
            await db.execute(
                `INSERT INTO odds_profiles (id, name, playType, odds, rebate, maxPayout, version, validFrom, validTo, createTime, updateTime) 
                 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`,
                [
                    newProfile.id,
                    newProfile.name,
                    newProfile.playType,
                    newProfile.odds,
                    newProfile.rebate ?? null,
                    newProfile.maxPayout ?? null,
                    newProfile.version,
                    newProfile.validFrom ?? null,
                    newProfile.validTo ?? null,
                    newProfile.createTime,
                    newProfile.updateTime
                ]
            );
        }
        profiles.value.push(newProfile);
    };

    const updateProfile = async (id: string, updatedProfile: Partial<Omit<OddsProfile, 'id' | 'createTime'>>) => {
        const index = profiles.value.findIndex((p) => p.id === id);
        if (index !== -1) {
            const newProfile = {
                ...profiles.value[index],
                ...updatedProfile,
                updateTime: Date.now(),
            };

            if (db) {
                await db.execute(
                    `UPDATE odds_profiles SET name = $1, playType = $2, odds = $3, rebate = $4, maxPayout = $5, version = $6, validFrom = $7, validTo = $8, updateTime = $9 WHERE id = $10`,
                    [
                        newProfile.name,
                        newProfile.playType,
                        newProfile.odds,
                        newProfile.rebate ?? null,
                        newProfile.maxPayout ?? null,
                        newProfile.version,
                        newProfile.validFrom ?? null,
                        newProfile.validTo ?? null,
                        newProfile.updateTime,
                        id
                    ]
                );
            }
            profiles.value[index] = newProfile;
        }
    };

    const deleteProfile = async (id: string) => {
        const index = profiles.value.findIndex((p) => p.id === id);
        if (index !== -1) {
            if (db) {
                await db.execute('DELETE FROM odds_profiles WHERE id = $1', [id]);
            }
            profiles.value.splice(index, 1);
        }
    };

    const getProfileById = (id: string) => {
        return profiles.value.find((p) => p.id === id);
    };

    // 获取指定玩法类型的所有赔率配置
    const getProfilesByPlayType = (playType: PlayType) => {
        return profiles.value.filter((p) => p.playType === playType);
    };

    return {
        profiles,
        init,
        addProfile,
        updateProfile,
        deleteProfile,
        getProfileById,
        getProfilesByPlayType,
    };
});

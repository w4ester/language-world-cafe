/**
 * Language Learning Progress Tracker
 * Tracks XP, badges, streaks, and achievements
 * All data stored in localStorage for privacy
 *
 * w4ester & ai orchestration
 */

class ProgressTracker {
    constructor() {
        this.data = this.loadProgress();
        this.badges = this.initializeBadges();
        this.achievements = this.initializeAchievements();
    }

    /**
     * Load progress from localStorage
     */
    loadProgress() {
        const stored = localStorage.getItem('language_learning_progress');
        if (stored) {
            return JSON.parse(stored);
        }

        // Default progress data
        return {
            totalXP: 0,
            level: 1,
            conversationsCompleted: 0,
            wordsSpoken: 0,
            languagesPracticed: { en: 0, es: 0 },
            scenarios: {
                server_only: 0,
                customer_only: 0,
                host_only: 0,
                full_experience: 0
            },
            streak: {
                current: 0,
                longest: 0,
                lastPracticeDate: null
            },
            badges: [],
            achievements: [],
            sessions: [],
            grammarScores: [],
            startDate: new Date().toISOString()
        };
    }

    /**
     * Save progress to localStorage
     */
    saveProgress() {
        localStorage.setItem('language_learning_progress', JSON.stringify(this.data));
        this.triggerProgressUpdate();
    }

    /**
     * Initialize badge definitions
     */
    initializeBadges() {
        return {
            // Conversation badges
            'first-steps': {
                id: 'first-steps',
                name: 'First Steps',
                icon: '👣',
                description: 'Complete your first conversation',
                requirement: () => this.data.conversationsCompleted >= 1
            },
            'chatterbox': {
                id: 'chatterbox',
                name: 'Chatterbox',
                icon: '💬',
                description: 'Complete 10 conversations',
                requirement: () => this.data.conversationsCompleted >= 10
            },
            'conversation-master': {
                id: 'conversation-master',
                name: 'Conversation Master',
                icon: '🎭',
                description: 'Complete 50 conversations',
                requirement: () => this.data.conversationsCompleted >= 50
            },

            // Language badges
            'bilingual-beginner': {
                id: 'bilingual-beginner',
                name: 'Bilingual Beginner',
                icon: '🌍',
                description: 'Practice in both English and Spanish',
                requirement: () => this.data.languagesPracticed.en > 0 && this.data.languagesPracticed.es > 0
            },
            'polyglot': {
                id: 'polyglot',
                name: 'Polyglot',
                icon: '🗣️',
                description: 'Practice 25+ times in each language',
                requirement: () => this.data.languagesPracticed.en >= 25 && this.data.languagesPracticed.es >= 25
            },

            // Role badges
            'customer-confident': {
                id: 'customer-confident',
                name: 'Customer Confident',
                icon: '😊',
                description: 'Complete 10 conversations as a customer',
                requirement: () => this.data.scenarios.server_only >= 10
            },
            'server-savvy': {
                id: 'server-savvy',
                name: 'Server Savvy',
                icon: '🍽️',
                description: 'Complete 10 conversations as a server',
                requirement: () => this.data.scenarios.customer_only >= 10
            },
            'host-hero': {
                id: 'host-hero',
                name: 'Host Hero',
                icon: '👋',
                description: 'Complete 10 conversations as a host',
                requirement: () => this.data.scenarios.host_only >= 10
            },
            'role-master': {
                id: 'role-master',
                name: 'Role Master',
                icon: '🎪',
                description: 'Master all three roles (10+ each)',
                requirement: () =>
                    this.data.scenarios.server_only >= 10 &&
                    this.data.scenarios.customer_only >= 10 &&
                    this.data.scenarios.host_only >= 10
            },

            // Streak badges
            'consistent-learner': {
                id: 'consistent-learner',
                name: 'Consistent Learner',
                icon: '📅',
                description: 'Practice 3 days in a row',
                requirement: () => this.data.streak.current >= 3
            },
            'dedicated-student': {
                id: 'dedicated-student',
                name: 'Dedicated Student',
                icon: '🔥',
                description: 'Practice 7 days in a row',
                requirement: () => this.data.streak.current >= 7
            },
            'unstoppable': {
                id: 'unstoppable',
                name: 'Unstoppable',
                icon: '⚡',
                description: 'Practice 30 days in a row',
                requirement: () => this.data.streak.current >= 30
            },

            // Quality badges
            'grammar-guru': {
                id: 'grammar-guru',
                name: 'Grammar Guru',
                icon: '📚',
                description: 'Get 10 "Excellent" grammar scores',
                requirement: () => {
                    const excellent = this.data.grammarScores.filter(s => s === 'Excellent').length;
                    return excellent >= 10;
                }
            },
            'pronunciation-pro': {
                id: 'pronunciation-pro',
                name: 'Pronunciation Pro',
                icon: '🎤',
                description: 'Complete 50 voice conversations',
                requirement: () => this.data.wordsSpoken >= 500
            },

            // Milestone badges
            'hundred-club': {
                id: 'hundred-club',
                name: '100 Club',
                icon: '💯',
                description: 'Reach 100 XP',
                requirement: () => this.data.totalXP >= 100
            },
            'level-five': {
                id: 'level-five',
                name: 'Level 5 Legend',
                icon: '🌟',
                description: 'Reach Level 5',
                requirement: () => this.data.level >= 5
            },
            'level-ten': {
                id: 'level-ten',
                name: 'Level 10 Champion',
                icon: '👑',
                description: 'Reach Level 10',
                requirement: () => this.data.level >= 10
            }
        };
    }

    /**
     * Initialize achievement definitions
     */
    initializeAchievements() {
        return {
            // Hidden achievements (surprise bonuses)
            'night-owl': {
                id: 'night-owl',
                name: 'Night Owl',
                icon: '🦉',
                description: 'Practice after midnight',
                xp: 25,
                hidden: true
            },
            'early-bird': {
                id: 'early-bird',
                name: 'Early Bird',
                icon: '🐦',
                description: 'Practice before 6 AM',
                xp: 25,
                hidden: true
            },
            'marathon-session': {
                id: 'marathon-session',
                name: 'Marathon Session',
                icon: '🏃',
                description: 'Practice for 30+ minutes straight',
                xp: 50,
                hidden: true
            },
            'perfect-score': {
                id: 'perfect-score',
                name: 'Perfect Score',
                icon: '💎',
                description: 'Get 5 "Excellent" scores in a row',
                xp: 100,
                hidden: true
            }
        };
    }

    /**
     * Record a conversation session
     */
    recordConversation(details) {
        const session = {
            timestamp: new Date().toISOString(),
            scenario: details.scenario || 'unknown',
            language: details.language || 'en',
            exchanges: details.exchanges || 0,
            grammarScore: details.grammarScore || null,
            duration: details.duration || 0,
            xpEarned: 0
        };

        // Calculate XP for this session
        let xp = 10; // Base XP per conversation

        // Bonus XP
        if (session.exchanges >= 5) xp += 10; // Meaningful conversation
        if (session.exchanges >= 10) xp += 15; // Long conversation
        if (session.grammarScore === 'Excellent') xp += 20;
        if (session.grammarScore === 'Good') xp += 10;
        if (session.duration >= 300) xp += 25; // 5+ minute session

        session.xpEarned = xp;

        // Update progress
        this.data.conversationsCompleted++;
        this.data.totalXP += xp;
        this.data.wordsSpoken += details.exchanges * 10; // Estimate
        this.data.languagesPracticed[session.language]++;
        this.data.scenarios[session.scenario]++;

        if (session.grammarScore) {
            this.data.grammarScores.push(session.grammarScore);
        }

        this.data.sessions.push(session);

        // Update streak
        this.updateStreak();

        // Update level
        this.updateLevel();

        // Check for new badges
        this.checkBadges();

        // Check for achievements
        this.checkAchievements(details);

        this.saveProgress();

        return {
            xpEarned: xp,
            totalXP: this.data.totalXP,
            level: this.data.level,
            newBadges: this.getNewBadges()
        };
    }

    /**
     * Update streak
     */
    updateStreak() {
        const today = new Date().toDateString();
        const lastPractice = this.data.streak.lastPracticeDate;

        if (!lastPractice) {
            // First ever practice
            this.data.streak.current = 1;
            this.data.streak.longest = 1;
        } else {
            const lastDate = new Date(lastPractice).toDateString();
            const yesterday = new Date(Date.now() - 86400000).toDateString();

            if (lastDate === today) {
                // Already practiced today, no change
                return;
            } else if (lastDate === yesterday) {
                // Practiced yesterday, continue streak
                this.data.streak.current++;
                if (this.data.streak.current > this.data.streak.longest) {
                    this.data.streak.longest = this.data.streak.current;
                }
            } else {
                // Streak broken
                this.data.streak.current = 1;
            }
        }

        this.data.streak.lastPracticeDate = new Date().toISOString();
    }

    /**
     * Update level based on XP
     */
    updateLevel() {
        // Level formula: level = floor(sqrt(totalXP / 10))
        // Level 1: 0 XP
        // Level 2: 40 XP
        // Level 3: 90 XP
        // Level 4: 160 XP
        // Level 5: 250 XP
        // etc.
        const newLevel = Math.floor(Math.sqrt(this.data.totalXP / 10)) + 1;

        if (newLevel > this.data.level) {
            const oldLevel = this.data.level;
            this.data.level = newLevel;
            this.triggerLevelUp(oldLevel, newLevel);
        }
    }

    /**
     * Check for newly earned badges
     */
    checkBadges() {
        const newBadges = [];

        Object.values(this.badges).forEach(badge => {
            if (!this.data.badges.includes(badge.id) && badge.requirement()) {
                this.data.badges.push(badge.id);
                newBadges.push(badge);
            }
        });

        return newBadges;
    }

    /**
     * Check for achievements
     */
    checkAchievements(details) {
        const newAchievements = [];
        const hour = new Date().getHours();

        // Night Owl
        if (hour >= 0 && hour < 6 && !this.data.achievements.includes('night-owl')) {
            this.data.achievements.push('night-owl');
            this.data.totalXP += this.achievements['night-owl'].xp;
            newAchievements.push(this.achievements['night-owl']);
        }

        // Early Bird
        if (hour >= 5 && hour < 7 && !this.data.achievements.includes('early-bird')) {
            this.data.achievements.push('early-bird');
            this.data.totalXP += this.achievements['early-bird'].xp;
            newAchievements.push(this.achievements['early-bird']);
        }

        // Marathon Session
        if (details.duration >= 1800 && !this.data.achievements.includes('marathon-session')) {
            this.data.achievements.push('marathon-session');
            this.data.totalXP += this.achievements['marathon-session'].xp;
            newAchievements.push(this.achievements['marathon-session']);
        }

        // Perfect Score
        const recentScores = this.data.grammarScores.slice(-5);
        if (recentScores.length === 5 && recentScores.every(s => s === 'Excellent')) {
            if (!this.data.achievements.includes('perfect-score')) {
                this.data.achievements.push('perfect-score');
                this.data.totalXP += this.achievements['perfect-score'].xp;
                newAchievements.push(this.achievements['perfect-score']);
            }
        }

        return newAchievements;
    }

    /**
     * Get XP needed for next level
     */
    getXPForNextLevel() {
        const nextLevel = this.data.level + 1;
        return Math.pow(nextLevel - 1, 2) * 10;
    }

    /**
     * Get XP needed for current level
     */
    getXPForCurrentLevel() {
        return Math.pow(this.data.level - 1, 2) * 10;
    }

    /**
     * Get progress to next level (0-1)
     */
    getLevelProgress() {
        const currentLevelXP = this.getXPForCurrentLevel();
        const nextLevelXP = this.getXPForNextLevel();
        const xpInLevel = this.data.totalXP - currentLevelXP;
        const xpNeeded = nextLevelXP - currentLevelXP;
        return Math.min(xpInLevel / xpNeeded, 1);
    }

    /**
     * Get all earned badges
     */
    getEarnedBadges() {
        return this.data.badges.map(id => this.badges[id]).filter(b => b);
    }

    /**
     * Get all available badges
     */
    getAllBadges() {
        return Object.values(this.badges).map(badge => ({
            ...badge,
            earned: this.data.badges.includes(badge.id)
        }));
    }

    /**
     * Get newly earned badges (not yet shown)
     */
    getNewBadges() {
        // This would need additional state tracking
        // For now, just return empty array
        return [];
    }

    /**
     * Get statistics summary
     */
    getStats() {
        return {
            level: this.data.level,
            totalXP: this.data.totalXP,
            xpToNextLevel: this.getXPForNextLevel() - this.data.totalXP,
            levelProgress: this.getLevelProgress(),
            conversationsCompleted: this.data.conversationsCompleted,
            wordsSpoken: this.data.wordsSpoken,
            currentStreak: this.data.streak.current,
            longestStreak: this.data.streak.longest,
            badgesEarned: this.data.badges.length,
            totalBadges: Object.keys(this.badges).length,
            achievementsEarned: this.data.achievements.length,
            daysActive: this.getDaysActive(),
            favoriteLanguage: this.getFavoriteLanguage(),
            favoriteScenario: this.getFavoriteScenario()
        };
    }

    /**
     * Get days active
     */
    getDaysActive() {
        const uniqueDays = new Set(
            this.data.sessions.map(s => new Date(s.timestamp).toDateString())
        );
        return uniqueDays.size;
    }

    /**
     * Get favorite language
     */
    getFavoriteLanguage() {
        const { en, es } = this.data.languagesPracticed;
        if (en > es) return 'English';
        if (es > en) return 'Spanish';
        return 'Both equally';
    }

    /**
     * Get favorite scenario
     */
    getFavoriteScenario() {
        const scenarios = this.data.scenarios;
        const max = Math.max(...Object.values(scenarios));
        const favorite = Object.keys(scenarios).find(k => scenarios[k] === max);

        const names = {
            'server_only': 'Ordering (Customer)',
            'customer_only': 'Serving (Server)',
            'host_only': 'Greeting (Host)',
            'full_experience': 'Full Experience'
        };

        return names[favorite] || 'None yet';
    }

    /**
     * Reset all progress
     */
    resetProgress() {
        if (confirm('Are you sure you want to reset all progress? This cannot be undone.')) {
            localStorage.removeItem('language_learning_progress');
            this.data = this.loadProgress();
            this.saveProgress();
            return true;
        }
        return false;
    }

    /**
     * Export progress data
     */
    exportProgress() {
        const dataStr = JSON.stringify(this.data, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);

        const link = document.createElement('a');
        link.href = url;
        link.download = `language-learning-progress-${new Date().toISOString().split('T')[0]}.json`;
        link.click();

        URL.revokeObjectURL(url);
    }

    /**
     * Import progress data
     */
    importProgress(jsonData) {
        try {
            const imported = JSON.parse(jsonData);
            this.data = imported;
            this.saveProgress();
            return true;
        } catch (error) {
            console.error('Failed to import progress:', error);
            return false;
        }
    }

    /**
     * Trigger progress update event
     */
    triggerProgressUpdate() {
        window.dispatchEvent(new CustomEvent('progressUpdate', {
            detail: this.getStats()
        }));
    }

    /**
     * Trigger level up event
     */
    triggerLevelUp(oldLevel, newLevel) {
        window.dispatchEvent(new CustomEvent('levelUp', {
            detail: { oldLevel, newLevel, totalXP: this.data.totalXP }
        }));
    }
}

// Global instance
window.progressTracker = new ProgressTracker();

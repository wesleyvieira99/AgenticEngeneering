const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({ testDir: '.', testMatch: '*.spec.js', timeout: 60000, workers: 1, reporter: [['list'], ['json', {outputFile: '../../artifacts/e2e-results.json'}]], use: {headless: true, screenshot:'only-on-failure', trace:'retain-on-failure'}, outputDir:'../../artifacts/playwright' });

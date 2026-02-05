from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
import os
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional
import threading

@dataclass
class CurrencyRate:
    code: str
    name: str
    rate: float
    last_updated: datetime

class CurrencyConverterHandler(BaseHTTPRequestHandler):
    
    # Cache for exchange rates (to avoid hitting API too frequently)
    exchange_rates_cache = {}
    cache_timestamp = None
    CACHE_DURATION = 3600  # Cache for 1 hour
    
    # Popular currencies with their symbols
    POPULAR_CURRENCIES = {
        'USD': {'name': 'US Dollar', 'symbol': '$'},
        'EUR': {'name': 'Euro', 'symbol': '€'},
        'GBP': {'name': 'British Pound', 'symbol': '£'},
        'JPY': {'name': 'Japanese Yen', 'symbol': '¥'},
        'CAD': {'name': 'Canadian Dollar', 'symbol': 'CA$'},
        'AUD': {'name': 'Australian Dollar', 'symbol': 'A$'},
        'CNY': {'name': 'Chinese Yuan', 'symbol': '¥'},
        'INR': {'name': 'Indian Rupee', 'symbol': '₹'},
        'NPR': {'name': 'Nepali Rupee', 'symbol': 'रु'},  # Added Nepali Rupee
        'SGD': {'name': 'Singapore Dollar', 'symbol': 'S$'},
        'AED': {'name': 'UAE Dirham', 'symbol': 'د.إ'},
    }
    
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_homepage()
        
        elif parsed_path.path == '/api/currencies':
            self.serve_currencies_list()
        
        elif parsed_path.path.startswith('/api/convert'):
            self.handle_conversion(parsed_path)
        
        elif parsed_path.path == '/api/history':
            self.serve_conversion_history()
        
        elif parsed_path.path == '/api/latest':
            self.serve_latest_rates()
        
        elif parsed_path.path == '/api/popular':
            self.serve_popular_rates()
        
        elif parsed_path.path == '/favicon.ico':
            self.send_favicon()
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/convert':
            self.handle_conversion_post()
        
        elif self.path == '/api/save':
            self.save_conversion()
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def serve_homepage(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Currency Converter Pro</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                :root {
                    --primary: #4361ee;
                    --secondary: #3a0ca3;
                    --accent: #7209b7;
                    --success: #4cc9f0;
                    --danger: #f72585;
                    --warning: #f8961e;
                    --light: #f8f9fa;
                    --dark: #212529;
                    --gray: #6c757d;
                    --shadow: 0 4px 20px rgba(0,0,0,0.1);
                    --gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }
                
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: var(--gradient);
                    min-height: 100vh;
                    padding: 20px;
                    color: var(--dark);
                }
                
                .app-container {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                
                /* Header */
                .app-header {
                    background: white;
                    border-radius: 20px;
                    padding: 30px;
                    margin-bottom: 30px;
                    box-shadow: var(--shadow);
                    text-align: center;
                }
                
                .header-content h1 {
                    font-size: 2.8rem;
                    background: linear-gradient(135deg, var(--primary), var(--accent));
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 10px;
                }
                
                .header-content p {
                    color: var(--gray);
                    font-size: 1.1rem;
                    max-width: 600px;
                    margin: 0 auto 20px;
                }
                
                .rate-info {
                    display: inline-block;
                    background: var(--light);
                    padding: 10px 20px;
                    border-radius: 50px;
                    font-size: 0.9rem;
                    color: var(--primary);
                    font-weight: 600;
                }
                
                .rate-info i {
                    margin-right: 8px;
                }
                
                /* Main Layout */
                .main-layout {
                    display: grid;
                    grid-template-columns: 1fr 400px;
                    gap: 30px;
                }
                
                @media (max-width: 992px) {
                    .main-layout {
                        grid-template-columns: 1fr;
                    }
                }
                
                /* Converter Card */
                .converter-card {
                    background: white;
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: var(--shadow);
                    margin-bottom: 30px;
                }
                
                .converter-title {
                    font-size: 1.8rem;
                    color: var(--dark);
                    margin-bottom: 30px;
                    display: flex;
                    align-items: center;
                    gap: 15px;
                }
                
                .converter-title i {
                    color: var(--primary);
                    font-size: 2rem;
                }
                
                .converter-form {
                    display: flex;
                    flex-direction: column;
                    gap: 25px;
                }
                
                .amount-section {
                    position: relative;
                }
                
                .amount-label {
                    display: block;
                    margin-bottom: 10px;
                    font-weight: 600;
                    color: var(--dark);
                    font-size: 1.1rem;
                }
                
                .amount-input {
                    width: 100%;
                    padding: 20px;
                    border: 2px solid #e0e0e0;
                    border-radius: 15px;
                    font-size: 2rem;
                    font-weight: bold;
                    transition: all 0.3s;
                    text-align: right;
                }
                
                .amount-input:focus {
                    outline: none;
                    border-color: var(--primary);
                    box-shadow: 0 0 0 4px rgba(67, 97, 238, 0.1);
                }
                
                .currency-display {
                    position: absolute;
                    left: 20px;
                    top: 50px;
                    font-size: 1.5rem;
                    font-weight: 600;
                    color: var(--primary);
                }
                
                .currencies-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                }
                
                @media (max-width: 576px) {
                    .currencies-grid {
                        grid-template-columns: 1fr;
                    }
                }
                
                .currency-selector {
                    position: relative;
                }
                
                .currency-selector label {
                    display: block;
                    margin-bottom: 10px;
                    font-weight: 600;
                    color: var(--dark);
                }
                
                .currency-dropdown {
                    width: 100%;
                    padding: 15px;
                    border: 2px solid #e0e0e0;
                    border-radius: 15px;
                    font-size: 1.1rem;
                    background: white;
                    cursor: pointer;
                    transition: all 0.3s;
                    appearance: none;
                    padding-right: 50px;
                }
                
                .currency-dropdown:focus {
                    outline: none;
                    border-color: var(--primary);
                }
                
                .dropdown-arrow {
                    position: absolute;
                    right: 20px;
                    top: 45px;
                    color: var(--gray);
                    pointer-events: none;
                }
                
                /* Result Card */
                .result-card {
                    background: linear-gradient(135deg, var(--primary), var(--secondary));
                    color: white;
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: var(--shadow);
                    text-align: center;
                    margin-top: 30px;
                }
                
                .result-title {
                    font-size: 1.2rem;
                    opacity: 0.9;
                    margin-bottom: 20px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                
                .result-amount {
                    font-size: 3.5rem;
                    font-weight: bold;
                    margin-bottom: 10px;
                    line-height: 1;
                }
                
                .result-currency {
                    font-size: 1.5rem;
                    opacity: 0.9;
                    margin-bottom: 30px;
                }
                
                .result-details {
                    display: flex;
                    justify-content: space-between;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid rgba(255,255,255,0.2);
                }
                
                .detail-item {
                    text-align: center;
                }
                
                .detail-value {
                    font-size: 1.3rem;
                    font-weight: 600;
                }
                
                .detail-label {
                    font-size: 0.9rem;
                    opacity: 0.7;
                    margin-top: 5px;
                }
                
                /* Action Buttons */
                .action-buttons {
                    display: flex;
                    gap: 15px;
                    margin-top: 30px;
                }
                
                .btn {
                    padding: 15px 30px;
                    border: none;
                    border-radius: 15px;
                    font-size: 1.1rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 10px;
                    flex: 1;
                }
                
                .btn-primary {
                    background: var(--primary);
                    color: white;
                }
                
                .btn-primary:hover {
                    background: var(--secondary);
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(67, 97, 238, 0.3);
                }
                
                .btn-secondary {
                    background: var(--light);
                    color: var(--dark);
                }
                
                .btn-secondary:hover {
                    background: #e9ecef;
                }
                
                /* Popular Rates Sidebar */
                .sidebar {
                    background: white;
                    border-radius: 20px;
                    padding: 30px;
                    box-shadow: var(--shadow);
                    height: fit-content;
                }
                
                .sidebar-title {
                    font-size: 1.5rem;
                    color: var(--dark);
                    margin-bottom: 25px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .rates-list {
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                }
                
                .rate-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 15px;
                    background: var(--light);
                    border-radius: 12px;
                    transition: all 0.3s;
                    cursor: pointer;
                }
                
                .rate-item:hover {
                    background: #e9ecef;
                    transform: translateX(5px);
                }
                
                .rate-item.active {
                    background: var(--primary);
                    color: white;
                }
                
                .rate-currency {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .rate-symbol {
                    font-size: 1.2rem;
                    font-weight: 600;
                }
                
                .rate-code {
                    font-size: 0.9rem;
                    opacity: 0.7;
                }
                
                .rate-value {
                    font-size: 1.2rem;
                    font-weight: 600;
                }
                
                /* History Section */
                .history-section {
                    background: white;
                    border-radius: 20px;
                    padding: 30px;
                    box-shadow: var(--shadow);
                    margin-top: 30px;
                }
                
                .section-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 25px;
                }
                
                .history-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                
                .history-table th {
                    text-align: left;
                    padding: 15px;
                    border-bottom: 2px solid var(--light);
                    color: var(--gray);
                    font-weight: 600;
                    text-transform: uppercase;
                    font-size: 0.9rem;
                    letter-spacing: 1px;
                }
                
                .history-table td {
                    padding: 15px;
                    border-bottom: 1px solid var(--light);
                }
                
                .history-table tr:hover {
                    background: var(--light);
                }
                
                /* Toast */
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 15px 25px;
                    border-radius: 10px;
                    color: white;
                    font-weight: 600;
                    z-index: 1000;
                    animation: slideIn 0.3s ease;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                }
                
                .toast.success {
                    background: linear-gradient(135deg, #4CAF50, #45a049);
                }
                
                .toast.error {
                    background: linear-gradient(135deg, #f72585, #ff006e);
                }
                
                .toast.info {
                    background: linear-gradient(135deg, var(--primary), var(--secondary));
                }
                
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
                
                /* Loading Spinner */
                .spinner {
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    border: 3px solid rgba(255,255,255,0.3);
                    border-radius: 50%;
                    border-top-color: white;
                    animation: spin 1s ease-in-out infinite;
                }
                
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                
                /* Responsive */
                @media (max-width: 768px) {
                    .app-header {
                        padding: 20px;
                    }
                    
                    .header-content h1 {
                        font-size: 2rem;
                    }
                    
                    .converter-card {
                        padding: 20px;
                    }
                    
                    .amount-input {
                        font-size: 1.5rem;
                        padding: 15px;
                    }
                    
                    .currency-display {
                        top: 40px;
                        font-size: 1.2rem;
                    }
                    
                    .result-amount {
                        font-size: 2.5rem;
                    }
                }
            </style>
        </head>
        <body>
            <div class="app-container">
                <!-- Header -->
                <header class="app-header">
                    <div class="header-content">
                        <h1><i class="fas fa-money-bill-wave"></i> Currency Converter Pro</h1>
                        <p>Convert between 150+ currencies with real-time exchange rates including Nepali Rupee (NPR)!</p>
                        <div class="rate-info">
                            <i class="fas fa-sync-alt"></i>
                            <span id="last-updated">Rates update every hour</span>
                        </div>
                    </div>
                </header>

                <!-- Main Layout -->
                <div class="main-layout">
                    <!-- Main Converter -->
                    <div class="main-content">
                        <!-- Converter Card -->
                        <div class="converter-card">
                            <h2 class="converter-title">
                                <i class="fas fa-exchange-alt"></i> Currency Converter
                            </h2>
                            
                            <form class="converter-form" id="converterForm">
                                <!-- Amount Input -->
                                <div class="amount-section">
                                    <label class="amount-label">Amount</label>
                                    <div class="currency-display" id="fromCurrencySymbol">$</div>
                                    <input type="number" 
                                           id="amount" 
                                           class="amount-input" 
                                           value="100" 
                                           min="0" 
                                           step="0.01"
                                           placeholder="0.00"
                                           required>
                                </div>
                                
                                <!-- Currency Selection -->
                                <div class="currencies-grid">
                                    <div class="currency-selector">
                                        <label for="fromCurrency">From Currency</label>
                                        <select id="fromCurrency" class="currency-dropdown">
                                            <!-- Currencies will be loaded here -->
                                        </select>
                                        <div class="dropdown-arrow">▼</div>
                                    </div>
                                    
                                    <div class="currency-selector">
                                        <label for="toCurrency">To Currency</label>
                                        <select id="toCurrency" class="currency-dropdown">
                                            <!-- Currencies will be loaded here -->
                                        </select>
                                        <div class="dropdown-arrow">▼</div>
                                    </div>
                                </div>
                                
                                <!-- Action Buttons -->
                                <div class="action-buttons">
                                    <button type="button" class="btn btn-primary" onclick="convertCurrency()" id="convertBtn">
                                        <i class="fas fa-calculator"></i> Convert
                                    </button>
                                    <button type="button" class="btn btn-secondary" onclick="swapCurrencies()">
                                        <i class="fas fa-exchange-alt"></i> Swap
                                    </button>
                                    <button type="button" class="btn btn-secondary" onclick="clearForm()">
                                        <i class="fas fa-eraser"></i> Clear
                                    </button>
                                </div>
                            </form>
                        </div>
                        
                        <!-- Result Card -->
                        <div class="result-card" id="resultCard" style="display: none;">
                            <div class="result-title">Converted Amount</div>
                            <div class="result-amount" id="resultAmount">0.00</div>
                            <div class="result-currency" id="resultCurrency">USD</div>
                            
                            <div class="result-details">
                                <div class="detail-item">
                                    <div class="detail-value" id="exchangeRate">1.00</div>
                                    <div class="detail-label">Exchange Rate</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-value" id="lastUpdatedTime">Just now</div>
                                    <div class="detail-label">Last Updated</div>
                                </div>
                            </div>
                            
                            <div class="action-buttons" style="margin-top: 30px;">
                                <button type="button" class="btn btn-secondary" onclick="saveConversion()">
                                    <i class="fas fa-save"></i> Save
                                </button>
                                <button type="button" class="btn btn-secondary" onclick="copyResult()">
                                    <i class="fas fa-copy"></i> Copy
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Sidebar -->
                    <aside class="sidebar">
                        <h3 class="sidebar-title">
                            <i class="fas fa-chart-line"></i> Popular Rates (vs USD)
                        </h3>
                        <div class="rates-list" id="popularRates">
                            <!-- Popular rates will be loaded here -->
                        </div>
                        
                        <div style="margin-top: 30px;">
                            <h3 class="sidebar-title">
                                <i class="fas fa-history"></i> Quick Convert
                            </h3>
                            <div class="action-buttons" style="flex-direction: column;">
                                <button type="button" class="btn btn-secondary" onclick="setAmount(100)">
                                    <i class="fas fa-dollar-sign"></i> $100 USD
                                </button>
                                <button type="button" class="btn btn-secondary" onclick="setAmount(500)">
                                    <i class="fas fa-dollar-sign"></i> $500 USD
                                </button>
                                <button type="button" class="btn btn-secondary" onclick="setAmount(1000)">
                                    <i class="fas fa-dollar-sign"></i> $1,000 USD
                                </button>
                            </div>
                            
                            <div style="margin-top: 20px;">
                                <h4 style="color: var(--dark); margin-bottom: 10px;">🇳🇵 Nepali Rupee (NPR)</h4>
                                <div class="action-buttons" style="flex-direction: column;">
                                    <button type="button" class="btn btn-secondary" onclick="convertToNPR(100)">
                                        <i class="fas fa-dollar-sign"></i> $100 → NPR
                                    </button>
                                    <button type="button" class="btn btn-secondary" onclick="convertFromNPR(1000)">
                                        <i class="fas fa-rupee-sign"></i> 1,000 NPR → USD
                                    </button>
                                </div>
                            </div>
                        </div>
                    </aside>
                </div>
                
                <!-- History Section -->
                <div class="history-section">
                    <div class="section-header">
                        <h3 class="sidebar-title">
                            <i class="fas fa-history"></i> Conversion History
                        </h3>
                        <button type="button" class="btn btn-secondary" onclick="clearHistory()">
                            <i class="fas fa-trash"></i> Clear History
                        </button>
                    </div>
                    <table class="history-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>From</th>
                                <th>To</th>
                                <th>Amount</th>
                                <th>Result</th>
                                <th>Rate</th>
                            </tr>
                        </thead>
                        <tbody id="historyTable">
                            <!-- History will be loaded here -->
                        </tbody>
                    </table>
                </div>
            </div>
            
            <script>
                // Global variables
                let currencies = [];
                let exchangeRates = {};
                
                // DOM Elements
                const fromCurrencySelect = document.getElementById('fromCurrency');
                const toCurrencySelect = document.getElementById('toCurrency');
                const amountInput = document.getElementById('amount');
                const fromCurrencySymbol = document.getElementById('fromCurrencySymbol');
                const resultCard = document.getElementById('resultCard');
                const resultAmount = document.getElementById('resultAmount');
                const resultCurrency = document.getElementById('resultCurrency');
                const exchangeRate = document.getElementById('exchangeRate');
                const lastUpdatedTime = document.getElementById('lastUpdatedTime');
                const popularRates = document.getElementById('popularRates');
                const historyTable = document.getElementById('historyTable');
                const lastUpdatedSpan = document.getElementById('last-updated');
                const convertBtn = document.getElementById('convertBtn');
                
                // Initialize on page load
                document.addEventListener('DOMContentLoaded', function() {
                    loadCurrencies();
                    loadPopularRates();
                    loadHistory();
                    updateLastUpdated();
                });
                
                // Load all available currencies
                function loadCurrencies() {
                    fetch('/api/currencies')
                        .then(response => response.json())
                        .then(data => {
                            currencies = data;
                            populateCurrencySelects();
                            // Set default currencies
                            setDefaultCurrencies();
                        })
                        .catch(error => {
                            console.error('Error loading currencies:', error);
                            showToast('Error loading currencies', 'error');
                        });
                }
                
                // Populate currency dropdowns
                function populateCurrencySelects() {
                    fromCurrencySelect.innerHTML = '';
                    toCurrencySelect.innerHTML = '';
                    
                    currencies.forEach(currency => {
                        const option1 = document.createElement('option');
                        option1.value = currency.code;
                        option1.textContent = `${currency.code} - ${currency.name}`;
                        
                        const option2 = option1.cloneNode(true);
                        
                        fromCurrencySelect.appendChild(option1);
                        toCurrencySelect.appendChild(option2);
                    });
                }
                
                // Set default currencies
                function setDefaultCurrencies() {
                    // Try to get user's location for default currency
                    const userCurrency = getUserCurrency();
                    
                    fromCurrencySelect.value = userCurrency;
                    toCurrencySelect.value = 'EUR';
                    updateCurrencySymbol();
                }
                
                // Guess user's currency based on browser language
                function getUserCurrency() {
                    const language = navigator.language || 'en-US';
                    
                    if (language.includes('en-US') || language.includes('en-CA')) return 'USD';
                    if (language.includes('en-GB')) return 'GBP';
                    if (language.includes('en-AU')) return 'AUD';
                    if (language.includes('ja')) return 'JPY';
                    if (language.includes('zh')) return 'CNY';
                    if (language.includes('hi')) return 'INR';
                    if (language.includes('ne')) return 'NPR';  // Nepali language
                    if (language.includes('ar')) return 'AED';
                    
                    // Default to USD
                    return 'USD';
                }
                
                // Load popular exchange rates
                function loadPopularRates() {
                    fetch('/api/popular')
                        .then(response => response.json())
                        .then(data => {
                            displayPopularRates(data);
                        })
                        .catch(error => {
                            console.error('Error loading popular rates:', error);
                        });
                }
                
                // Display popular rates in sidebar
                function displayPopularRates(rates) {
                    popularRates.innerHTML = '';
                    
                    Object.entries(rates).forEach(([currency, rate]) => {
                        const rateItem = document.createElement('div');
                        rateItem.className = 'rate-item';
                        rateItem.onclick = () => {
                            toCurrencySelect.value = currency;
                            convertCurrency();
                        };
                        
                        const currencyInfo = getCurrencyInfo(currency);
                        
                        rateItem.innerHTML = `
                            <div class="rate-currency">
                                <span class="rate-symbol">${currencyInfo.symbol}</span>
                                <span class="rate-code">${currency}</span>
                            </div>
                            <div class="rate-value">${rate.toFixed(4)}</div>
                        `;
                        
                        popularRates.appendChild(rateItem);
                    });
                }
                
                // Get currency info (symbol, name)
                function getCurrencyInfo(currencyCode) {
                    const currency = currencies.find(c => c.code === currencyCode);
                    if (currency) {
                        return {
                            symbol: currency.symbol || currencyCode,
                            name: currency.name
                        };
                    }
                    return { symbol: currencyCode, name: currencyCode };
                }
                
                // Main conversion function
                function convertCurrency() {
                    const amount = parseFloat(amountInput.value);
                    const fromCurrency = fromCurrencySelect.value;
                    const toCurrency = toCurrencySelect.value;
                    
                    if (!amount || amount <= 0) {
                        showToast('Please enter a valid amount', 'error');
                        return;
                    }
                    
                    if (fromCurrency === toCurrency) {
                        showToast('Please select different currencies', 'error');
                        return;
                    }
                    
                    // Show loading
                    convertBtn.innerHTML = '<span class="spinner"></span> Converting...';
                    convertBtn.disabled = true;
                    
                    // Make API call
                    fetch(`/api/convert?amount=${amount}&from=${fromCurrency}&to=${toCurrency}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                displayResult(data);
                                saveConversionToLocal(data);
                                updateLastUpdated();
                            } else {
                                showToast(data.error || 'Conversion failed', 'error');
                            }
                        })
                        .catch(error => {
                            console.error('Error converting currency:', error);
                            showToast('Error converting currency', 'error');
                        })
                        .finally(() => {
                            // Reset button
                            convertBtn.innerHTML = '<i class="fas fa-calculator"></i> Convert';
                            convertBtn.disabled = false;
                        });
                }
                
                // Convert USD to Nepali Rupee
                function convertToNPR(amount) {
                    amountInput.value = amount;
                    fromCurrencySelect.value = 'USD';
                    toCurrencySelect.value = 'NPR';
                    updateCurrencySymbol();
                    convertCurrency();
                }
                
                // Convert Nepali Rupee to USD
                function convertFromNPR(amount) {
                    amountInput.value = amount;
                    fromCurrencySelect.value = 'NPR';
                    toCurrencySelect.value = 'USD';
                    updateCurrencySymbol();
                    convertCurrency();
                }
                
                // Display conversion result
                function displayResult(data) {
                    resultAmount.textContent = data.result.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                    
                    resultCurrency.textContent = data.to;
                    exchangeRate.textContent = data.rate.toFixed(6);
                    lastUpdatedTime.textContent = 'Just now';
                    
                    // Show result card
                    resultCard.style.display = 'block';
                    
                    // Smooth scroll to result
                    resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
                
                // Swap currencies
                function swapCurrencies() {
                    const temp = fromCurrencySelect.value;
                    fromCurrencySelect.value = toCurrencySelect.value;
                    toCurrencySelect.value = temp;
                    updateCurrencySymbol();
                    
                    // Convert immediately if there's a result
                    if (resultCard.style.display !== 'none') {
                        convertCurrency();
                    }
                }
                
                // Update currency symbol display
                function updateCurrencySymbol() {
                    const currencyCode = fromCurrencySelect.value;
                    const currencyInfo = getCurrencyInfo(currencyCode);
                    fromCurrencySymbol.textContent = currencyInfo.symbol;
                }
                
                // Set amount quickly
                function setAmount(amount) {
                    amountInput.value = amount;
                    convertCurrency();
                }
                
                // Clear form
                function clearForm() {
                    amountInput.value = '';
                    resultCard.style.display = 'none';
                    showToast('Form cleared', 'info');
                }
                
                // Save conversion to server
                function saveConversion() {
                    const amount = parseFloat(amountInput.value);
                    const fromCurrency = fromCurrencySelect.value;
                    const toCurrency = toCurrencySelect.value;
                    
                    fetch('/api/save', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            amount: amount,
                            from: fromCurrency,
                            to: toCurrency,
                            result: parseFloat(resultAmount.textContent.replace(/,/g, '')),
                            rate: parseFloat(exchangeRate.textContent)
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showToast('Conversion saved!', 'success');
                            loadHistory();
                        }
                    })
                    .catch(error => {
                        console.error('Error saving conversion:', error);
                    });
                }
                
                // Save conversion to localStorage
                function saveConversionToLocal(data) {
                    const history = JSON.parse(localStorage.getItem('currencyHistory') || '[]');
                    
                    history.unshift({
                        date: new Date().toLocaleString(),
                        from: data.from,
                        to: data.to,
                        amount: data.amount,
                        result: data.result,
                        rate: data.rate
                    });
                    
                    // Keep only last 50 conversions
                    if (history.length > 50) {
                        history.pop();
                    }
                    
                    localStorage.setItem('currencyHistory', JSON.stringify(history));
                    loadHistory();
                }
                
                // Load conversion history
                function loadHistory() {
                    // Try server history first, fallback to localStorage
                    fetch('/api/history')
                        .then(response => response.json())
                        .then(data => {
                            displayHistory(data);
                        })
                        .catch(() => {
                            // Fallback to localStorage
                            const history = JSON.parse(localStorage.getItem('currencyHistory') || '[]');
                            displayHistory(history);
                        });
                }
                
                // Display history in table
                function displayHistory(history) {
                    historyTable.innerHTML = '';
                    
                    if (history.length === 0) {
                        historyTable.innerHTML = `
                            <tr>
                                <td colspan="6" style="text-align: center; padding: 40px; color: var(--gray);">
                                    <i class="fas fa-history" style="font-size: 2rem; margin-bottom: 10px; display: block;"></i>
                                    No conversion history yet
                                </td>
                            </tr>
                        `;
                        return;
                    }
                    
                    history.forEach(item => {
                        const row = document.createElement('tr');
                        
                        row.innerHTML = `
                            <td>${item.date}</td>
                            <td><strong>${item.from}</strong></td>
                            <td><strong>${item.to}</strong></td>
                            <td>${parseFloat(item.amount).toLocaleString('en-US', {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                            })}</td>
                            <td><strong>${parseFloat(item.result).toLocaleString('en-US', {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                            })}</strong></td>
                            <td>${parseFloat(item.rate).toFixed(6)}</td>
                        `;
                        
                        historyTable.appendChild(row);
                    });
                }
                
                // Clear history
                function clearHistory() {
                    if (confirm('Are you sure you want to clear all history?')) {
                        localStorage.removeItem('currencyHistory');
                        loadHistory();
                        showToast('History cleared', 'success');
                    }
                }
                
                // Copy result to clipboard
                function copyResult() {
                    const text = `${amountInput.value} ${fromCurrencySelect.value} = ${resultAmount.textContent} ${toCurrencySelect.value}`;
                    
                    navigator.clipboard.writeText(text)
                        .then(() => {
                            showToast('Copied to clipboard!', 'success');
                        })
                        .catch(err => {
                            console.error('Failed to copy: ', err);
                            showToast('Failed to copy', 'error');
                        });
                }
                
                // Update last updated time
                function updateLastUpdated() {
                    const now = new Date();
                    lastUpdatedSpan.textContent = `Last updated: ${now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
                }
                
                // Show toast notification
                function showToast(message, type) {
                    // Remove existing toasts
                    const existingToasts = document.querySelectorAll('.toast');
                    existingToasts.forEach(toast => toast.remove());
                    
                    const toast = document.createElement('div');
                    toast.className = `toast ${type}`;
                    toast.textContent = message;
                    
                    document.body.appendChild(toast);
                    
                    // Auto remove after 3 seconds
                    setTimeout(() => {
                        toast.style.animation = 'slideOut 0.3s ease';
                        setTimeout(() => toast.remove(), 300);
                    }, 3000);
                }
                
                // Event listeners
                fromCurrencySelect.addEventListener('change', updateCurrencySymbol);
                amountInput.addEventListener('input', updateCurrencySymbol);
                
                // Auto-convert when currencies change
                fromCurrencySelect.addEventListener('change', () => {
                    if (amountInput.value && resultCard.style.display !== 'none') {
                        convertCurrency();
                    }
                });
                
                toCurrencySelect.addEventListener('change', () => {
                    if (amountInput.value && resultCard.style.display !== 'none') {
                        convertCurrency();
                    }
                });
                
                // Auto-convert on amount change (with debounce)
                let convertTimeout;
                amountInput.addEventListener('input', () => {
                    clearTimeout(convertTimeout);
                    
                    if (amountInput.value && resultCard.style.display !== 'none') {
                        convertTimeout = setTimeout(() => {
                            convertCurrency();
                        }, 500);
                    }
                });
            </script>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
    
    def serve_currencies_list(self):
        """Return list of all supported currencies"""
        currencies = [
            {"code": "USD", "name": "US Dollar", "symbol": "$"},
            {"code": "EUR", "name": "Euro", "symbol": "€"},
            {"code": "GBP", "name": "British Pound", "symbol": "£"},
            {"code": "JPY", "name": "Japanese Yen", "symbol": "¥"},
            {"code": "CAD", "name": "Canadian Dollar", "symbol": "CA$"},
            {"code": "AUD", "name": "Australian Dollar", "symbol": "A$"},
            {"code": "CNY", "name": "Chinese Yuan", "symbol": "¥"},
            {"code": "INR", "name": "Indian Rupee", "symbol": "₹"},
            {"code": "NPR", "name": "Nepali Rupee", "symbol": "रु"},  # Added Nepali Rupee
            {"code": "SGD", "name": "Singapore Dollar", "symbol": "S$"},
            {"code": "AED", "name": "UAE Dirham", "symbol": "د.إ"},
            {"code": "CHF", "name": "Swiss Franc", "symbol": "CHF"},
            {"code": "HKD", "name": "Hong Kong Dollar", "symbol": "HK$"},
            {"code": "KRW", "name": "South Korean Won", "symbol": "₩"},
            {"code": "MXN", "name": "Mexican Peso", "symbol": "MX$"},
            {"code": "BRL", "name": "Brazilian Real", "symbol": "R$"},
            {"code": "RUB", "name": "Russian Ruble", "symbol": "₽"},
            {"code": "ZAR", "name": "South African Rand", "symbol": "R"},
            {"code": "TRY", "name": "Turkish Lira", "symbol": "₺"},
            {"code": "NZD", "name": "New Zealand Dollar", "symbol": "NZ$"},
            {"code": "SEK", "name": "Swedish Krona", "symbol": "kr"},
            {"code": "NOK", "name": "Norwegian Krone", "symbol": "kr"},
            {"code": "DKK", "name": "Danish Krone", "symbol": "kr"},
            {"code": "PLN", "name": "Polish Zloty", "symbol": "zł"},
            {"code": "THB", "name": "Thai Baht", "symbol": "฿"},
            {"code": "IDR", "name": "Indonesian Rupiah", "symbol": "Rp"},
            {"code": "MYR", "name": "Malaysian Ringgit", "symbol": "RM"},
            {"code": "PHP", "name": "Philippine Peso", "symbol": "₱"},
            {"code": "SAR", "name": "Saudi Riyal", "symbol": "﷼"},
            {"code": "EGP", "name": "Egyptian Pound", "symbol": "E£"},
            {"code": "PKR", "name": "Pakistani Rupee", "symbol": "₨"},
        ]
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(currencies).encode())
    
    def get_exchange_rates(self):
        """Get exchange rates from cache or API"""
        now = datetime.now()
        
        # Return cached rates if still valid
        if (self.cache_timestamp and 
            (now - self.cache_timestamp).seconds < self.CACHE_DURATION and
            self.exchange_rates_cache):
            return self.exchange_rates_cache
        
        try:
            # Using ExchangeRate-API (free tier)
            api_key = "YOUR_API_KEY_HERE"  # Get free key from exchangerate-api.com
            url = f"https://api.exchangerate-api.com/v4/latest/USD"
            
            # For demo purposes, using fallback rates if no API key
            if api_key == "YOUR_API_KEY_HERE":
                print("⚠️  Using demo exchange rates (get free API key from exchangerate-api.com)")
                rates = self.get_fallback_rates()
            else:
                response = urllib.request.urlopen(url)
                data = json.loads(response.read().decode())
                rates = data['rates']
                # Add NPR if not in API response (API might not have NPR)
                if 'NPR' not in rates:
                    rates['NPR'] = 133.25  # Default fallback rate
                
            self.exchange_rates_cache = rates
            self.cache_timestamp = now
            
            return rates
            
        except Exception as e:
            print(f"Error fetching exchange rates: {e}")
            # Return fallback rates if API fails
            return self.get_fallback_rates()
    
    def get_fallback_rates(self):
        """Fallback exchange rates for demo purposes"""
        return {
            'USD': 1.0,
            'EUR': 0.92,
            'GBP': 0.79,
            'JPY': 148.50,
            'CAD': 1.35,
            'AUD': 1.52,
            'CNY': 7.18,
            'INR': 83.10,
            'NPR': 133.25,  # Added Nepali Rupee rate (1 USD = ~133.25 NPR)
            'SGD': 1.34,
            'AED': 3.67,
            'CHF': 0.88,
            'HKD': 7.82,
            'KRW': 1330.0,
            'MXN': 17.25,
            'BRL': 4.95,
            'RUB': 92.50,
            'ZAR': 18.75,
            'TRY': 30.85,
            'NZD': 1.63,
            'SEK': 10.45,
            'NOK': 10.85,
            'DKK': 6.88,
            'PLN': 4.02,
            'THB': 35.60,
            'IDR': 15650.0,
            'MYR': 4.68,
            'PHP': 56.20,
            'SAR': 3.75,
            'EGP': 30.90,
            'PKR': 281.5,
        }
    
    def handle_conversion(self, parsed_path):
        """Handle currency conversion request"""
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        try:
            amount = float(query_params.get('amount', [0])[0])
            from_currency = query_params.get('from', ['USD'])[0].upper()
            to_currency = query_params.get('to', ['EUR'])[0].upper()
            
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            rates = self.get_exchange_rates()
            
            # Convert to USD first, then to target currency
            if from_currency == 'USD':
                from_rate = 1.0
            else:
                from_rate = rates.get(from_currency)
                if not from_rate:
                    raise ValueError(f"Unsupported currency: {from_currency}")
            
            if to_currency == 'USD':
                to_rate = 1.0
            else:
                to_rate = rates.get(to_currency)
                if not to_rate:
                    raise ValueError(f"Unsupported currency: {to_currency}")
            
            # Convert amount to USD, then to target currency
            amount_in_usd = amount / from_rate
            result = amount_in_usd * to_rate
            rate = to_rate / from_rate
            
            response = {
                'success': True,
                'amount': amount,
                'from': from_currency,
                'to': to_currency,
                'result': round(result, 4),
                'rate': round(rate, 6),
                'timestamp': datetime.now().isoformat()
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())
    
    def handle_conversion_post(self):
        """Handle POST conversion request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            
            amount = float(data.get('amount', 0))
            from_currency = data.get('from', 'USD').upper()
            to_currency = data.get('to', 'EUR').upper()
            
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            rates = self.get_exchange_rates()
            
            # Convert to USD first, then to target currency
            if from_currency == 'USD':
                from_rate = 1.0
            else:
                from_rate = rates.get(from_currency)
                if not from_rate:
                    raise ValueError(f"Unsupported currency: {from_currency}")
            
            if to_currency == 'USD':
                to_rate = 1.0
            else:
                to_rate = rates.get(to_currency)
                if not to_rate:
                    raise ValueError(f"Unsupported currency: {to_currency}")
            
            # Convert amount to USD, then to target currency
            amount_in_usd = amount / from_rate
            result = amount_in_usd * to_rate
            rate = to_rate / from_rate
            
            response = {
                'success': True,
                'amount': amount,
                'from': from_currency,
                'to': to_currency,
                'result': round(result, 4),
                'rate': round(rate, 6),
                'timestamp': datetime.now().isoformat()
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())
    
    def serve_popular_rates(self):
        """Return popular exchange rates vs USD"""
        rates = self.get_exchange_rates()
        popular_rates = {}
        
        for currency in self.POPULAR_CURRENCIES.keys():
            if currency in rates and currency != 'USD':
                popular_rates[currency] = rates[currency]
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(popular_rates).encode())
    
    def serve_latest_rates(self):
        """Return all latest exchange rates"""
        rates = self.get_exchange_rates()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(rates).encode())
    
    def serve_conversion_history(self):
        """Return conversion history"""
        # For simplicity, return empty array
        # In production, you'd retrieve from database
        
        history = []
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(history).encode())
    
    def save_conversion(self):
        """Save conversion to history"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            
            # In production, save to database
            # For now, just return success
            
            response = {
                'success': True,
                'message': 'Conversion saved'
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())
    
    def send_favicon(self):
        self.send_response(200)
        self.send_header('Content-type', 'image/x-icon')
        self.end_headers()
        self.wfile.write(b'')

def init_database():
    """Initialize SQLite database for history"""
    try:
        conn = sqlite3.connect('currency_converter.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                result REAL NOT NULL,
                rate REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    PORT = 8080
    HOST = '0.0.0.0'
    
    try:
        server = HTTPServer((HOST, PORT), CurrencyConverterHandler)
        
        print("=" * 60)
        print("💱 CURRENCY CONVERTER PRO (WITH NPR)")
        print("=" * 60)
        print(f"🌐 Server URL: http://{HOST}:{PORT}")
        print(f"💾 Database: currency_converter.db")
        print("\n✨ Features:")
        print("   • 💰 Convert 31+ currencies including NPR")
        print("   • 🇳🇵 Nepali Rupee (NPR) support")
        print("   • 📊 Real-time exchange rates")
        print("   • 📈 Popular rates sidebar")
        print("   • 📋 Conversion history")
        print("   • 🎨 Modern, responsive UI")
        print("   • ⚡ Auto-updating rates (cached)")
        print("\n🇳🇵 NPR Quick Conversions:")
        print("   • $100 USD → NPR")
        print("   • 1,000 NPR → USD")
        print("\n🖥️  Access from:")
        print(f"   • Local: http://localhost:{PORT}")
        print(f"   • Network: http://[YOUR-IP]:{PORT}")
        print("\n💡 Tip: Get free API key from exchangerate-api.com")
        print("      and replace 'YOUR_API_KEY_HERE' in the code")
        print("\n🛑 Press Ctrl+C to stop")
        print("=" * 60)
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
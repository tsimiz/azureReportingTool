"""Web GUI for Azure Reporting Tool."""

import os
import sys
import json
import subprocess
import logging
import tempfile
import shutil
from typing import Optional, Dict, Any, List
from flask import Flask, render_template_string, request, jsonify, send_file

from azure_reporter.modules.azure_fetcher import AzureFetcher
from azure_reporter.modules.ai_analyzer import AIAnalyzer
from azure_reporter.modules.powerpoint_generator import PowerPointGenerator
from azure_reporter.modules.pdf_generator import PDFGenerator
from azure_reporter.modules.backlog_generator import BacklogGenerator
from azure_reporter.utils.config_loader import ConfigLoader
from azure_reporter.utils.logger import setup_logger

app = Flask(__name__)
logger = setup_logger('azure_reporter_web', logging.INFO)

# Store current configuration and state
current_state = {
    'subscription_id': None,
    'subscriptions': [],
    'config': None,
    'last_report': None
}


def get_azure_login_status() -> Dict[str, Any]:
    """Check if user is logged in to Azure CLI and get account info."""
    try:
        result = subprocess.run(
            ['az', 'account', 'show', '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            account_info = json.loads(result.stdout)
            return {
                'logged_in': True,
                'user': account_info.get('user', {}).get('name', 'Unknown'),
                'tenant': account_info.get('tenantId', 'Unknown'),
                'subscription_id': account_info.get('id', ''),
                'subscription_name': account_info.get('name', 'Unknown')
            }
    except subprocess.TimeoutExpired:
        logger.warning("Azure CLI command timed out")
    except FileNotFoundError:
        logger.warning("Azure CLI not found")
    except json.JSONDecodeError:
        logger.warning("Could not parse Azure CLI output")
    except Exception as e:
        logger.error(f"Error checking Azure login status: {e}")
    
    return {'logged_in': False}


def get_subscriptions() -> List[Dict[str, str]]:
    """Get list of available Azure subscriptions."""
    try:
        result = subprocess.run(
            ['az', 'account', 'list', '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            subscriptions = json.loads(result.stdout)
            return [
                {
                    'id': sub.get('id', ''),
                    'name': sub.get('name', 'Unknown'),
                    'is_default': sub.get('isDefault', False)
                }
                for sub in subscriptions
            ]
    except Exception as e:
        logger.error(f"Error getting subscriptions: {e}")
    
    return []


def set_subscription(subscription_id: str) -> bool:
    """Set the active Azure subscription."""
    try:
        result = subprocess.run(
            ['az', 'account', 'set', '--subscription', subscription_id],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error setting subscription: {e}")
        return False


# HTML template with Azure-inspired modern minimalistic design
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Azure Reporting Tool</title>
    <style>
        :root {
            --azure-blue: #0078d4;
            --azure-dark-blue: #004578;
            --azure-light-blue: #50b0f0;
            --azure-gray: #f3f2f1;
            --azure-dark-gray: #323130;
            --azure-border: #edebe9;
            --azure-success: #107c10;
            --azure-warning: #ffaa44;
            --azure-error: #d13438;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--azure-gray);
            color: var(--azure-dark-gray);
            line-height: 1.5;
        }
        
        .header {
            background: linear-gradient(135deg, var(--azure-blue) 0%, var(--azure-dark-blue) 100%);
            color: white;
            padding: 16px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 20px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .header-logo {
            width: 32px;
            height: 32px;
            background: white;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: var(--azure-blue);
            font-size: 16px;
        }
        
        .login-status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }
        
        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        
        .status-indicator.connected {
            background-color: var(--azure-success);
        }
        
        .status-indicator.disconnected {
            background-color: var(--azure-error);
        }
        
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 24px;
            overflow: hidden;
        }
        
        .card-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--azure-border);
            font-weight: 600;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .card-header-icon {
            width: 24px;
            height: 24px;
            background: var(--azure-blue);
            border-radius: 4px;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
        }
        
        .card-body {
            padding: 20px;
        }
        
        .form-group {
            margin-bottom: 16px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 6px;
            font-weight: 500;
            font-size: 14px;
        }
        
        .form-group select,
        .form-group input[type="text"],
        .form-group input[type="number"] {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--azure-border);
            border-radius: 4px;
            font-size: 14px;
            font-family: inherit;
            transition: border-color 0.2s;
        }
        
        .form-group select:focus,
        .form-group input:focus {
            outline: none;
            border-color: var(--azure-blue);
            box-shadow: 0 0 0 1px var(--azure-blue);
        }
        
        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .checkbox-group input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: var(--azure-blue);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--azure-dark-blue);
        }
        
        .btn-primary:disabled {
            background: #c8c6c4;
            cursor: not-allowed;
        }
        
        .btn-secondary {
            background: white;
            color: var(--azure-dark-gray);
            border: 1px solid var(--azure-border);
        }
        
        .btn-secondary:hover {
            background: var(--azure-gray);
        }
        
        .btn-success {
            background: var(--azure-success);
            color: white;
        }
        
        .btn-success:hover {
            background: #0e6b0e;
        }
        
        .actions {
            display: flex;
            gap: 12px;
            margin-top: 20px;
        }
        
        .alert {
            padding: 12px 16px;
            border-radius: 4px;
            margin-bottom: 16px;
            font-size: 14px;
        }
        
        .alert-info {
            background: #deecf9;
            color: var(--azure-dark-blue);
            border-left: 4px solid var(--azure-blue);
        }
        
        .alert-warning {
            background: #fff4ce;
            color: #835c00;
            border-left: 4px solid var(--azure-warning);
        }
        
        .alert-error {
            background: #fde7e9;
            color: #a80000;
            border-left: 4px solid var(--azure-error);
        }
        
        .alert-success {
            background: #dff6dd;
            color: #0e6b0e;
            border-left: 4px solid var(--azure-success);
        }
        
        .progress-container {
            margin-top: 16px;
            display: none;
        }
        
        .progress-bar {
            height: 4px;
            background: var(--azure-border);
            border-radius: 2px;
            overflow: hidden;
        }
        
        .progress-bar-fill {
            height: 100%;
            background: var(--azure-blue);
            width: 0%;
            transition: width 0.3s;
            animation: progress-animation 2s infinite;
        }
        
        @keyframes progress-animation {
            0% { width: 0%; }
            50% { width: 70%; }
            100% { width: 100%; }
        }
        
        .progress-text {
            font-size: 14px;
            margin-top: 8px;
            color: #605e5c;
        }
        
        .report-preview {
            background: var(--azure-gray);
            border: 1px solid var(--azure-border);
            border-radius: 4px;
            padding: 20px;
            max-height: 500px;
            overflow-y: auto;
        }
        
        .report-section {
            margin-bottom: 24px;
        }
        
        .report-section h3 {
            font-size: 16px;
            color: var(--azure-dark-blue);
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--azure-border);
        }
        
        .finding-item {
            background: white;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 8px;
            border-left: 4px solid var(--azure-blue);
        }
        
        .finding-item.critical {
            border-left-color: var(--azure-error);
        }
        
        .finding-item.high {
            border-left-color: var(--azure-warning);
        }
        
        .finding-item.medium {
            border-left-color: var(--azure-blue);
        }
        
        .finding-item.low {
            border-left-color: var(--azure-success);
        }
        
        .finding-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .finding-resource {
            font-weight: 600;
        }
        
        .finding-severity {
            font-size: 12px;
            padding: 2px 8px;
            border-radius: 12px;
            text-transform: uppercase;
        }
        
        .finding-severity.critical {
            background: var(--azure-error);
            color: white;
        }
        
        .finding-severity.high {
            background: var(--azure-warning);
            color: white;
        }
        
        .finding-severity.medium {
            background: var(--azure-blue);
            color: white;
        }
        
        .finding-severity.low {
            background: var(--azure-success);
            color: white;
        }
        
        .finding-description {
            font-size: 14px;
            color: #605e5c;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: white;
            border: 1px solid var(--azure-border);
            border-radius: 4px;
            padding: 16px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: 600;
            color: var(--azure-blue);
        }
        
        .stat-label {
            font-size: 12px;
            color: #605e5c;
            text-transform: uppercase;
        }
        
        .hidden {
            display: none !important;
        }
        
        .footer {
            text-align: center;
            padding: 24px;
            color: #605e5c;
            font-size: 12px;
        }
        
        .subscription-badge {
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 12px;
        }
        
        .loading {
            position: relative;
            pointer-events: none;
        }
        
        .loading::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.7);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 12px;
                text-align: center;
            }
            
            .form-row {
                grid-template-columns: 1fr;
            }
            
            .actions {
                flex-direction: column;
            }
            
            .btn {
                width: 100%;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <h1>
            <div class="header-logo">Az</div>
            Azure Reporting Tool
        </h1>
        <div class="login-status">
            <span class="status-indicator" id="statusIndicator"></span>
            <span id="loginStatusText">Checking...</span>
            <span class="subscription-badge" id="subscriptionBadge"></span>
        </div>
    </header>

    <main class="main-container">
        <!-- Login Status Alert -->
        <div id="loginAlert" class="alert alert-warning hidden">
            <strong>Not logged in to Azure.</strong> Please run <code>az login</code> in your terminal to authenticate.
        </div>

        <!-- Subscription Selection -->
        <div class="card" id="subscriptionCard">
            <div class="card-header">
                <div class="card-header-icon">☁</div>
                Subscription
            </div>
            <div class="card-body">
                <div class="form-group">
                    <label for="subscriptionSelect">Select Azure Subscription</label>
                    <select id="subscriptionSelect" onchange="changeSubscription()">
                        <option value="">Loading subscriptions...</option>
                    </select>
                </div>
            </div>
        </div>

        <!-- Settings -->
        <div class="card">
            <div class="card-header">
                <div class="card-header-icon">⚙</div>
                Settings
            </div>
            <div class="card-body">
                <div class="form-row">
                    <div class="form-group">
                        <label for="outputDir">Output Directory</label>
                        <input type="text" id="outputDir" value="./output">
                    </div>
                    <div class="form-group">
                        <label for="reportFilename">Report Filename</label>
                        <input type="text" id="reportFilename" value="azure_report">
                    </div>
                    <div class="form-group">
                        <label for="exportFormat">Export Format</label>
                        <select id="exportFormat">
                            <option value="pdf">PDF (Recommended)</option>
                            <option value="pptx">PowerPoint (PPTX)</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <div class="checkbox-group">
                            <input type="checkbox" id="enableAI" checked>
                            <label for="enableAI">Enable AI Analysis</label>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="aiModel">AI Model</label>
                        <select id="aiModel">
                            <option value="gpt-4">GPT-4</option>
                            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="aiTemperature">AI Temperature</label>
                        <input type="number" id="aiTemperature" value="0.3" min="0" max="1" step="0.1">
                    </div>
                </div>
                
                <h4 style="margin: 16px 0 12px; font-size: 14px;">Resources to Analyze</h4>
                <div class="form-row">
                    <div class="form-group">
                        <div class="checkbox-group">
                            <input type="checkbox" id="analyzeVMs" checked>
                            <label for="analyzeVMs">Virtual Machines</label>
                        </div>
                    </div>
                    <div class="form-group">
                        <div class="checkbox-group">
                            <input type="checkbox" id="analyzeStorage" checked>
                            <label for="analyzeStorage">Storage Accounts</label>
                        </div>
                    </div>
                    <div class="form-group">
                        <div class="checkbox-group">
                            <input type="checkbox" id="analyzeNSGs" checked>
                            <label for="analyzeNSGs">Network Security Groups</label>
                        </div>
                    </div>
                    <div class="form-group">
                        <div class="checkbox-group">
                            <input type="checkbox" id="analyzeVNets" checked>
                            <label for="analyzeVNets">Virtual Networks</label>
                        </div>
                    </div>
                    <div class="form-group">
                        <div class="checkbox-group">
                            <input type="checkbox" id="analyzeAll" checked>
                            <label for="analyzeAll">All Resources</label>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Run Analysis -->
        <div class="card">
            <div class="card-header">
                <div class="card-header-icon">▶</div>
                Run Analysis
            </div>
            <div class="card-body">
                <p style="margin-bottom: 16px; color: #605e5c;">
                    Click the button below to start analyzing your Azure environment against Microsoft's best practices.
                </p>
                
                <div class="actions">
                    <button class="btn btn-primary" id="runAnalysisBtn" onclick="runAnalysis()">
                        🔍 Run Analysis
                    </button>
                </div>
                
                <div class="progress-container" id="progressContainer">
                    <div class="progress-bar">
                        <div class="progress-bar-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-text" id="progressText">Initializing...</div>
                </div>
            </div>
        </div>

        <!-- Report Preview -->
        <div class="card hidden" id="reportCard">
            <div class="card-header">
                <div class="card-header-icon">📊</div>
                Report Preview
            </div>
            <div class="card-body">
                <div class="stats-grid" id="statsGrid">
                    <!-- Stats will be populated dynamically -->
                </div>
                
                <div class="report-preview" id="reportPreview">
                    <!-- Report content will be populated dynamically -->
                </div>
                
                <div class="actions" style="margin-top: 20px;">
                    <button class="btn btn-success" id="downloadPdfBtn" onclick="downloadReport('pdf')">
                        📄 Download PDF
                    </button>
                    <button class="btn btn-success" id="downloadPptxBtn" onclick="downloadReport('pptx')">
                        📊 Download PowerPoint
                    </button>
                    <button class="btn btn-secondary" onclick="downloadReport('backlog')">
                        📋 Download Backlog (CSV)
                    </button>
                </div>
            </div>
        </div>
    </main>

    <footer class="footer">
        Azure Reporting Tool | Analyze your Azure environment against best practices
    </footer>

    <script>
        let analysisResult = null;
        
        // Check login status on page load
        document.addEventListener('DOMContentLoaded', function() {
            checkLoginStatus();
            loadSubscriptions();
        });
        
        async function checkLoginStatus() {
            try {
                const response = await fetch('/api/login-status');
                const data = await response.json();
                
                const indicator = document.getElementById('statusIndicator');
                const statusText = document.getElementById('loginStatusText');
                const badge = document.getElementById('subscriptionBadge');
                const alert = document.getElementById('loginAlert');
                const runBtn = document.getElementById('runAnalysisBtn');
                
                if (data.logged_in) {
                    indicator.className = 'status-indicator connected';
                    statusText.textContent = data.user;
                    badge.textContent = data.subscription_name;
                    badge.style.display = 'inline';
                    alert.classList.add('hidden');
                    runBtn.disabled = false;
                } else {
                    indicator.className = 'status-indicator disconnected';
                    statusText.textContent = 'Not logged in';
                    badge.style.display = 'none';
                    alert.classList.remove('hidden');
                    runBtn.disabled = true;
                }
            } catch (error) {
                console.error('Error checking login status:', error);
            }
        }
        
        async function loadSubscriptions() {
            try {
                const response = await fetch('/api/subscriptions');
                const subscriptions = await response.json();
                
                const select = document.getElementById('subscriptionSelect');
                select.innerHTML = '';
                
                if (subscriptions.length === 0) {
                    select.innerHTML = '<option value="">No subscriptions available</option>';
                    return;
                }
                
                subscriptions.forEach(sub => {
                    const option = document.createElement('option');
                    option.value = sub.id;
                    option.textContent = sub.name;
                    if (sub.is_default) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading subscriptions:', error);
            }
        }
        
        async function changeSubscription() {
            const select = document.getElementById('subscriptionSelect');
            const subscriptionId = select.value;
            
            if (!subscriptionId) return;
            
            try {
                const response = await fetch('/api/set-subscription', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ subscription_id: subscriptionId })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    await checkLoginStatus();
                } else {
                    alert('Failed to change subscription: ' + result.error);
                }
            } catch (error) {
                console.error('Error changing subscription:', error);
                alert('Error changing subscription');
            }
        }
        
        function getSettings() {
            return {
                output_dir: document.getElementById('outputDir').value,
                report_filename: document.getElementById('reportFilename').value,
                export_format: document.getElementById('exportFormat').value,
                ai_enabled: document.getElementById('enableAI').checked,
                ai_model: document.getElementById('aiModel').value,
                ai_temperature: parseFloat(document.getElementById('aiTemperature').value),
                resources: {
                    virtual_machines: document.getElementById('analyzeVMs').checked,
                    storage_accounts: document.getElementById('analyzeStorage').checked,
                    network_security_groups: document.getElementById('analyzeNSGs').checked,
                    virtual_networks: document.getElementById('analyzeVNets').checked,
                    analyze_all_resources: document.getElementById('analyzeAll').checked
                }
            };
        }
        
        async function runAnalysis() {
            const runBtn = document.getElementById('runAnalysisBtn');
            const progressContainer = document.getElementById('progressContainer');
            const progressText = document.getElementById('progressText');
            const reportCard = document.getElementById('reportCard');
            
            runBtn.disabled = true;
            progressContainer.style.display = 'block';
            reportCard.classList.add('hidden');
            
            const settings = getSettings();
            
            try {
                progressText.textContent = 'Starting analysis...';
                
                const response = await fetch('/api/run-analysis', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(settings)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    analysisResult = result;
                    progressText.textContent = 'Analysis complete!';
                    displayReport(result);
                    reportCard.classList.remove('hidden');
                } else {
                    progressText.textContent = 'Analysis failed: ' + result.error;
                }
            } catch (error) {
                console.error('Error running analysis:', error);
                progressText.textContent = 'Error: ' + error.message;
            } finally {
                runBtn.disabled = false;
            }
        }
        
        function displayReport(result) {
            const statsGrid = document.getElementById('statsGrid');
            const reportPreview = document.getElementById('reportPreview');
            
            // Display stats
            const stats = result.stats || {};
            statsGrid.innerHTML = `
                <div class="stat-card">
                    <div class="stat-value">${stats.total_resources || 0}</div>
                    <div class="stat-label">Total Resources</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.total_findings || 0}</div>
                    <div class="stat-label">Findings</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.critical_findings || 0}</div>
                    <div class="stat-label">Critical</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${stats.high_findings || 0}</div>
                    <div class="stat-label">High</div>
                </div>
            `;
            
            // Display findings
            let findingsHtml = '';
            
            // Executive Summary
            if (result.executive_summary) {
                findingsHtml += `
                    <div class="report-section">
                        <h3>Executive Summary</h3>
                        <p style="white-space: pre-wrap;">${result.executive_summary}</p>
                    </div>
                `;
            }
            
            // Findings by category
            const analyses = result.analyses || {};
            for (const [category, analysis] of Object.entries(analyses)) {
                if (category === 'executive_summary') continue;
                
                const findings = analysis.findings || [];
                if (findings.length === 0) continue;
                
                findingsHtml += `
                    <div class="report-section">
                        <h3>${formatCategoryName(category)}</h3>
                `;
                
                for (const finding of findings) {
                    const severity = (finding.severity || 'medium').toLowerCase();
                    findingsHtml += `
                        <div class="finding-item ${severity}">
                            <div class="finding-header">
                                <span class="finding-resource">${finding.resource || 'Unknown'}</span>
                                <span class="finding-severity ${severity}">${severity}</span>
                            </div>
                            <div class="finding-description">
                                <strong>${finding.issue || ''}</strong>
                                ${finding.recommendation ? '<br><em>Recommendation: ' + finding.recommendation + '</em>' : ''}
                            </div>
                        </div>
                    `;
                }
                
                findingsHtml += '</div>';
            }
            
            if (!findingsHtml) {
                findingsHtml = '<p>No findings to display. Run the analysis to see results.</p>';
            }
            
            reportPreview.innerHTML = findingsHtml;
        }
        
        function formatCategoryName(name) {
            return name
                .replace(/_/g, ' ')
                .replace(/\\b\\w/g, c => c.toUpperCase());
        }
        
        async function downloadReport(format) {
            if (!analysisResult) {
                alert('Please run an analysis first.');
                return;
            }
            
            try {
                const response = await fetch(`/api/download/${format}`);
                
                if (!response.ok) {
                    const error = await response.json();
                    alert('Download failed: ' + error.error);
                    return;
                }
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = 'report';
                if (contentDisposition) {
                    const match = contentDisposition.match(/filename="?(.+?)"?$/);
                    if (match) filename = match[1];
                }
                
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } catch (error) {
                console.error('Error downloading report:', error);
                alert('Error downloading report');
            }
        }
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """Render the main GUI page."""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/login-status')
def api_login_status():
    """Get Azure CLI login status."""
    status = get_azure_login_status()
    if status['logged_in']:
        current_state['subscription_id'] = status['subscription_id']
    return jsonify(status)


@app.route('/api/subscriptions')
def api_subscriptions():
    """Get list of Azure subscriptions."""
    subscriptions = get_subscriptions()
    current_state['subscriptions'] = subscriptions
    return jsonify(subscriptions)


@app.route('/api/set-subscription', methods=['POST'])
def api_set_subscription():
    """Set the active Azure subscription."""
    data = request.get_json()
    subscription_id = data.get('subscription_id')
    
    if not subscription_id:
        return jsonify({'success': False, 'error': 'No subscription ID provided'})
    
    success = set_subscription(subscription_id)
    if success:
        current_state['subscription_id'] = subscription_id
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to set subscription'})


@app.route('/api/run-analysis', methods=['POST'])
def api_run_analysis():
    """Run the Azure analysis."""
    try:
        settings = request.get_json()
        logger.info(f"Running analysis with settings: {settings}")
        
        # Check login status first
        login_status = get_azure_login_status()
        if not login_status['logged_in']:
            return jsonify({
                'success': False,
                'error': 'Not logged in to Azure. Please run "az login" first.'
            })
        
        subscription_id = login_status['subscription_id']
        
        # Create config
        config = {
            'output': {
                'directory': settings.get('output_dir', './output'),
                'report_filename': settings.get('report_filename', 'azure_report'),
                'export_format': settings.get('export_format', 'pdf')
            },
            'resources': settings.get('resources', {
                'virtual_machines': True,
                'storage_accounts': True,
                'network_security_groups': True,
                'virtual_networks': True,
                'analyze_all_resources': True
            }),
            'ai_analysis': {
                'enabled': settings.get('ai_enabled', True),
                'model': settings.get('ai_model', 'gpt-4'),
                'temperature': settings.get('ai_temperature', 0.3)
            }
        }
        
        # Create output directory
        output_dir = config['output']['directory']
        os.makedirs(output_dir, exist_ok=True)
        
        # Fetch Azure resources using DefaultAzureCredential (which uses Azure CLI credentials)
        logger.info("Fetching Azure resources...")
        fetcher = AzureFetcher(subscription_id=subscription_id)
        resources = fetcher.fetch_all_resources()
        
        # Calculate statistics
        total_resources = sum(len(r) for r in resources.values())
        
        analyses = {}
        executive_summary = ""
        total_findings = 0
        critical_findings = 0
        high_findings = 0
        
        # Run AI analysis if enabled
        if config['ai_analysis']['enabled']:
            logger.info("Running AI analysis...")
            
            # Get OpenAI config from environment
            config_loader = ConfigLoader()
            openai_config = config_loader.get_openai_config()
            
            if openai_config.get('api_key'):
                try:
                    analyzer = AIAnalyzer(
                        api_key=openai_config['api_key'],
                        model=openai_config.get('model', settings.get('ai_model', 'gpt-4')),
                        temperature=settings.get('ai_temperature', 0.3),
                        azure_endpoint=openai_config.get('azure_endpoint'),
                        azure_deployment=openai_config.get('azure_deployment')
                    )
                    analyses = analyzer.analyze_all_resources(resources)
                    executive_summary = analyses.get('executive_summary', '')
                    
                    # Count findings
                    for category, analysis in analyses.items():
                        if category == 'executive_summary':
                            continue
                        findings = analysis.get('findings', [])
                        total_findings += len(findings)
                        for finding in findings:
                            severity = finding.get('severity', '').lower()
                            if severity == 'critical':
                                critical_findings += 1
                            elif severity == 'high':
                                high_findings += 1
                except Exception as e:
                    logger.error(f"AI analysis failed: {e}")
                    analyses = {'error': str(e)}
            else:
                logger.warning("No OpenAI API key configured")
        
        # Generate report files
        export_format = config['output']['export_format']
        report_filename = config['output']['report_filename']
        
        if export_format == 'pdf':
            if not report_filename.endswith('.pdf'):
                report_filename = report_filename.rsplit('.', 1)[0] + '.pdf' if '.' in report_filename else report_filename + '.pdf'
            output_path = os.path.join(output_dir, report_filename)
            generator = PDFGenerator()
            generator.generate_report(resources, analyses, output_path)
        else:
            if not report_filename.endswith('.pptx'):
                report_filename = report_filename.rsplit('.', 1)[0] + '.pptx' if '.' in report_filename else report_filename + '.pptx'
            output_path = os.path.join(output_dir, report_filename)
            generator = PowerPointGenerator()
            generator.generate_report(resources, analyses, output_path)
        
        # Generate backlog
        backlog_gen = BacklogGenerator()
        backlog_gen.extract_backlog_items(analyses)
        backlog_gen.generate_all_formats(output_dir)
        
        # Store result for download
        current_state['last_report'] = {
            'output_dir': output_dir,
            'report_filename': report_filename,
            'export_format': export_format,
            'resources': resources,
            'analyses': analyses
        }
        
        logger.info("Analysis complete")
        
        return jsonify({
            'success': True,
            'stats': {
                'total_resources': total_resources,
                'total_findings': total_findings,
                'critical_findings': critical_findings,
                'high_findings': high_findings
            },
            'executive_summary': executive_summary,
            'analyses': analyses,
            'output_path': output_path
        })
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/download/<format>')
def api_download(format):
    """Download the generated report."""
    if not current_state.get('last_report'):
        return jsonify({'error': 'No report available. Please run an analysis first.'}), 404
    
    report = current_state['last_report']
    output_dir = report['output_dir']
    
    try:
        if format == 'pdf':
            filename = report['report_filename']
            if not filename.endswith('.pdf'):
                filename = filename.rsplit('.', 1)[0] + '.pdf' if '.' in filename else filename + '.pdf'
            filepath = os.path.join(output_dir, filename)
            
            # Generate PDF if it doesn't exist
            if not os.path.exists(filepath):
                generator = PDFGenerator()
                generator.generate_report(report['resources'], report['analyses'], filepath)
            
            return send_file(
                filepath,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
            
        elif format == 'pptx':
            filename = report['report_filename']
            if not filename.endswith('.pptx'):
                filename = filename.rsplit('.', 1)[0] + '.pptx' if '.' in filename else filename + '.pptx'
            filepath = os.path.join(output_dir, filename)
            
            # Generate PPTX if it doesn't exist
            if not os.path.exists(filepath):
                generator = PowerPointGenerator()
                generator.generate_report(report['resources'], report['analyses'], filepath)
            
            return send_file(
                filepath,
                mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                as_attachment=True,
                download_name=filename
            )
            
        elif format == 'backlog':
            filepath = os.path.join(output_dir, 'improvement_backlog.csv')
            
            # Generate backlog if it doesn't exist
            if not os.path.exists(filepath):
                backlog_gen = BacklogGenerator()
                backlog_gen.extract_backlog_items(report['analyses'])
                backlog_gen.generate_all_formats(output_dir)
            
            return send_file(
                filepath,
                mimetype='text/csv',
                as_attachment=True,
                download_name='improvement_backlog.csv'
            )
        else:
            return jsonify({'error': f'Unknown format: {format}'}), 400
            
    except Exception as e:
        logger.error(f"Download failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def main():
    """Main entry point for the web GUI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Azure Reporting Tool - Web GUI'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to run the web server on (default: 5000)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host to bind the web server to (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("Azure Reporting Tool - Web GUI")
    print(f"{'='*60}")
    print(f"\nStarting web server at http://{args.host}:{args.port}")
    print("\nOpen this URL in your web browser to use the GUI.")
    print("Press Ctrl+C to stop the server.\n")
    
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()

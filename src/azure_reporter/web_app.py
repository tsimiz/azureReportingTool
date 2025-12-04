"""Web GUI for Azure Reporting Tool."""

import os
import sys
import json
import re
import subprocess
import logging
import tempfile
import shutil
import time
import select
from typing import Optional, Dict, Any, List
from flask import Flask, render_template_string, request, jsonify, send_file

from azure_reporter.modules.azure_fetcher import AzureFetcher
from azure_reporter.modules.ai_analyzer import AIAnalyzer
from azure_reporter.modules.tag_analyzer import TagAnalyzer
from azure_reporter.modules.cost_analyzer import CostAnalyzer
from azure_reporter.modules.powerpoint_generator import PowerPointGenerator
from azure_reporter.modules.pdf_generator import PDFGenerator
from azure_reporter.modules.backlog_generator import BacklogGenerator
from azure_reporter.utils.config_loader import ConfigLoader
from azure_reporter.utils.logger import setup_logger

app = Flask(__name__)
logger = setup_logger('azure_reporter_web', logging.INFO)

# Device code pattern for Azure login
DEVICE_CODE_PATTERN = re.compile(r'code\s+([A-Z0-9]{9})')

# Store current configuration and state
current_state = {
    'subscription_id': None,
    'subscriptions': [],
    'config': None,
    'last_report': None,
    'env_vars': {}  # Store environment variables set via GUI
}


def ensure_file_extension(filename: str, extension: str) -> str:
    """Ensure a filename has the specified extension.
    
    Args:
        filename: The filename to check/modify
        extension: The extension to ensure (e.g., '.pdf', '.pptx')
        
    Returns:
        The filename with the correct extension
    """
    if not extension.startswith('.'):
        extension = '.' + extension
    if not filename.endswith(extension):
        if '.' in filename:
            filename = filename.rsplit('.', 1)[0] + extension
        else:
            filename = filename + extension
    return filename


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
        .form-group input[type="password"],
        .form-group input[type="number"] {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--azure-border);
            border-radius: 4px;
            font-size: 14px;
            font-family: inherit;
            transition: border-color 0.2s;
            height: 42px;
            box-sizing: border-box;
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
        
        .config-section {
            background: var(--azure-gray);
            border: 1px solid var(--azure-border);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 20px;
        }
        
        .config-section-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--azure-border);
        }
        
        .config-section-header h4 {
            margin: 0;
            font-size: 15px;
            font-weight: 600;
            color: var(--azure-dark-blue);
        }
        
        .config-section-header .badge {
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 500;
        }
        
        .config-section-header .badge-openai {
            background: #10a37f;
            color: white;
        }
        
        .config-section-header .badge-azure {
            background: var(--azure-blue);
            color: white;
        }
        
        .config-section-header .badge-sp {
            background: #5c2d91;
            color: white;
        }
        
        .config-section-description {
            font-size: 13px;
            color: #605e5c;
            margin-bottom: 12px;
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
        
        /* Backlog table styles */
        .backlog-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        
        .backlog-table th,
        .backlog-table td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid var(--azure-border);
        }
        
        .backlog-table th {
            background: var(--azure-gray);
            font-weight: 600;
            color: var(--azure-dark-gray);
            position: sticky;
            top: 0;
        }
        
        .backlog-table tr:hover {
            background: #f9f9f9;
        }
        
        .backlog-table .severity-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .backlog-table .severity-badge.critical {
            background: var(--azure-error);
            color: white;
        }
        
        .backlog-table .severity-badge.high {
            background: var(--azure-warning);
            color: white;
        }
        
        .backlog-table .severity-badge.medium {
            background: var(--azure-blue);
            color: white;
        }
        
        .backlog-table .severity-badge.low {
            background: var(--azure-success);
            color: white;
        }
        
        .backlog-table .priority-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: var(--azure-blue);
            color: white;
            font-weight: 600;
            font-size: 12px;
        }
        
        .backlog-table-container {
            max-height: 500px;
            overflow-y: auto;
            border: 1px solid var(--azure-border);
            border-radius: 4px;
        }
        
        .backlog-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }
        
        .backlog-summary-item {
            background: var(--azure-gray);
            padding: 12px;
            border-radius: 4px;
            text-align: center;
        }
        
        .backlog-summary-item .count {
            font-size: 24px;
            font-weight: 600;
            color: var(--azure-blue);
        }
        
        .backlog-summary-item .label {
            font-size: 12px;
            color: #605e5c;
            text-transform: uppercase;
        }
        
        .backlog-filters {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .backlog-filters select {
            padding: 6px 10px;
            border: 1px solid var(--azure-border);
            border-radius: 4px;
            font-size: 14px;
        }
        
        /* Tag Compliance Styles */
        .tag-compliance-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 16px;
            margin: 16px 0;
        }
        
        .resource-group-card {
            border: 1px solid var(--azure-border);
            border-radius: 8px;
            padding: 16px;
            background: white;
        }
        
        .resource-group-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--azure-border);
        }
        
        .resource-group-name {
            font-weight: 600;
            font-size: 14px;
            color: var(--azure-dark-blue);
        }
        
        .compliance-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .compliance-badge.high {
            background: #d4edda;
            color: #155724;
        }
        
        .compliance-badge.medium {
            background: #fff3cd;
            color: #856404;
        }
        
        .compliance-badge.low {
            background: #f8d7da;
            color: #721c24;
        }
        
        .tag-status {
            font-size: 12px;
            margin: 8px 0;
        }
        
        .tag-status.missing {
            color: var(--azure-error);
        }
        
        .tag-status.present {
            color: var(--azure-success);
        }
        
        .resource-list {
            margin-top: 12px;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .resource-item {
            padding: 8px;
            margin: 4px 0;
            background: var(--azure-gray);
            border-radius: 4px;
            font-size: 12px;
        }
        
        .resource-item-name {
            font-weight: 500;
            color: var(--azure-dark-gray);
        }
        
        .resource-item-missing {
            color: var(--azure-error);
            font-size: 11px;
            margin-top: 4px;
        }
        
        /* Christmas Theme Toggle Button */
        .christmas-toggle {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 24px;
            padding: 4px 8px;
            margin-left: 12px;
            border-radius: 4px;
            transition: all 0.3s ease;
            opacity: 0.8;
        }
        
        .christmas-toggle:hover {
            opacity: 1;
            transform: scale(1.1);
        }
        
        .christmas-toggle.active {
            animation: tree-glow 1.5s ease-in-out infinite alternate;
        }
        
        @keyframes tree-glow {
            from { filter: drop-shadow(0 0 2px #ffd700); }
            to { filter: drop-shadow(0 0 8px #ffd700); }
        }
        
        /* Christmas Theme Styles */
        body.christmas-theme {
            --christmas-red: #c41e3a;
            --christmas-green: #165b33;
            --christmas-gold: #ffd700;
            --christmas-dark-green: #0d3820;
            --christmas-light-red: #ff6b6b;
            background-color: #f5f0e8;
        }
        
        body.christmas-theme::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(22, 91, 51, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 90% 80%, rgba(196, 30, 58, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 50% 50%, rgba(255, 215, 0, 0.02) 0%, transparent 70%);
            pointer-events: none;
            z-index: 0;
        }
        
        body.christmas-theme .main-container,
        body.christmas-theme .header,
        body.christmas-theme .footer {
            position: relative;
            z-index: 1;
        }
        
        body.christmas-theme .header {
            background: linear-gradient(135deg, var(--christmas-red) 0%, var(--christmas-dark-green) 100%);
            position: relative;
            overflow: visible;
        }
        
        /* Icicles on header */
        body.christmas-theme .header::after {
            content: '';
            position: absolute;
            bottom: -15px;
            left: 0;
            right: 0;
            height: 20px;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 20'%3E%3Cdefs%3E%3ClinearGradient id='iceGrad' x1='0%25' y1='0%25' x2='0%25' y2='100%25'%3E%3Cstop offset='0%25' style='stop-color:%23e8f4f8'/%3E%3Cstop offset='100%25' style='stop-color:%23b8d4e3'/%3E%3C/linearGradient%3E%3C/defs%3E%3Cpath d='M0,0 L5,0 L5,8 L2.5,15 L0,8 Z' fill='url(%23iceGrad)'/%3E%3Cpath d='M10,0 L18,0 L18,5 L14,12 L10,5 Z' fill='url(%23iceGrad)'/%3E%3Cpath d='M22,0 L26,0 L26,10 L24,18 L22,10 Z' fill='url(%23iceGrad)'/%3E%3Cpath d='M32,0 L38,0 L38,6 L35,11 L32,6 Z' fill='url(%23iceGrad)'/%3E%3Cpath d='M45,0 L50,0 L50,9 L47.5,16 L45,9 Z' fill='url(%23iceGrad)'/%3E%3Cpath d='M55,0 L60,0 L60,7 L57.5,13 L55,7 Z' fill='url(%23iceGrad)'/%3E%3Cpath d='M65,0 L72,0 L72,5 L68.5,10 L65,5 Z' fill='url(%23iceGrad)'/%3E%3Cpath d='M78,0 L82,0 L82,11 L80,19 L78,11 Z' fill='url(%23iceGrad)'/%3E%3Cpath d='M88,0 L94,0 L94,6 L91,12 L88,6 Z' fill='url(%23iceGrad)'/%3E%3C/svg%3E");
            background-repeat: repeat-x;
            background-size: 100px 20px;
            z-index: 10;
            pointer-events: none;
        }
        
        body.christmas-theme .card {
            border-top: 3px solid var(--christmas-green);
        }
        
        body.christmas-theme .card-header {
            background: linear-gradient(90deg, rgba(22, 91, 51, 0.05) 0%, rgba(196, 30, 58, 0.05) 100%);
        }
        
        body.christmas-theme .card-header-icon {
            background: var(--christmas-red);
        }
        
        body.christmas-theme .btn-primary {
            background: var(--christmas-red);
        }
        
        body.christmas-theme .btn-primary:hover {
            background: #a01830;
        }
        
        body.christmas-theme .btn-success {
            background: var(--christmas-green);
        }
        
        body.christmas-theme .btn-success:hover {
            background: var(--christmas-dark-green);
        }
        
        body.christmas-theme .stat-value {
            color: var(--christmas-red);
        }
        
        body.christmas-theme .alert-info {
            border-left-color: var(--christmas-green);
            background: rgba(22, 91, 51, 0.1);
        }
        
        body.christmas-theme .header-logo {
            color: var(--christmas-red);
        }
        
        body.christmas-theme .subscription-badge {
            background: rgba(255, 215, 0, 0.3);
        }
        
        /* Snowfall Animation */
        .snowfall-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
            overflow: hidden;
            display: none;
        }
        
        body.christmas-theme .snowfall-container {
            display: block;
        }
        
        .snowflake {
            position: absolute;
            top: -10px;
            color: white;
            font-size: 1em;
            text-shadow: 0 0 3px rgba(255, 255, 255, 0.8);
            animation: snowfall linear infinite;
            opacity: 0.8;
        }
        
        @keyframes snowfall {
            0% {
                transform: translateY(-10px) rotate(0deg);
            }
            100% {
                transform: translateY(100vh) rotate(360deg);
            }
        }
    </style>
</head>
<body>
    <!-- Snowfall container for Christmas theme -->
    <div class="snowfall-container" id="snowfallContainer"></div>
    
    <header class="header">
        <h1>
            <div class="header-logo">Az</div>
            Azure Reporting Tool
        </h1>
        <div class="login-status">
            <span class="status-indicator" id="statusIndicator"></span>
            <span id="loginStatusText">Checking...</span>
            <span class="subscription-badge" id="subscriptionBadge"></span>
            <button class="christmas-toggle" id="christmasToggle" onclick="toggleChristmasTheme()" title="Toggle Christmas Theme">🎄</button>
        </div>
    </header>

    <main class="main-container">
        <!-- Login Status Alert -->
        <div id="loginAlert" class="alert alert-warning hidden">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <strong>Not logged in to Azure.</strong> Click the button to login or run <code>az login</code> in your terminal.
                </div>
                <button class="btn btn-primary" onclick="azureLogin()" id="azureLoginBtn" style="margin: 0;">
                    🔐 Login to Azure
                </button>
            </div>
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
                <div style="margin-top: 12px;">
                    <button class="btn btn-secondary" onclick="refreshSubscriptions()" style="margin-right: 8px;">
                        🔄 Refresh Subscriptions
                    </button>
                    <button class="btn btn-primary" onclick="azureLogin()" id="azureLoginBtn2">
                        🔐 Login to Azure
                    </button>
                </div>
            </div>
        </div>

        <!-- Environment Variables -->
        <div class="card">
            <div class="card-header">
                <div class="card-header-icon">🔑</div>
                Configuration
            </div>
            <div class="card-body">
                <div class="alert alert-info" style="margin-bottom: 20px;">
                    Configure your API keys and credentials. These are stored in memory for the current session only.
                    Choose <strong>either</strong> OpenAI API <strong>or</strong> Azure AI Foundry for AI analysis.
                </div>
                
                <!-- Service Principal Section -->
                <div class="config-section">
                    <div class="config-section-header">
                        <h4>🔐 Azure Service Principal</h4>
                        <span class="badge badge-sp">Authentication</span>
                    </div>
                    <p class="config-section-description">
                        Optional: Configure Service Principal for programmatic Azure access. If not set, Azure CLI credentials will be used.
                    </p>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="azureTenantId">Tenant ID</label>
                            <input type="text" id="azureTenantId" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx">
                        </div>
                        <div class="form-group">
                            <label for="azureClientId">Client ID (App ID)</label>
                            <input type="text" id="azureClientId" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx">
                        </div>
                        <div class="form-group">
                            <label for="azureClientSecret">Client Secret</label>
                            <input type="password" id="azureClientSecret" placeholder="Your client secret">
                        </div>
                    </div>
                </div>
                
                <!-- OpenAI API Section -->
                <div class="config-section">
                    <div class="config-section-header">
                        <h4>🤖 OpenAI API</h4>
                        <span class="badge badge-openai">Option A</span>
                    </div>
                    <p class="config-section-description">
                        Use OpenAI's API directly. Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank">platform.openai.com</a>.
                    </p>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="openaiApiKey">API Key</label>
                            <input type="password" id="openaiApiKey" placeholder="sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx">
                        </div>
                        <div class="form-group">
                            <label for="openaiModel">Model</label>
                            <input type="text" id="openaiModel" value="gpt-4" placeholder="gpt-4 or gpt-3.5-turbo">
                        </div>
                    </div>
                </div>
                
                <!-- Azure AI Foundry Section -->
                <div class="config-section">
                    <div class="config-section-header">
                        <h4>☁️ Azure AI Foundry (Azure OpenAI)</h4>
                        <span class="badge badge-azure">Option B</span>
                    </div>
                    <p class="config-section-description">
                        Use Azure OpenAI Service. Configure your Azure OpenAI resource from the <a href="https://portal.azure.com" target="_blank">Azure Portal</a>.
                    </p>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="azureOpenaiEndpoint">Endpoint URL</label>
                            <input type="text" id="azureOpenaiEndpoint" placeholder="https://your-resource.openai.azure.com/">
                        </div>
                        <div class="form-group">
                            <label for="azureOpenaiKey">API Key</label>
                            <input type="password" id="azureOpenaiKey" placeholder="Your Azure OpenAI key">
                        </div>
                        <div class="form-group">
                            <label for="azureOpenaiDeployment">Deployment Name</label>
                            <input type="text" id="azureOpenaiDeployment" placeholder="gpt-4-deployment">
                        </div>
                    </div>
                </div>
                
                <div class="actions">
                    <button class="btn btn-primary" onclick="saveEnvVars()">
                        💾 Save Configuration
                    </button>
                    <button class="btn btn-secondary" onclick="loadEnvVars()">
                        🔄 Load Current Values
                    </button>
                </div>
                <div id="envVarsStatus" class="alert hidden" style="margin-top: 12px;"></div>
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
                
                <h4 style="margin: 16px 0 12px; font-size: 14px;">Tag Analysis</h4>
                <div class="alert alert-info" style="margin-bottom: 12px; padding: 10px;">
                    Tag analysis checks resource tags against required tags. This feature does not use AI.
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <div class="checkbox-group">
                            <input type="checkbox" id="enableTagAnalysis">
                            <label for="enableTagAnalysis">Enable Tag Analysis</label>
                        </div>
                    </div>
                    <div class="form-group" style="flex: 2;">
                        <label for="requiredTags">Required Tags (comma-separated)</label>
                        <input type="text" id="requiredTags" placeholder="Environment, Owner, CostCenter, Project">
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

        <!-- Tag Compliance Section -->
        <div class="card hidden" id="tagComplianceCard">
            <div class="card-header">
                <div class="card-header-icon">🏷️</div>
                Tag Compliance Details
            </div>
            <div class="card-body">
                <div class="tag-compliance-summary" id="tagComplianceSummary">
                    <!-- Tag compliance summary will be populated dynamically -->
                </div>
                
                <h4 style="margin: 16px 0 12px; font-size: 14px; font-weight: 600;">Resources Grouped by Resource Group</h4>
                <div class="tag-compliance-grid" id="tagComplianceGrid">
                    <!-- Resource group cards will be populated dynamically -->
                </div>
            </div>
        </div>

        <!-- Improvement Backlog -->
        <div class="card hidden" id="backlogCard">
            <div class="card-header">
                <div class="card-header-icon">📋</div>
                Improvement Backlog
            </div>
            <div class="card-body">
                <div class="backlog-summary" id="backlogSummary">
                    <!-- Backlog summary will be populated dynamically -->
                </div>
                
                <div class="backlog-filters" style="margin: 16px 0;">
                    <label style="margin-right: 8px;">Filter by severity:</label>
                    <select id="backlogSeverityFilter" onchange="filterBacklog()">
                        <option value="all">All</option>
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                    </select>
                    <label style="margin-left: 16px; margin-right: 8px;">Filter by category:</label>
                    <select id="backlogCategoryFilter" onchange="filterBacklog()">
                        <option value="all">All</option>
                    </select>
                </div>
                
                <div class="backlog-table-container" style="overflow-x: auto;">
                    <table class="backlog-table" id="backlogTable">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Priority</th>
                                <th>Severity</th>
                                <th>Resource</th>
                                <th>Category</th>
                                <th>Issue</th>
                                <th>Recommendation</th>
                                <th>Effort</th>
                            </tr>
                        </thead>
                        <tbody id="backlogTableBody">
                            <!-- Backlog items will be populated dynamically -->
                        </tbody>
                    </table>
                </div>
                
                <div class="actions" style="margin-top: 20px;">
                    <button class="btn btn-success" onclick="downloadReport('backlog')">
                        📋 Download Backlog (CSV)
                    </button>
                    <button class="btn btn-secondary" onclick="downloadReport('backlog-json')">
                        📄 Download Backlog (JSON)
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
        let backlogItems = [];
        
        // Christmas Theme Functions
        function toggleChristmasTheme() {
            const body = document.body;
            const toggle = document.getElementById('christmasToggle');
            const isEnabled = body.classList.toggle('christmas-theme');
            toggle.classList.toggle('active', isEnabled);
            
            // Save preference to localStorage
            localStorage.setItem('christmasTheme', isEnabled ? 'enabled' : 'disabled');
            
            // Create or remove snowflakes
            if (isEnabled) {
                createSnowflakes();
            } else {
                removeSnowflakes();
            }
        }
        
        function createSnowflakes() {
            const container = document.getElementById('snowfallContainer');
            if (!container) return;
            
            // Clear existing snowflakes
            container.innerHTML = '';
            
            // Create snowflakes (reduced count for better performance)
            const snowflakeChars = ['❄', '❅', '❆', '✻', '✼', '❉'];
            const numSnowflakes = 30;
            
            for (let i = 0; i < numSnowflakes; i++) {
                const snowflake = document.createElement('div');
                snowflake.className = 'snowflake';
                snowflake.innerHTML = snowflakeChars[Math.floor(Math.random() * snowflakeChars.length)];
                snowflake.style.left = Math.random() * 100 + '%';
                snowflake.style.fontSize = (Math.random() * 10 + 8) + 'px';
                snowflake.style.animationDuration = (Math.random() * 5 + 5) + 's';
                snowflake.style.animationDelay = (Math.random() * 10) + 's';
                snowflake.style.opacity = Math.random() * 0.6 + 0.4;
                container.appendChild(snowflake);
            }
        }
        
        function removeSnowflakes() {
            const container = document.getElementById('snowfallContainer');
            if (container) {
                container.innerHTML = '';
            }
        }
        
        function loadChristmasTheme() {
            const savedTheme = localStorage.getItem('christmasTheme');
            const toggleBtn = document.getElementById('christmasToggle');
            if (savedTheme === 'enabled') {
                document.body.classList.add('christmas-theme');
                if (toggleBtn) {
                    toggleBtn.classList.add('active');
                }
                createSnowflakes();
            }
        }
        
        // Check login status on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadChristmasTheme();
            checkLoginStatus();
            loadSubscriptions();
            loadEnvVars();
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
            const requiredTagsInput = document.getElementById('requiredTags').value;
            const requiredTags = requiredTagsInput 
                ? requiredTagsInput.split(',').map(tag => tag.trim()).filter(tag => tag)
                : [];
            
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
                },
                tag_analysis: {
                    enabled: document.getElementById('enableTagAnalysis').checked,
                    required_tags: requiredTags
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
            // Build stats HTML with tag compliance if available
            let statsHtml = `
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
            
            // Add tag compliance stat if available
            if (stats.tag_compliance_rate !== undefined) {
                const complianceColor = stats.tag_compliance_rate >= 90 ? 'var(--azure-success)' : 
                                       (stats.tag_compliance_rate >= 70 ? 'var(--azure-warning)' : 'var(--azure-error)');
                statsHtml += `
                    <div class="stat-card">
                        <div class="stat-value" style="color: ${complianceColor};">${stats.tag_compliance_rate}%</div>
                        <div class="stat-label">Tag Compliance</div>
                    </div>
                `;
            }
            
            statsGrid.innerHTML = statsHtml;
            
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
            
            // Display tag compliance if available
            if (analyses.tag_analysis) {
                displayTagCompliance(analyses.tag_analysis);
                document.getElementById('tagComplianceCard').classList.remove('hidden');
            }
            
            // Display backlog if available
            if (result.backlog && result.backlog.length > 0) {
                displayBacklog(result.backlog);
                document.getElementById('backlogCard').classList.remove('hidden');
            }
        }
        
        function displayTagCompliance(tagAnalysis) {
            const summary = tagAnalysis.summary || {};
            const resourceGroupsDetails = tagAnalysis.resource_groups_details || [];
            
            // Display summary
            const summaryDiv = document.getElementById('tagComplianceSummary');
            const complianceRate = summary.overall_compliance_rate || 0;
            const complianceClass = complianceRate >= 90 ? 'high' : (complianceRate >= 70 ? 'medium' : 'low');
            
            summaryDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
                    <div>
                        <div style="font-size: 32px; font-weight: 700; color: ${complianceRate >= 90 ? 'var(--azure-success)' : (complianceRate >= 70 ? 'var(--azure-warning)' : 'var(--azure-error)')};">
                            ${complianceRate}%
                        </div>
                        <div style="font-size: 14px; color: var(--azure-dark-gray);">Overall Compliance</div>
                    </div>
                    <div style="flex: 1; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px;">
                        <div>
                            <div style="font-size: 18px; font-weight: 600;">${summary.total_resources || 0}</div>
                            <div style="font-size: 12px; color: var(--azure-dark-gray);">Total Resources</div>
                        </div>
                        <div>
                            <div style="font-size: 18px; font-weight: 600;">${summary.total_resource_groups || 0}</div>
                            <div style="font-size: 12px; color: var(--azure-dark-gray);">Resource Groups</div>
                        </div>
                        <div>
                            <div style="font-size: 18px; font-weight: 600;">${summary.required_tags_count || 0}</div>
                            <div style="font-size: 12px; color: var(--azure-dark-gray);">Required Tags</div>
                        </div>
                        <div>
                            <div style="font-size: 18px; font-weight: 600; color: var(--azure-error);">${summary.resources_without_tags || 0}</div>
                            <div style="font-size: 12px; color: var(--azure-dark-gray);">Without Any Tags</div>
                        </div>
                    </div>
                </div>
            `;
            
            // Display resource groups
            const grid = document.getElementById('tagComplianceGrid');
            let gridHtml = '';
            
            for (const rg of resourceGroupsDetails) {
                const rgCompliance = rg.compliance_rate || 0;
                const rgComplianceClass = rgCompliance >= 90 ? 'high' : (rgCompliance >= 70 ? 'medium' : 'low');
                const missingTags = rg.missing_tags || [];
                const nonCompliantCount = rg.non_compliant_resources || 0;
                const totalResources = rg.total_resources || 0;
                const resources = rg.resources || [];
                const nonCompliantResources = resources.filter(r => r.missing_tags && r.missing_tags.length > 0);
                
                gridHtml += `
                    <div class="resource-group-card">
                        <div class="resource-group-header">
                            <div class="resource-group-name">${rg.name || 'Unknown'}</div>
                            <div class="compliance-badge ${rgComplianceClass}">${rgCompliance}%</div>
                        </div>
                        
                        ${missingTags.length > 0 ? 
                            `<div class="tag-status missing">⚠️ RG Missing: ${missingTags.join(', ')}</div>` :
                            `<div class="tag-status present">✓ RG has all required tags</div>`
                        }
                        
                        <div style="margin: 8px 0; font-size: 12px; color: var(--azure-dark-gray);">
                            ${nonCompliantCount} of ${totalResources} resources missing tags
                        </div>
                        
                        ${nonCompliantResources.length > 0 ? `
                            <div class="resource-list">
                                ${nonCompliantResources.slice(0, 5).map(resource => `
                                    <div class="resource-item">
                                        <div class="resource-item-name">${resource.resource_name || 'Unknown'}</div>
                                        <div class="resource-item-missing">Missing: ${(resource.missing_tags || []).join(', ')}</div>
                                    </div>
                                `).join('')}
                                ${nonCompliantResources.length > 5 ? 
                                    `<div style="text-align: center; font-size: 11px; color: var(--azure-dark-gray); margin-top: 8px;">
                                        ... and ${nonCompliantResources.length - 5} more resources
                                    </div>` : ''
                                }
                            </div>
                        ` : ''}
                    </div>
                `;
            }
            
            if (!gridHtml) {
                gridHtml = '<p style="color: var(--azure-dark-gray);">No resource groups found or tag analysis not enabled.</p>';
            }
            
            grid.innerHTML = gridHtml;
        }
        
        function displayBacklog(items) {
            backlogItems = items;
            
            // Update summary
            const summary = document.getElementById('backlogSummary');
            const criticalCount = items.filter(i => i.severity === 'CRITICAL').length;
            const highCount = items.filter(i => i.severity === 'HIGH').length;
            const mediumCount = items.filter(i => i.severity === 'MEDIUM').length;
            const lowCount = items.filter(i => i.severity === 'LOW').length;
            
            summary.innerHTML = `
                <div class="backlog-summary-item">
                    <div class="count">${items.length}</div>
                    <div class="label">Total Items</div>
                </div>
                <div class="backlog-summary-item">
                    <div class="count" style="color: var(--azure-error);">${criticalCount}</div>
                    <div class="label">Critical</div>
                </div>
                <div class="backlog-summary-item">
                    <div class="count" style="color: var(--azure-warning);">${highCount}</div>
                    <div class="label">High</div>
                </div>
                <div class="backlog-summary-item">
                    <div class="count" style="color: var(--azure-blue);">${mediumCount}</div>
                    <div class="label">Medium</div>
                </div>
                <div class="backlog-summary-item">
                    <div class="count" style="color: var(--azure-success);">${lowCount}</div>
                    <div class="label">Low</div>
                </div>
            `;
            
            // Populate category filter
            const categories = [...new Set(items.map(i => i.category))];
            const categoryFilter = document.getElementById('backlogCategoryFilter');
            categoryFilter.innerHTML = '<option value="all">All</option>';
            categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat;
                option.textContent = cat;
                categoryFilter.appendChild(option);
            });
            
            // Display table
            renderBacklogTable(items);
        }
        
        function renderBacklogTable(items) {
            const tbody = document.getElementById('backlogTableBody');
            tbody.innerHTML = '';
            
            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px;">No backlog items found.</td></tr>';
                return;
            }
            
            items.forEach(item => {
                const severityClass = item.severity.toLowerCase();
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.id}</td>
                    <td><span class="priority-badge">${item.priority}</span></td>
                    <td><span class="severity-badge ${severityClass}">${item.severity}</span></td>
                    <td>${item.resource_name}</td>
                    <td>${item.category}</td>
                    <td>${item.issue}</td>
                    <td>${item.recommendation}</td>
                    <td>${item.estimated_effort}</td>
                `;
                tbody.appendChild(row);
            });
        }
        
        function filterBacklog() {
            const severityFilter = document.getElementById('backlogSeverityFilter').value;
            const categoryFilter = document.getElementById('backlogCategoryFilter').value;
            
            let filtered = backlogItems;
            
            if (severityFilter !== 'all') {
                filtered = filtered.filter(item => item.severity.toLowerCase() === severityFilter);
            }
            
            if (categoryFilter !== 'all') {
                filtered = filtered.filter(item => item.category === categoryFilter);
            }
            
            renderBacklogTable(filtered);
        }
        
        // Environment Variables Functions
        async function saveEnvVars() {
            const envVars = {
                azure_tenant_id: document.getElementById('azureTenantId').value,
                azure_client_id: document.getElementById('azureClientId').value,
                azure_client_secret: document.getElementById('azureClientSecret').value,
                openai_api_key: document.getElementById('openaiApiKey').value,
                openai_model: document.getElementById('openaiModel').value,
                azure_openai_endpoint: document.getElementById('azureOpenaiEndpoint').value,
                azure_openai_key: document.getElementById('azureOpenaiKey').value,
                azure_openai_deployment: document.getElementById('azureOpenaiDeployment').value
            };
            
            try {
                const response = await fetch('/api/env-vars', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(envVars)
                });
                
                const result = await response.json();
                const statusDiv = document.getElementById('envVarsStatus');
                
                if (result.success) {
                    statusDiv.className = 'alert alert-success';
                    statusDiv.textContent = 'Configuration saved successfully!';
                } else {
                    statusDiv.className = 'alert alert-error';
                    statusDiv.textContent = 'Failed to save: ' + result.error;
                }
                statusDiv.classList.remove('hidden');
                
                setTimeout(() => {
                    statusDiv.classList.add('hidden');
                }, 3000);
            } catch (error) {
                console.error('Error saving configuration:', error);
                const statusDiv = document.getElementById('envVarsStatus');
                statusDiv.className = 'alert alert-error';
                statusDiv.textContent = 'Error saving configuration';
                statusDiv.classList.remove('hidden');
            }
        }
        
        async function loadEnvVars() {
            try {
                const response = await fetch('/api/env-vars');
                const data = await response.json();
                
                if (data.azure_tenant_id) {
                    document.getElementById('azureTenantId').value = data.azure_tenant_id;
                }
                if (data.azure_client_id) {
                    document.getElementById('azureClientId').value = data.azure_client_id;
                }
                if (data.azure_client_secret) {
                    document.getElementById('azureClientSecret').value = data.azure_client_secret;
                }
                if (data.openai_api_key) {
                    document.getElementById('openaiApiKey').value = data.openai_api_key;
                }
                if (data.openai_model) {
                    document.getElementById('openaiModel').value = data.openai_model;
                }
                if (data.azure_openai_endpoint) {
                    document.getElementById('azureOpenaiEndpoint').value = data.azure_openai_endpoint;
                }
                if (data.azure_openai_key) {
                    document.getElementById('azureOpenaiKey').value = data.azure_openai_key;
                }
                if (data.azure_openai_deployment) {
                    document.getElementById('azureOpenaiDeployment').value = data.azure_openai_deployment;
                }
            } catch (error) {
                console.error('Error loading configuration:', error);
            }
        }
        
        async function azureLogin() {
            try {
                const response = await fetch('/api/azure-login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('Azure login initiated. Please check your browser for the login prompt or follow the device code instructions shown.');
                    // Poll for login completion
                    setTimeout(async () => {
                        await checkLoginStatus();
                        await loadSubscriptions();
                    }, 5000);
                } else if (result.device_code) {
                    alert(`To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code: ${result.user_code}`);
                    // Poll for login completion
                    pollLoginStatus();
                } else {
                    alert('Login failed: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error during Azure login:', error);
                alert('Error initiating Azure login. Please try running "az login" in your terminal.');
            }
        }
        
        async function pollLoginStatus() {
            let attempts = 0;
            const maxAttempts = 60; // 5 minutes max
            
            const poll = async () => {
                attempts++;
                const status = await fetch('/api/login-status');
                const data = await status.json();
                
                if (data.logged_in) {
                    await checkLoginStatus();
                    await loadSubscriptions();
                    return;
                }
                
                if (attempts < maxAttempts) {
                    setTimeout(poll, 5000);
                }
            };
            
            setTimeout(poll, 5000);
        }
        
        async function refreshSubscriptions() {
            await loadSubscriptions();
            await checkLoginStatus();
        }
        
        function formatCategoryName(name) {
            return name
                .replace(/_/g, ' ')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
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


@app.route('/api/azure-login', methods=['POST'])
def api_azure_login():
    """Initiate Azure CLI login using device code flow."""
    try:
        # Use device code flow which works without browser interaction
        result = subprocess.run(
            ['az', 'login', '--use-device-code'],
            capture_output=True,
            text=True,
            timeout=10  # Short timeout to get the device code quickly
        )
        
        # Check if we got a device code in the output
        if 'devicelogin' in result.stderr.lower() or 'device' in result.stderr.lower():
            # Extract user code from the message
            code_match = DEVICE_CODE_PATTERN.search(result.stderr)
            if code_match:
                user_code = code_match.group(1)
                return jsonify({
                    'success': False,
                    'device_code': True,
                    'user_code': user_code,
                    'message': f'To sign in, use a web browser to open https://microsoft.com/devicelogin and enter the code {user_code}'
                })
        
        # If login succeeded immediately
        if result.returncode == 0:
            return jsonify({'success': True})
        
        return jsonify({
            'success': False,
            'error': result.stderr or 'Login failed'
        })
        
    except subprocess.TimeoutExpired:
        # Device code flow - command is waiting for user input
        # Try to get the device code by running in background
        try:
            # Start the login process in background
            process = subprocess.Popen(
                ['az', 'login', '--use-device-code'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Read stderr for the device code message
            output = ""
            start_time = time.time()
            while time.time() - start_time < 5:
                if process.stderr:
                    line = process.stderr.readline()
                    if line:
                        output += line
                        if 'devicelogin' in output.lower():
                            break
                time.sleep(0.1)
            
            # Extract user code from output
            code_match = DEVICE_CODE_PATTERN.search(output)
            if code_match:
                user_code = code_match.group(1)
                return jsonify({
                    'success': False,
                    'device_code': True,
                    'user_code': user_code,
                    'message': f'To sign in, use a web browser to open https://microsoft.com/devicelogin and enter the code {user_code}'
                })
                
            return jsonify({
                'success': False,
                'device_code': True,
                'message': 'Please check your terminal for the device code or run "az login" manually.'
            })
        except Exception as e:
            logger.error(f"Error in background login: {e}")
            return jsonify({
                'success': False,
                'error': 'Login process started. Please complete authentication in your browser or terminal.'
            })
            
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'Azure CLI is not installed. Please install Azure CLI first.'
        })
    except Exception as e:
        logger.error(f"Error during Azure login: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/env-vars', methods=['GET'])
def api_get_env_vars():
    """Get current environment variables (masked for security)."""
    # Load from environment and merge with GUI-set values
    env_config = {}
    
    # Service Principal credentials
    tenant_id = current_state['env_vars'].get('azure_tenant_id') or os.getenv('AZURE_TENANT_ID', '')
    client_id = current_state['env_vars'].get('azure_client_id') or os.getenv('AZURE_CLIENT_ID', '')
    client_secret = current_state['env_vars'].get('azure_client_secret') or os.getenv('AZURE_CLIENT_SECRET', '')
    
    env_config['azure_tenant_id'] = tenant_id  # Not masked as it's not as sensitive
    env_config['azure_client_id'] = client_id  # Not masked as it's not as sensitive
    env_config['azure_client_secret'] = _mask_secret(client_secret)
    
    # Check GUI-set values first, then fall back to environment
    openai_key = current_state['env_vars'].get('openai_api_key') or os.getenv('OPENAI_API_KEY', '')
    azure_key = current_state['env_vars'].get('azure_openai_key') or os.getenv('AZURE_OPENAI_KEY', '')
    
    env_config['openai_api_key'] = _mask_secret(openai_key)
    env_config['openai_model'] = current_state['env_vars'].get('openai_model') or os.getenv('OPENAI_MODEL', 'gpt-4')
    env_config['azure_openai_endpoint'] = current_state['env_vars'].get('azure_openai_endpoint') or os.getenv('AZURE_OPENAI_ENDPOINT', '')
    env_config['azure_openai_key'] = _mask_secret(azure_key)
    env_config['azure_openai_deployment'] = current_state['env_vars'].get('azure_openai_deployment') or os.getenv('AZURE_OPENAI_DEPLOYMENT', '')
    
    return jsonify(env_config)


@app.route('/api/env-vars', methods=['POST'])
def api_set_env_vars():
    """Set environment variables for the current session."""
    try:
        data = request.get_json()
        
        # Store in current state (session-only, not persisted to disk for security)
        # Only update if value is provided and not a masked value
        
        # Service Principal credentials
        if data.get('azure_tenant_id'):
            current_state['env_vars']['azure_tenant_id'] = data['azure_tenant_id']
        
        if data.get('azure_client_id'):
            current_state['env_vars']['azure_client_id'] = data['azure_client_id']
        
        if data.get('azure_client_secret') and not _is_masked_value(data['azure_client_secret']):
            current_state['env_vars']['azure_client_secret'] = data['azure_client_secret']
        
        # OpenAI credentials
        if data.get('openai_api_key') and not _is_masked_value(data['openai_api_key']):
            current_state['env_vars']['openai_api_key'] = data['openai_api_key']
        
        if data.get('openai_model'):
            current_state['env_vars']['openai_model'] = data['openai_model']
        
        # Azure OpenAI credentials
        if data.get('azure_openai_endpoint'):
            current_state['env_vars']['azure_openai_endpoint'] = data['azure_openai_endpoint']
        
        if data.get('azure_openai_key') and not _is_masked_value(data['azure_openai_key']):
            current_state['env_vars']['azure_openai_key'] = data['azure_openai_key']
        
        if data.get('azure_openai_deployment'):
            current_state['env_vars']['azure_openai_deployment'] = data['azure_openai_deployment']
        
        logger.info("Environment variables updated via GUI")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error setting environment variables: {e}")
        return jsonify({'success': False, 'error': str(e)})


def _mask_secret(secret: str) -> str:
    """Mask a secret value for display, showing only first and last 4 characters."""
    if not secret:
        return ''
    if len(secret) <= 8:
        return '***'
    return secret[:4] + '***' + secret[-4:]


def _is_masked_value(value: str) -> bool:
    """Check if a value appears to be a masked secret.
    
    Returns True if the value contains '***' which indicates it's a masked value
    that should not be used to overwrite the actual secret.
    """
    return bool(value and '***' in value)


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
            },
            'tag_analysis': settings.get('tag_analysis', {
                'enabled': False,
                'required_tags': []
            })
        }
        
        # Create output directory
        output_dir = config['output']['directory']
        os.makedirs(output_dir, exist_ok=True)
        
        # Fetch Azure resources using DefaultAzureCredential (which uses Azure CLI credentials)
        logger.info("Fetching Azure resources...")
        fetcher = AzureFetcher(subscription_id=subscription_id)
        resources = fetcher.fetch_all_resources()
        
        # Calculate statistics (with type checking)
        total_resources = sum(
            len(r) for r in resources.values() 
            if isinstance(r, (list, dict, set, tuple))
        )
        
        analyses = {}
        executive_summary = ""
        total_findings = 0
        critical_findings = 0
        high_findings = 0
        
        # Run AI analysis if enabled
        if config['ai_analysis']['enabled']:
            logger.info("Running AI analysis...")
            
            # Get OpenAI config - prefer GUI-set values over environment
            gui_env = current_state.get('env_vars', {})
            
            # Determine API configuration
            openai_api_key = gui_env.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
            openai_model = gui_env.get('openai_model') or os.getenv('OPENAI_MODEL', 'gpt-4')
            azure_endpoint = gui_env.get('azure_openai_endpoint') or os.getenv('AZURE_OPENAI_ENDPOINT')
            azure_key = gui_env.get('azure_openai_key') or os.getenv('AZURE_OPENAI_KEY')
            azure_deployment = gui_env.get('azure_openai_deployment') or os.getenv('AZURE_OPENAI_DEPLOYMENT')
            
            # Check if Azure OpenAI is fully configured
            use_azure_openai = bool(azure_endpoint and azure_key and azure_deployment)
            
            # Prefer Azure OpenAI if fully configured
            if use_azure_openai:
                api_key = azure_key
                model = azure_deployment
            else:
                api_key = openai_api_key
                model = settings.get('ai_model', openai_model)
            
            if api_key:
                try:
                    analyzer = AIAnalyzer(
                        api_key=api_key,
                        model=model,
                        temperature=settings.get('ai_temperature', 0.3),
                        azure_endpoint=azure_endpoint if use_azure_openai else None,
                        azure_deployment=azure_deployment if use_azure_openai else None
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
        
        # Run tag analysis if enabled
        tag_config = config.get('tag_analysis', {})
        if tag_config.get('enabled', False):
            logger.info("Running tag analysis...")
            required_tags = tag_config.get('required_tags', [])
            
            tag_analyzer = TagAnalyzer(required_tags=required_tags)
            tag_analysis = tag_analyzer.analyze_resource_tags(resources)
            analyses['tag_analysis'] = tag_analysis
            
            # Count tag findings
            tag_findings = tag_analysis.get('findings', [])
            total_findings += len(tag_findings)
            for finding in tag_findings:
                severity = finding.get('severity', '').lower()
                if severity == 'critical':
                    critical_findings += 1
                elif severity == 'high':
                    high_findings += 1
            
            logger.info(f"Tag analysis complete. Compliance rate: {tag_analysis.get('summary', {}).get('overall_compliance_rate', 0)}%")
        
        # Run cost analysis (enabled by default)
        cost_config = config.get('cost_analysis', {'enabled': True})
        if cost_config.get('enabled', True):
            logger.info("Running cost analysis...")
            
            cost_analyzer = CostAnalyzer()
            cost_analysis = cost_analyzer.analyze_costs(resources)
            analyses['cost_analysis'] = cost_analysis
            
            # Count cost findings
            cost_findings = cost_analysis.get('findings', [])
            total_findings += len(cost_findings)
            for finding in cost_findings:
                severity = finding.get('severity', '').lower()
                if severity == 'critical':
                    critical_findings += 1
                elif severity == 'high':
                    high_findings += 1
            
            logger.info(f"Cost analysis complete. Found {len(cost_findings)} optimization opportunities.")
        
        # Generate report files
        export_format = config['output']['export_format']
        report_filename = config['output']['report_filename']
        
        if export_format == 'pdf':
            report_filename = ensure_file_extension(report_filename, '.pdf')
            output_path = os.path.join(output_dir, report_filename)
            generator = PDFGenerator()
            generator.generate_report(resources, analyses, output_path)
        else:
            report_filename = ensure_file_extension(report_filename, '.pptx')
            output_path = os.path.join(output_dir, report_filename)
            generator = PowerPointGenerator()
            generator.generate_report(resources, analyses, output_path)
        
        # Generate backlog
        backlog_gen = BacklogGenerator()
        backlog_gen.extract_backlog_items(analyses)
        backlog_gen.generate_all_formats(output_dir)
        
        # Get backlog items for the response
        backlog_items = backlog_gen.backlog_items
        
        # Store result for download
        current_state['last_report'] = {
            'output_dir': output_dir,
            'report_filename': report_filename,
            'export_format': export_format,
            'resources': resources,
            'analyses': analyses,
            'backlog': backlog_items
        }
        
        logger.info("Analysis complete")
        # Build stats including tag compliance if available
        stats = {
            'total_resources': total_resources,
            'total_findings': total_findings,
            'critical_findings': critical_findings,
            'high_findings': high_findings
        }
        
        # Add tag compliance stats if tag analysis was run
        if 'tag_analysis' in analyses:
            tag_summary = analyses['tag_analysis'].get('summary', {})
            stats['tag_compliance_rate'] = tag_summary.get('overall_compliance_rate', 0)
            stats['resources_with_tags'] = tag_summary.get('resources_with_tags', 0)
            stats['resources_without_tags'] = tag_summary.get('resources_without_tags', 0)
        
        # Add cost analysis stats if cost analysis was run
        if 'cost_analysis' in analyses:
            cost_summary = analyses['cost_analysis'].get('summary', {})
            opportunities = analyses['cost_analysis'].get('optimization_opportunities', {})
            stats['cost_optimization_opportunities'] = cost_summary.get('total_findings', 0)
            stats['immediate_actions_needed'] = opportunities.get('immediate_actions', 0)
        
        return jsonify({
            'success': True,
            'stats': stats,
            'executive_summary': executive_summary,
            'analyses': analyses,
            'backlog': backlog_items,
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
            filename = ensure_file_extension(report['report_filename'], '.pdf')
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
            filename = ensure_file_extension(report['report_filename'], '.pptx')
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
        elif format == 'backlog-json':
            filepath = os.path.join(output_dir, 'improvement_backlog.json')
            
            # Generate backlog if it doesn't exist
            if not os.path.exists(filepath):
                backlog_gen = BacklogGenerator()
                backlog_gen.extract_backlog_items(report['analyses'])
                backlog_gen.generate_all_formats(output_dir)
            
            return send_file(
                filepath,
                mimetype='application/json',
                as_attachment=True,
                download_name='improvement_backlog.json'
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

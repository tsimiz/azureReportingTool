# Azure Reporting Tool

A comprehensive tool to automatically generate reports and analysis of Azure environments against Microsoft's best practices. The tool fetches data from your Azure subscription, uses AI to analyze it against best practices, generates a PowerPoint presentation, and creates an improvement backlog.

## Features

- **Automated Azure Data Fetching**: Retrieves information about **ALL resources** in your Azure subscription, including:
  - Virtual Machines (with detailed analysis)
  - Storage Accounts (with detailed analysis)
  - Network Security Groups (with detailed analysis)
  - Virtual Networks (with detailed analysis)
  - Resource Groups
  - **All other Azure resource types in your subscription**

- **AI-Powered Analysis**: Uses OpenAI GPT-4 to analyze your Azure environment against Microsoft's best practices across:
  - Security
  - Performance
  - Cost Optimization
  - Operational Excellence
  - Reliability

- **Cost Analysis & Optimization Recommendations**: Analyzes resources for cost optimization opportunities (no AI required):
  - Identifies stopped VMs still incurring compute charges
  - Detects deallocated VMs with ongoing storage costs
  - Reviews GPU and memory-optimized VM usage
  - Analyzes premium and geo-redundant storage configurations
  - Identifies potentially orphaned resources (unattached disks, unused public IPs)
  - Recommends Reserved Instances for running VMs
  - Flags resources missing cost allocation tags
  - Detects consolidation opportunities for similar resources
  - Generates prioritized cost optimization recommendations
  - Enabled by default

- **Tag Compliance Analysis**: Analyze resource tags against required tags (no AI required):
  - Define required tags that should be present on all resources
  - **Validate tag values and flag invalid/placeholder values** (e.g., "none", "na", "tbd")
  - Get compliance percentage for each required tag
  - Identify which resources are missing required tags or have invalid values
  - Generate findings for tag compliance issues
  - Can be enabled independently of AI analysis

- **PowerPoint Report Generation**: Creates a professional PowerPoint presentation with:
  - Executive Summary
  - Resource Overview
  - Cost Analysis & Optimization Recommendations
  - Tag Compliance Analysis (when enabled)
  - Detailed Findings by Resource Type
  - Recommendations for Improvement
  - Best Practices Already Met

- **Improvement Backlog**: Generates prioritized backlog in multiple formats:
  - CSV for spreadsheet applications
  - JSON for programmatic access
  - Markdown for documentation

## Prerequisites

- Python 3.8 or higher
- Azure subscription with appropriate permissions
- **AI Service** (choose one):
  - OpenAI API key, OR
  - Azure AI Foundry (Azure OpenAI Service) endpoint and key
- Azure Service Principal credentials (recommended) or Azure CLI authentication

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/tsimiz/azureReportingTool.git
cd azureReportingTool
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install -e .
```

## Configuration

### 1. Set up Azure credentials

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

The tool supports **two authentication methods** for Azure:

#### Authentication Method 1: Azure CLI Login (Recommended for Development)

The simplest way to get started is to use Azure CLI authentication:

1. **Install Azure CLI** if not already installed ([installation guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))

2. **Login to Azure**:
   ```bash
   az login
   ```

3. **Get your Subscription ID**:
   ```bash
   az account show --query id -o tsv
   ```

4. **Configure `.env` with minimal settings**:
   ```env
   # Required: Your Azure subscription ID
   AZURE_SUBSCRIPTION_ID=your-subscription-id
   
   # AI Service (choose one)
   OPENAI_API_KEY=your-openai-api-key
   OPENAI_MODEL=gpt-4
   ```

That's it! The tool will automatically use your Azure CLI credentials.

#### Authentication Method 2: Service Principal (Recommended for Production)

For production environments or automated scenarios, use a Service Principal:

1. **Create a Service Principal**:
   ```bash
   az ad sp create-for-rbac --name "AzureReportingTool" --role Reader --scopes /subscriptions/YOUR_SUBSCRIPTION_ID
   ```

2. The command will output:
   - `appId` → Use as `AZURE_CLIENT_ID`
   - `password` → Use as `AZURE_CLIENT_SECRET`
   - `tenant` → Use as `AZURE_TENANT_ID`

3. **Configure `.env` with Service Principal credentials**:

   **Using OpenAI API:**
   ```env
   # Azure credentials
   AZURE_SUBSCRIPTION_ID=your-subscription-id
   AZURE_TENANT_ID=your-tenant-id
   AZURE_CLIENT_ID=your-client-id
   AZURE_CLIENT_SECRET=your-client-secret
   
   # OpenAI API key
   OPENAI_API_KEY=your-openai-api-key
   OPENAI_MODEL=gpt-4
   ```

   **Using Azure AI Foundry (Azure OpenAI Service):**
   ```env
   # Azure credentials
   AZURE_SUBSCRIPTION_ID=your-subscription-id
   AZURE_TENANT_ID=your-tenant-id
   AZURE_CLIENT_ID=your-client-id
   AZURE_CLIENT_SECRET=your-client-secret
   
   # Azure AI Foundry / Azure OpenAI Service
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_KEY=your-azure-openai-key
   AZURE_OPENAI_DEPLOYMENT=your-deployment-name
   ```

#### How to get Azure AI Foundry (Azure OpenAI) credentials:

If you prefer to use Azure AI Foundry instead of OpenAI API:

1. **Create an Azure OpenAI resource**:
   - Go to the [Azure Portal](https://portal.azure.com)
   - Navigate to "Create a resource" → Search for "Azure OpenAI"
   - Click "Create" and fill in the required information:
     - Subscription: Select your Azure subscription
     - Resource group: Select or create a resource group
     - Region: Choose a region that supports Azure OpenAI
     - Name: Choose a unique name for your resource
     - Pricing tier: Select appropriate tier
   - Click "Review + create" and then "Create"

2. **Deploy a model**:
   - Once the resource is created, go to the resource
   - Navigate to "Model deployments" or use Azure AI Foundry portal
   - Click "Create new deployment"
   - Select a model (e.g., gpt-4, gpt-35-turbo)
   - Give your deployment a name (you'll use this as `AZURE_OPENAI_DEPLOYMENT`)
   - Click "Create"

3. **Get your credentials**:
   - In your Azure OpenAI resource, go to "Keys and Endpoint"
   - Copy the following:
     - **Endpoint**: Use as `AZURE_OPENAI_ENDPOINT` (e.g., `https://your-resource-name.openai.azure.com/`)
     - **Key 1 or Key 2**: Use as `AZURE_OPENAI_KEY`
   - Note your deployment name from step 2 for `AZURE_OPENAI_DEPLOYMENT`

4. **Update your `.env` file**:
   ```env
   # Use Azure AI Foundry instead of OpenAI API
   # (Comment out or remove OPENAI_API_KEY when using Azure AI Foundry)
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_KEY=your-azure-openai-key-from-portal
   AZURE_OPENAI_DEPLOYMENT=your-deployment-name
   ```

**Note**: The tool will automatically use Azure AI Foundry if `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_KEY` are set, otherwise it will fall back to OpenAI API if `OPENAI_API_KEY` is provided.

### 2. Configure report settings (optional)

Copy and customize the configuration file:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` to customize:
- Output directory and filenames
- Resources to analyze
- AI analysis settings (can be disabled)
- Tag analysis settings (can be enabled independently of AI)
- Cost analysis settings
- Report content preferences

### Cost Analysis Configuration

Cost analysis identifies cost optimization opportunities in your Azure environment. This feature does not require AI and is **enabled by default**. It can be configured in your `config.yaml`:

```yaml
# Cost analysis settings
cost_analysis:
  enabled: true
```

When enabled, the cost analysis will:
- Identify stopped VMs still incurring compute charges
- Detect deallocated VMs with ongoing storage costs
- Review GPU and memory-optimized VM usage for right-sizing opportunities
- Analyze premium and geo-redundant storage configurations
- Identify potentially orphaned resources (unattached disks, unused public IPs)
- Recommend Azure Reserved Instances for running VMs
- Flag resources missing cost allocation tags
- Detect consolidation opportunities for similar resources
- Generate prioritized cost optimization recommendations
- Add cost optimization items to the improvement backlog

**Note:** You can disable cost analysis (`cost_analysis.enabled: false`) if you prefer to focus only on other analysis types.

### Tag Analysis Configuration

Tag analysis allows you to check if your Azure resources have required tags and validates tag values for compliance. This feature does not require AI and can be enabled independently. Add the following to your `config.yaml`:

```yaml
# Tag analysis settings
tag_analysis:
  enabled: true
  required_tags:
    - Environment
    - Owner
    - CostCenter
    - Project
  # Optional: List of tag values that should be flagged as invalid/non-compliant
  # Resources with these values will be marked as non-compliant even if the tag exists
  invalid_tag_values:
    - none
    - na
    - n/a
    - ""      # empty string
    - tbd
    - todo
    - unknown
```

When enabled, the tag analysis will:
- Report which resources are missing required tags
- **Validate tag values and flag invalid/placeholder values** (e.g., "none", "na", "tbd")
- Calculate compliance percentage for each required tag
- Generate findings for resources with missing tags or invalid tag values
- Add tag compliance items to the improvement backlog

**Note:** You can disable AI analysis (`ai_analysis.enabled: false`) and still use tag analysis, or use both together.

## Usage

### Command Line Interface

#### Basic Usage

```bash
python -m azure_reporter.main
```

Or if installed as a package:

```bash
azure-reporter
```

#### With Custom Configuration

```bash
python -m azure_reporter.main --config /path/to/config.yaml
```

#### With Verbose Logging

```bash
python -m azure_reporter.main --verbose
```

### Web GUI

The tool also provides a modern web-based graphical user interface (GUI) with Azure-inspired design that can be run locally in your web browser.

#### Prerequisites for Web GUI

1. **Azure CLI**: Make sure you have Azure CLI installed and are logged in:
   ```bash
   az login
   ```

2. **Environment Configuration**: Configure your `.env` file with OpenAI/Azure OpenAI credentials for AI analysis (optional but recommended).

#### Starting the Web GUI

```bash
python -m azure_reporter.web_app
```

Or if installed as a package:

```bash
azure-reporter-gui
```

#### Web GUI Options

```bash
# Run on a specific port
python -m azure_reporter.web_app --port 8080

# Run on a specific host (e.g., to allow external access)
python -m azure_reporter.web_app --host 0.0.0.0

# Enable debug mode
python -m azure_reporter.web_app --debug
```

#### Using the Web GUI

1. **Open your browser**: Navigate to `http://127.0.0.1:5000` (or the port you specified)

2. **Check login status**: The header shows your Azure login status. If you see "Not logged in", run `az login` in your terminal.

3. **Select subscription**: Use the dropdown to select which Azure subscription to analyze.

4. **Configure settings**:
   - **Output Directory**: Where to save generated reports
   - **Report Filename**: Name for the generated report
   - **Export Format**: Choose between PDF (recommended) or PowerPoint
   - **AI Analysis**: Enable/disable AI-powered analysis
   - **AI Model**: Select GPT-4 or GPT-3.5 Turbo
   - **Resources**: Select which resource types to analyze

5. **Run Analysis**: Click the "Run Analysis" button to start the analysis. Progress will be shown.

6. **View Results**: After analysis completes:
   - View summary statistics (total resources, findings by severity)
   - Browse findings organized by category
   - See the executive summary

7. **Download Reports**: Use the download buttons to save:
   - PDF report
   - PowerPoint presentation
   - Improvement backlog (CSV)

#### Web GUI Features

- **Modern Azure-inspired design**: Clean, minimalistic interface with Azure color scheme
- **Real-time login status**: Shows whether you're logged in and to which subscription
- **Easy subscription switching**: Change subscriptions with a dropdown
- **Configurable settings**: Adjust all settings through the GUI
- **Live progress updates**: See analysis progress in real-time
- **Interactive report preview**: Browse findings before downloading
- **Multiple export formats**: Download reports in PDF, PPTX, or CSV format

## Output

The tool generates the following files in the `output/` directory (or as configured):

1. **azure_report.pptx** - PowerPoint presentation with complete analysis
2. **improvement_backlog.csv** - Prioritized backlog in CSV format
3. **improvement_backlog.json** - Backlog with metadata in JSON format
4. **improvement_backlog.md** - Human-readable backlog in Markdown

## Project Structure

```
azureReportingTool/
├── src/
│   └── azure_reporter/
│       ├── __init__.py
│       ├── main.py                    # Main CLI orchestration script
│       ├── web_app.py                 # Web GUI application
│       ├── modules/
│       │   ├── __init__.py
│       │   ├── azure_fetcher.py       # Azure data fetching
│       │   ├── ai_analyzer.py         # AI-powered analysis
│       │   ├── powerpoint_generator.py # PPT generation
│       │   ├── pdf_generator.py       # PDF generation
│       │   └── backlog_generator.py   # Backlog creation
│       └── utils/
│           ├── __init__.py
│           ├── config_loader.py       # Configuration management
│           └── logger.py              # Logging utilities
├── tests/                             # Test files
├── output/                            # Generated reports (git-ignored)
├── requirements.txt                   # Python dependencies
├── setup.py                          # Package installation config
├── .env.example                      # Environment variables template
├── config.example.yaml               # Configuration template
├── .gitignore                        # Git ignore rules
└── README.md                         # This file
```

## Azure Permissions

The Service Principal needs at least the following permissions:

- **Reader** role on the subscription (for reading resource information)
- **Security Reader** role (optional, for security center data)

To assign roles:

```bash
# Reader role
az role assignment create --assignee YOUR_CLIENT_ID \
  --role Reader \
  --scope /subscriptions/YOUR_SUBSCRIPTION_ID

# Security Reader role (optional)
az role assignment create --assignee YOUR_CLIENT_ID \
  --role "Security Reader" \
  --scope /subscriptions/YOUR_SUBSCRIPTION_ID
```

## Troubleshooting

### Authentication Errors

If you encounter authentication errors:
- Verify your `.env` file has correct credentials
- Ensure the Service Principal has appropriate permissions
- Try authenticating with Azure CLI: `az login`

### Missing Resources

If some resources aren't appearing:
- Check that the Service Principal has Reader access to the resource groups
- Verify the resources exist in the specified subscription

### AI Analysis Errors

If AI analysis fails:

**For OpenAI API users:**
- Verify your OpenAI API key is valid
- Check you have sufficient OpenAI API credits
- Ensure you're using a supported model (gpt-4 or gpt-3.5-turbo)

**For Azure AI Foundry users:**
- Verify your Azure OpenAI endpoint URL is correct (should include `https://` and end with `/`)
- Check your Azure OpenAI API key is valid
- Ensure your deployment name matches exactly what you configured in Azure portal
- Verify your Azure OpenAI resource has sufficient quota
- Check that your model deployment is active and not in a failed state
- Ensure you have proper network access to your Azure OpenAI endpoint

### PowerPoint Generation Issues

If PowerPoint generation fails:
- Ensure python-pptx is installed correctly
- Check write permissions in the output directory

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

Never commit your `.env` file or any files containing credentials to version control. The `.gitignore` file is configured to exclude these files.

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.

## Roadmap

Future enhancements planned:
- ✅ ~~Support for more Azure resource types~~ (Now analyzes ALL resources in subscription!)
- ✅ ~~Web-based GUI~~ (Modern, Azure-inspired web interface now available!)
- ✅ ~~Cost analysis and optimization recommendations~~ (Comprehensive cost analysis with prioritized recommendations!)
- Compliance checking (PCI DSS, HIPAA, etc.)
- Historical trending and comparison
- Azure DevOps integration for backlog import
- Export to Excel format

## Acknowledgments

- Microsoft Azure SDK for Python
- OpenAI for AI capabilities
- python-pptx for PowerPoint generation

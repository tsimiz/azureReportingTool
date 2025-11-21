# Azure Reporting Tool

A comprehensive tool to automatically generate reports and analysis of Azure environments against Microsoft's best practices. The tool fetches data from your Azure subscription, uses AI to analyze it against best practices, generates a PowerPoint presentation, and creates an improvement backlog.

## Features

- **Automated Azure Data Fetching**: Retrieves information about your Azure resources including:
  - Virtual Machines
  - Storage Accounts
  - Network Security Groups
  - Virtual Networks
  - Resource Groups

- **AI-Powered Analysis**: Uses OpenAI GPT-4 to analyze your Azure environment against Microsoft's best practices across:
  - Security
  - Performance
  - Cost Optimization
  - Operational Excellence
  - Reliability

- **PowerPoint Report Generation**: Creates a professional PowerPoint presentation with:
  - Executive Summary
  - Resource Overview
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

Edit `.env` and add your credentials:

**Option A: Using OpenAI API**

```env
# Azure credentials
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id

# OpenAI API key
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
```

**Option B: Using Azure AI Foundry (Azure OpenAI Service)**

```env
# Azure credentials
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id

# Azure AI Foundry / Azure OpenAI Service
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_KEY=your-azure-openai-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

#### How to get Azure credentials:

1. **Create a Service Principal**:
   ```bash
   az ad sp create-for-rbac --name "AzureReportingTool" --role Reader --scopes /subscriptions/YOUR_SUBSCRIPTION_ID
   ```

2. The command will output:
   - `appId` → Use as `AZURE_CLIENT_ID`
   - `password` → Use as `AZURE_CLIENT_SECRET`
   - `tenant` → Use as `AZURE_TENANT_ID`

3. Get your Subscription ID:
   ```bash
   az account show --query id -o tsv
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
- AI analysis settings
- Report content preferences

## Usage

### Basic Usage

```bash
python -m azure_reporter.main
```

Or if installed as a package:

```bash
azure-reporter
```

### With Custom Configuration

```bash
python -m azure_reporter.main --config /path/to/config.yaml
```

### With Verbose Logging

```bash
python -m azure_reporter.main --verbose
```

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
│       ├── main.py                    # Main orchestration script
│       ├── modules/
│       │   ├── __init__.py
│       │   ├── azure_fetcher.py       # Azure data fetching
│       │   ├── ai_analyzer.py         # AI-powered analysis
│       │   ├── powerpoint_generator.py # PPT generation
│       │   └── backlog_generator.py   # Backlog creation
│       └── utils/
│           ├── __init__.py
│           ├── config_loader.py       # Configuration management
│           └── logger.py              # Logging utilities
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
- Support for more Azure resource types
- Cost analysis and optimization recommendations
- Compliance checking (PCI DSS, HIPAA, etc.)
- Historical trending and comparison
- Azure DevOps integration for backlog import
- Export to other formats (PDF, Excel)

## Acknowledgments

- Microsoft Azure SDK for Python
- OpenAI for AI capabilities
- python-pptx for PowerPoint generation

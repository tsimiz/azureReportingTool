# Quick Start Guide

Get started with Azure Reporting Tool in 5 minutes!

## Prerequisites

- Python 3.8+ installed
- Azure subscription
- OpenAI API key OR Azure AI Foundry (Azure OpenAI Service) endpoint

## Step 1: Install Dependencies

```bash
# Clone the repository
git clone https://github.com/tsimiz/azureReportingTool.git
cd azureReportingTool

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Azure Access

### Create Azure Service Principal

```bash
# Login to Azure
az login

# Create service principal
az ad sp create-for-rbac --name "AzureReportingTool" --role Reader --scopes /subscriptions/YOUR_SUBSCRIPTION_ID
```

This will output:
```json
{
  "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "displayName": "AzureReportingTool",
  "password": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "tenant": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### Get Subscription ID

```bash
az account show --query id -o tsv
```

## Step 3: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

Add your credentials to `.env`:

**Option A: Using OpenAI API**

```env
AZURE_TENANT_ID=<tenant from service principal output>
AZURE_CLIENT_ID=<appId from service principal output>
AZURE_CLIENT_SECRET=<password from service principal output>
AZURE_SUBSCRIPTION_ID=<your subscription id>

OPENAI_API_KEY=<your OpenAI API key>
OPENAI_MODEL=gpt-4
```

**Option B: Using Azure AI Foundry (Azure OpenAI)**

```env
AZURE_TENANT_ID=<tenant from service principal output>
AZURE_CLIENT_ID=<appId from service principal output>
AZURE_CLIENT_SECRET=<password from service principal output>
AZURE_SUBSCRIPTION_ID=<your subscription id>

# Azure AI Foundry / Azure OpenAI Service
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_KEY=<your Azure OpenAI key>
AZURE_OPENAI_DEPLOYMENT=<your deployment name>
```

See [README.md](README.md) for detailed instructions on setting up Azure AI Foundry.

## Step 4: Run the Tool

```bash
python -m azure_reporter.main
```

Or use the example script:

```bash
python example_usage.py
```

## Step 5: View Results

Check the `output/` directory for:
- `azure_report.pptx` - PowerPoint presentation
- `improvement_backlog.csv` - Improvement items in CSV
- `improvement_backlog.json` - Backlog in JSON format
- `improvement_backlog.md` - Human-readable backlog

## Customizing the Report

To customize settings:

```bash
# Copy example configuration
cp config.example.yaml config.yaml

# Edit configuration
nano config.yaml

# Run with custom config
python -m azure_reporter.main --config config.yaml
```

## Troubleshooting

### "Authentication failed"

- Verify credentials in `.env` file
- Ensure Service Principal has Reader role
- Try: `az login` to verify Azure access

### "No resources found"

- Check that resources exist in the subscription
- Verify Service Principal has access to resource groups
- Check the subscription ID is correct

### "OpenAI API error" or "Azure OpenAI error"

**For OpenAI API:**
- Verify OpenAI API key is valid
- Check you have API credits
- Try using gpt-3.5-turbo instead of gpt-4 in `.env`

**For Azure AI Foundry:**
- Verify your Azure OpenAI endpoint and key are correct
- Check that your deployment name matches what's in Azure portal
- Ensure your Azure OpenAI resource is active and has quota available

## Next Steps

- Review the generated PowerPoint report
- Check the improvement backlog
- Prioritize critical and high-severity findings
- See [README.md](README.md) for detailed documentation

## Getting Help

- Check [README.md](README.md) for full documentation
- Review example configuration in `config.example.yaml`
- Open an issue on GitHub for bugs or questions

## Security Notes

- Never commit `.env` file to version control
- Store credentials securely
- Use principle of least privilege for Service Principal
- Rotate credentials regularly

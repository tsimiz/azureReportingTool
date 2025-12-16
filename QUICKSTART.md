# 🚀 Quick Start Guide

This guide will help you get the Azure Reporting Tool up and running in minutes.

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ [.NET 8.0 SDK](https://dotnet.microsoft.com/download)
- ✅ [Node.js 18+](https://nodejs.org/)
- ✅ [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- ✅ Azure subscription with appropriate permissions

## ⚡ 5-Minute Setup

### 1️⃣ Clone and Navigate

```bash
git clone https://github.com/tsimiz/azureReportingTool.git
cd azureReportingTool
```

### 2️⃣ Start Backend (Terminal 1)

```bash
cd backend/AzureReportingTool.Api
dotnet run
```

Backend will start on: `http://localhost:5000`

### 3️⃣ Start Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Frontend will start on: `http://localhost:5173`

### 4️⃣ Login to Azure

```bash
az login
```

### 5️⃣ Open Browser

Navigate to `http://localhost:5173` and start analyzing!

## 🔧 Configuration

### Environment Variables (Optional)

Create `.env` file in project root:

```env
# Azure Configuration
AZURE_SUBSCRIPTION_ID=your-subscription-id

# OpenAI Configuration (Option A)
OPENAI_API_KEY=sk-proj-xxxxx
OPENAI_MODEL=gpt-4

# Azure OpenAI Configuration (Option B)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4-deployment
```

## 🐛 Troubleshooting

### Backend Issues

**Port Already in Use:**
```bash
# Change port in Properties/launchSettings.json
"applicationUrl": "http://localhost:5001"
```

**Azure Authentication Failed:**
```bash
# Re-login to Azure
az login
az account show
```

### Frontend Issues

**Port Already in Use:**
```bash
# Use different port
npm run dev -- --port 3000
```

**API Connection Failed:**
- Check backend is running on `http://localhost:5000`
- Update `API_BASE_URL` in `frontend/src/App.tsx` if needed

## 📚 Next Steps

- [Full Documentation](README.md)
- [API Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)
- [Contributing Guide](CONTRIBUTING.md)

## 💡 Tips

- Use `dotnet watch run` in backend for hot reload
- Frontend supports hot module replacement by default
- Add `--verbose` flag for detailed logging

## 🆘 Getting Help

- 📖 Check [README.md](README.md)
- 💬 Open an [Issue](https://github.com/tsimiz/azureReportingTool/issues)
- 📧 Contact maintainers

---

**Ready to analyze your Azure environment? Let's go! 🚀**

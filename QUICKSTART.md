# 🚀 Quick Start Guide

This guide will help you get the Azure Reporting Tool up and running in minutes.

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ [.NET 10 SDK](https://dotnet.microsoft.com/download)
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

Backend will start on: `http://localhost:5175` (default .NET development port)

### 3️⃣ Start Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Frontend will start on: `http://localhost:5173`

> **Note**: The frontend is pre-configured to connect to `http://localhost:5175/api`. If your backend runs on a different port, see the [Frontend Configuration](#frontend-configuration) section below.

### 4️⃣ Login to Azure

```bash
az login
```

### 5️⃣ Open Browser

Navigate to `http://localhost:5173` and start analyzing!

## 🔧 Configuration

### Frontend Configuration

To configure the frontend to connect to a backend on a different port or address:

1. **Copy the example environment file:**
   ```bash
   cd frontend
   cp .env.example .env
   ```

2. **Edit `.env` and set your backend URL:**
   ```env
   # For Docker deployment (port 5000)
   VITE_API_BASE_URL=http://localhost:5000/api
   
   # For custom backend
   VITE_API_BASE_URL=http://your-backend-host:port/api
   ```

3. **Restart the frontend:**
   ```bash
   npm run dev
   ```

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
- Check backend is running (default port: `http://localhost:5175`)
- If backend uses a different port, create `frontend/.env` file:
  ```env
  VITE_API_BASE_URL=http://localhost:YOUR_PORT/api
  ```
- Restart frontend after changing `.env` file

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

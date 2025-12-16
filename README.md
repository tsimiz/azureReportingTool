# ☁️ Azure Reporting Tool

<div align="center">

![Azure](https://img.shields.io/badge/Azure-0078D4?style=for-the-badge&logo=microsoft-azure&logoColor=white)
![.NET](https://img.shields.io/badge/.NET-512BD4?style=for-the-badge&logo=dotnet&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Material-UI](https://img.shields.io/badge/Material--UI-007FFF?style=for-the-badge&logo=mui&logoColor=white)

**A modern, enterprise-grade tool for comprehensive Azure environment analysis and reporting** ⚡

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 🚀 Overview

The **Azure Reporting Tool** is a cutting-edge solution built with **.NET 8.0** backend and **React with TypeScript** frontend, designed to automatically generate comprehensive reports and analysis of Azure environments against Microsoft's best practices.

### ✨ What's New

- 🎯 **Modern Stack**: Rebuilt from Python to .NET & React for enhanced performance
- 🎨 **Beautiful UI**: Material-UI based interface with Azure-inspired design
- ⚡ **Real-time Analysis**: Fast, efficient resource scanning with async processing
- 🔒 **Secure by Default**: Built with security best practices
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices

---

## 🌟 Features

### 🔍 **Comprehensive Resource Analysis**
- **All Azure Resources**: Analyzes every resource type in your subscription
- **Deep Insights**: Virtual Machines, Storage Accounts, NSGs, Virtual Networks, and more
- **Resource Discovery**: Automatic detection and categorization

### 🤖 **AI-Powered Intelligence**
- **OpenAI Integration**: Leverages GPT-4 for intelligent analysis
- **Azure OpenAI Support**: Full support for Azure AI Foundry
- **Smart Recommendations**: Context-aware security and optimization suggestions

### 💰 **Cost Optimization**
- **Savings Identification**: Finds underutilized and orphaned resources
- **Reserved Instances**: Recommendations for RI opportunities
- **Tag-based Tracking**: Cost allocation tag compliance
- **Priority Rankings**: Focuses on high-impact optimizations

### 🏷️ **Tag Compliance**
- **Policy Enforcement**: Validates required tags across resources
- **Value Validation**: Detects placeholder and invalid tag values
- **Compliance Reporting**: Resource group level compliance metrics
- **Non-compliant Tracking**: Detailed reports of missing tags

### 📊 **Professional Reporting**
- **Multiple Formats**: PDF and PowerPoint exports
- **Executive Summaries**: High-level overviews for stakeholders
- **Detailed Findings**: Technical details for implementation teams
- **Improvement Backlog**: Prioritized action items in CSV/JSON/Markdown

---

## 🛠️ Technology Stack

### Backend (.NET 8.0)
```
├── ASP.NET Core Web API
├── Azure SDK for .NET
├── Azure.Identity (DefaultAzureCredential)
├── Azure.ResourceManager
└── DocumentFormat.OpenXml & iTextSharp
```

### Frontend (React + TypeScript)
```
├── React 18+ with TypeScript
├── Material-UI (MUI) Components
├── Axios for API communication
└── Vite for build tooling
```

---

## 📋 Prerequisites

### Required
- ✅ **.NET 8.0 SDK** or higher
- ✅ **Node.js 18+** and **npm**
- ✅ **Azure subscription** with appropriate permissions
- ✅ **Azure CLI** (for authentication)

### Optional (for AI Features)
- 🤖 **OpenAI API key**, OR
- ☁️ **Azure AI Foundry** (Azure OpenAI Service) endpoint and key

---

## 🚀 Quick Start

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/tsimiz/azureReportingTool.git
cd azureReportingTool
```

### 2️⃣ Setup Backend (.NET)

```bash
cd backend
dotnet restore
dotnet build
```

### 3️⃣ Setup Frontend (React)

```bash
cd ../frontend
npm install
```

### 4️⃣ Azure Authentication

Login to your Azure account:

```bash
az login
```

Get your subscription ID:

```bash
az account show --query id -o tsv
```

### 5️⃣ Start the Applications

**Terminal 1 - Backend:**
```bash
cd backend/AzureReportingTool.Api
dotnet run
```
The API will start on `https://localhost:5000` (or `http://localhost:5000`)

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```
The UI will start on `http://localhost:5173`

### 6️⃣ Access the Application

Open your browser and navigate to:
```
http://localhost:5173
```

---

## 📖 Documentation

### Configuration

#### Azure Authentication

The tool supports **DefaultAzureCredential** which supports multiple authentication methods:

1. **Azure CLI** (Recommended for development)
2. **Service Principal** (Recommended for production)
3. **Managed Identity** (For Azure-hosted deployments)

#### AI Configuration

**Option A: OpenAI API**
```json
{
  "OpenAI": {
    "ApiKey": "sk-proj-xxxxx",
    "Model": "gpt-4"
  }
}
```

**Option B: Azure AI Foundry**
```json
{
  "AzureOpenAI": {
    "Endpoint": "https://your-resource.openai.azure.com/",
    "ApiKey": "your-key",
    "Deployment": "gpt-4-deployment"
  }
}
```

### Analysis Settings

Configure analysis through the React UI:

- 📁 **Output Directory**: Where reports are saved
- 📝 **Report Filename**: Name of generated reports
- 📊 **Export Format**: PDF or PowerPoint
- 🤖 **AI Analysis**: Enable/disable AI-powered insights
- 🏷️ **Tag Analysis**: Configure required tags and validation

---

## 📁 Project Structure

```
azureReportingTool/
├── backend/                          # .NET Backend
│   ├── AzureReportingTool.Api/      # Web API Project
│   │   ├── Controllers/             # API Controllers
│   │   └── Program.cs               # API Configuration
│   ├── AzureReportingTool.Core/     # Core Business Logic
│   │   ├── Models/                  # Data Models
│   │   └── Services/                # Business Services
│   └── AzureReportingTool.sln       # Solution File
├── frontend/                         # React Frontend
│   ├── src/
│   │   ├── App.tsx                  # Main Application Component
│   │   ├── main.tsx                 # Application Entry Point
│   │   └── App.css                  # Styles
│   ├── package.json                 # Node Dependencies
│   └── vite.config.ts               # Vite Configuration
└── README.md                         # This File
```

---

## 🎨 Features Showcase

### Modern UI Dashboard
- 📊 Real-time statistics cards
- 🎯 Interactive findings table
- 📋 Executive summary view
- 🎨 Azure-inspired color scheme

### Analysis Capabilities
- ✅ Automated resource discovery
- 🔍 Security compliance checks
- 💰 Cost optimization recommendations
- 🏷️ Tag compliance validation
- 📈 Detailed reporting

---

## 🔧 Development

### Build Backend

```bash
cd backend
dotnet build
```

### Build Frontend

```bash
cd frontend
npm run build
```

### Run Tests

```bash
# Backend tests
cd backend
dotnet test

# Frontend tests
cd frontend
npm test
```

---

## 🐳 Docker Support (Coming Soon)

```bash
# Build and run with Docker Compose
docker-compose up
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Workflow

1. 🍴 Fork the repository
2. 🌿 Create a feature branch (`git checkout -b feature/amazing-feature`)
3. 💾 Commit your changes (`git commit -m 'Add amazing feature'`)
4. 📤 Push to the branch (`git push origin feature/amazing-feature`)
5. 🔀 Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌟 Roadmap

- [ ] 🔐 Advanced security scanning integration
- [ ] 📊 Historical trend analysis
- [ ] 🔗 Azure DevOps integration
- [ ] 📧 Email report delivery
- [ ] 🌐 Multi-tenant support
- [ ] 📱 Mobile app
- [ ] 🎯 Custom compliance frameworks
- [ ] 🔄 Automated remediation workflows

---

## 💬 Support

- 📧 **Email**: Open an issue on GitHub
- 💬 **Discussions**: Use GitHub Discussions
- 🐛 **Bug Reports**: Create an issue with the bug template
- 💡 **Feature Requests**: Create an issue with the feature request template

---

## 🙏 Acknowledgments

- **Microsoft Azure** - For the comprehensive Azure SDK
- **OpenAI** - For AI capabilities
- **Material-UI** - For the beautiful React components
- **.NET Foundation** - For the excellent .NET platform
- **React Team** - For the amazing frontend framework

---

<div align="center">

**Built with ❤️ using .NET 8.0 & React**

⭐ **Star us on GitHub!** ⭐

[Report Bug](https://github.com/tsimiz/azureReportingTool/issues) · [Request Feature](https://github.com/tsimiz/azureReportingTool/issues) · [Documentation](https://github.com/tsimiz/azureReportingTool/wiki)

</div>

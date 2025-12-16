# 🤝 Contributing to Azure Reporting Tool

Thank you for your interest in contributing! This guide will help you get started.

## 📋 Code of Conduct

Be respectful, inclusive, and collaborative. We're building something great together! 🚀

## 🐛 Reporting Issues

### Before Creating an Issue

- 🔍 Search existing issues to avoid duplicates
- ✅ Use the latest version of the tool
- 📝 Gather relevant information

### Creating an Issue

Include:
- 🖥️ **Environment**: .NET version, Node.js version, OS
- 🔢 **Version**: Tool version
- 📊 **Error Messages**: Full error logs
- 🔄 **Steps to Reproduce**: Detailed steps
- 🎯 **Expected Behavior**: What should happen
- 💥 **Actual Behavior**: What actually happens

## 💡 Suggesting Enhancements

1. Open an issue with the "enhancement" label
2. Describe the feature clearly
3. Explain the benefits
4. Provide use case examples
5. Consider implementation details

## 🛠️ Development Setup

### Prerequisites

```bash
# Required
.NET 10 SDK
Node.js 18+
Azure CLI
Git

# Optional
Docker Desktop
```

### Getting Started

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/azureReportingTool.git
cd azureReportingTool

# 2. Create feature branch
git checkout -b feature/amazing-feature

# 3. Setup backend
cd backend
dotnet restore
dotnet build

# 4. Setup frontend
cd ../frontend
npm install

# 5. Run tests
cd ../backend
dotnet test

cd ../frontend
npm test
```

## 📝 Code Style

### Backend (.NET)

```csharp
// Use C# naming conventions
public class MyService 
{
    // PascalCase for properties
    public string PropertyName { get; set; }
    
    // camelCase for private fields
    private readonly ILogger _logger;
    
    // Async methods end with Async
    public async Task<Result> ProcessAsync()
    {
        // Implementation
    }
}

// Use XML documentation
/// <summary>
/// Fetches Azure resources from subscription
/// </summary>
/// <param name="subscriptionId">The subscription ID</param>
/// <returns>List of Azure resources</returns>
public async Task<List<AzureResource>> FetchResourcesAsync(string subscriptionId)
```

**Guidelines:**
- ✅ Use nullable reference types
- ✅ Follow async/await patterns
- ✅ Use dependency injection
- ✅ Write XML documentation for public APIs
- ✅ Keep methods focused and small
- ✅ Use meaningful variable names
- ✅ Handle exceptions appropriately

### Frontend (React + TypeScript)

```typescript
// Use TypeScript interfaces
interface AnalysisResult {
  executiveSummary: string;
  findings: Finding[];
}

// Functional components with hooks
const AnalysisComponent: React.FC = () => {
  const [data, setData] = useState<AnalysisResult | null>(null);
  
  useEffect(() => {
    // Side effects here
  }, []);
  
  return (
    <Box>
      {/* JSX here */}
    </Box>
  );
};

// Use arrow functions for handlers
const handleClick = async () => {
  try {
    const result = await fetchData();
    setData(result);
  } catch (error) {
    console.error('Error:', error);
  }
};
```

**Guidelines:**
- ✅ Use TypeScript for type safety
- ✅ Functional components with hooks
- ✅ Material-UI components
- ✅ Meaningful component names
- ✅ Extract reusable components
- ✅ Handle loading and error states
- ✅ Use async/await for API calls

## 🧪 Testing

### Backend Tests

```bash
cd backend
dotnet test
```

### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage
```

### Integration Tests

```bash
# Run both backend and frontend
docker-compose up
# Test the full flow
```

## 📦 Pull Request Process

1. **Update Documentation**
   - Update README.md if needed
   - Add inline code comments
   - Update API documentation

2. **Test Your Changes**
   - ✅ All tests pass
   - ✅ No build warnings
   - ✅ Linter passes
   - ✅ Manual testing completed

3. **Commit Guidelines**
   ```bash
   # Use conventional commits
   feat: Add new feature
   fix: Fix bug
   docs: Update documentation
   style: Code style changes
   refactor: Code refactoring
   test: Add tests
   chore: Maintenance tasks
   ```

4. **Create Pull Request**
   - Clear title and description
   - Reference related issues
   - Add screenshots for UI changes
   - Request reviewers

5. **Code Review**
   - Address feedback promptly
   - Keep discussions focused
   - Be open to suggestions

## 🏗️ Project Structure

```
azureReportingTool/
├── backend/
│   ├── AzureReportingTool.Api/      # Web API
│   │   ├── Controllers/             # API endpoints
│   │   └── Program.cs               # Startup
│   └── AzureReportingTool.Core/     # Business logic
│       ├── Models/                  # Data models
│       └── Services/                # Services
├── frontend/
│   └── src/
│       ├── components/              # React components
│       ├── services/                # API clients
│       └── App.tsx                  # Main app
└── docs/                            # Documentation
```

## 🎯 Areas for Contribution

### High Priority
- 🔐 Enhanced security scanning
- 📊 Additional report formats
- 🌍 Internationalization
- 🧪 Test coverage improvement

### Medium Priority
- 📈 Performance optimizations
- 🎨 UI/UX enhancements
- 📱 Mobile responsiveness
- 🔧 Configuration improvements

### Good First Issues
- 📝 Documentation updates
- 🐛 Bug fixes
- 🧹 Code cleanup
- ✨ Minor features

## 🔍 Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Works on multiple platforms
- [ ] No breaking changes (or documented)

## 📖 Additional Resources

- [.NET Documentation](https://docs.microsoft.com/en-us/dotnet/)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Material-UI Documentation](https://mui.com/)
- [Azure SDK Documentation](https://docs.microsoft.com/en-us/dotnet/azure/)

## 💬 Communication

- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code contributions
- **Discussions**: General questions and ideas

## 🙏 Recognition

All contributors will be:
- Listed in the README
- Mentioned in release notes
- Part of our growing community

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

<div align="center">

**Thank you for contributing! 🎉**

Every contribution, no matter how small, makes a difference.

</div>

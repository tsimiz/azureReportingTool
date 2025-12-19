import { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Paper,
  Button,
  TextField,
  FormControlLabel,
  Checkbox,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  MenuItem,
  Select,
  InputLabel,
  FormControl,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
} from '@mui/material';
import {
  CloudQueue as CloudIcon,
  Analytics as AnalyticsIcon,
  Security as SecurityIcon,
  SmartToy as AiIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Lightbulb as LightbulbIcon,
} from '@mui/icons-material';
import axios from 'axios';
import './App.css';

// API Base URL - configurable via VITE_API_BASE_URL environment variable
// Default: http://localhost:5175/api (matches .NET default port)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5175/api';
const DEFAULT_SUBSCRIPTION_ID = '00000000-0000-0000-0000-000000000000';

interface AnalysisSettings {
  outputDirectory: string;
  reportFilename: string;
  exportFormat: string;
  aiEnabled: boolean;
  aiModel: string;
  aiTemperature: number;
  resources: {
    virtualMachines: boolean;
    storageAccounts: boolean;
    networkSecurityGroups: boolean;
    virtualNetworks: boolean;
    analyzeAllResources: boolean;
  };
  tagAnalysis: {
    enabled: boolean;
    requiredTags: string[];
    invalidTagValues: string[];
  };
  aiConfiguration: {
    provider: 'openai' | 'azure' | 'none';
    openAI: {
      apiKey: string;
      model: string;
    };
    azureAI: {
      endpoint: string;
      apiKey: string;
      deployment: string;
    };
  };
}

interface Finding {
  id: string;
  resourceName: string;
  category: string;
  severity: string;
  issue: string;
  recommendation: string;
  estimatedEffort: string;
  priority: number;
}

interface PillarSummary {
  name: string;
  overview: string;
  currentState: string;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  score: string;
}

interface ExecutiveSummaryPillars {
  security: PillarSummary;
  costOptimization: PillarSummary;
  operationalExcellence: PillarSummary;
  reliability: PillarSummary;
  performanceEfficiency: PillarSummary;
}

interface AnalysisResult {
  executiveSummary: string;
  executiveSummaryPillars?: ExecutiveSummaryPillars;
  findings: Finding[];
  statistics: {
    TotalResources?: number;
    TotalFindings?: number;
    CriticalFindings?: number;
    HighFindings?: number;
  };
  tagCompliance?: Record<string, unknown>;
  costAnalysis?: Record<string, unknown>;
}

interface LoginStatus {
  logged_in: boolean;
  user: string;
  subscription_id: string;
  subscription_name: string;
}

interface Subscription {
  id: string;
  name: string;
  is_default: boolean;
}

function App() {
  const [subscriptionId, setSubscriptionId] = useState(DEFAULT_SUBSCRIPTION_ID);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [analyzeAllSubscriptions, setAnalyzeAllSubscriptions] = useState(false);
  const [loginStatus, setLoginStatus] = useState<LoginStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [settings, setSettings] = useState<AnalysisSettings>({
    outputDirectory: './output',
    reportFilename: 'azure_report',
    exportFormat: 'pdf',
    aiEnabled: true,
    aiModel: 'gpt-4',
    aiTemperature: 0.3,
    resources: {
      virtualMachines: true,
      storageAccounts: true,
      networkSecurityGroups: true,
      virtualNetworks: true,
      analyzeAllResources: true,
    },
    tagAnalysis: {
      enabled: false,
      requiredTags: [],
      invalidTagValues: [],
    },
    aiConfiguration: {
      provider: 'none',
      openAI: {
        apiKey: '',
        model: 'gpt-4',
      },
      azureAI: {
        endpoint: '',
        apiKey: '',
        deployment: 'gpt-4',
      },
    },
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch login status and subscriptions on component mount
  useEffect(() => {
    const fetchAzureStatus = async () => {
      try {
        // Fetch login status
        const loginResponse = await axios.get(`${API_BASE_URL}/Azure/login-status`);
        setLoginStatus(loginResponse.data);
        
        // Fetch subscriptions
        try {
          const subsResponse = await axios.get(`${API_BASE_URL}/Azure/subscriptions`);
          setSubscriptions(subsResponse.data);
          
          // Set default subscription if available
          const defaultSub = subsResponse.data.find((sub: Subscription) => sub.is_default);
          if (defaultSub) {
            setSubscriptionId(defaultSub.id);
          } else if (subsResponse.data.length > 0) {
            setSubscriptionId(subsResponse.data[0].id);
          }
        } catch (err) {
          console.error('Failed to fetch subscriptions:', err);
          // Still set default from login status if subscription fetch fails
          if (loginResponse.data.subscription_id) {
            setSubscriptionId(loginResponse.data.subscription_id);
          }
        }
      } catch (err) {
        console.error('Failed to fetch Azure status:', err);
        setError('Failed to connect to backend API. Please ensure the backend is running.');
      } finally {
        setLoadingStatus(false);
      }
    };

    fetchAzureStatus();
  }, []);

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      // Note: Backend currently supports single subscription analysis
      // When analyzeAllSubscriptions is true, we would need backend support for batch processing
      const response = await axios.post(`${API_BASE_URL}/Analysis/run`, {
        subscriptionId: analyzeAllSubscriptions ? 'all' : subscriptionId,
        analyzeAllSubscriptions,
        settings,
      });
      setResult(response.data);
    } catch (err) {
      const errorMessage = (err as { response?: { data?: { error?: string } } })?.response?.data?.error || 'An error occurred during analysis';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string): 'error' | 'warning' | 'info' | 'success' | 'default' => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const getScoreColor = (score: string): 'success' | 'warning' | 'error' | 'info' => {
    switch (score.toLowerCase()) {
      case 'high':
        return 'success';
      case 'medium':
        return 'warning';
      case 'low':
        return 'error';
      default:
        return 'info';
    }
  };

  const renderPillarSummary = (pillar: PillarSummary) => {
    return (
      <Accordion key={pillar.name} defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              {pillar.name}
            </Typography>
            <Chip 
              label={`Score: ${pillar.score}`} 
              color={getScoreColor(pillar.score)}
              sx={{ mr: 2 }}
            />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box>
            <Typography variant="body2" color="text.secondary" paragraph>
              {pillar.overview}
            </Typography>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              Current State Assessment
            </Typography>
            <Typography variant="body2" paragraph sx={{ bgcolor: 'background.default', p: 2, borderRadius: 1 }}>
              {pillar.currentState}
            </Typography>
            
            {pillar.strengths.length > 0 && (
              <>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom sx={{ mt: 2 }}>
                  ✅ Strengths
                </Typography>
                <List dense>
                  {pillar.strengths.map((strength, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <CheckCircleIcon color="success" />
                      </ListItemIcon>
                      <ListItemText primary={strength} />
                    </ListItem>
                  ))}
                </List>
              </>
            )}
            
            {pillar.weaknesses.length > 0 && (
              <>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom sx={{ mt: 2 }}>
                  ⚠️ Areas for Improvement
                </Typography>
                <List dense>
                  {pillar.weaknesses.map((weakness, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <WarningIcon color="warning" />
                      </ListItemIcon>
                      <ListItemText primary={weakness} />
                    </ListItem>
                  ))}
                </List>
              </>
            )}
            
            {pillar.recommendations.length > 0 && (
              <>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom sx={{ mt: 2 }}>
                  💡 Recommendations
                </Typography>
                <List dense>
                  {pillar.recommendations.map((recommendation, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <LightbulbIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText primary={recommendation} />
                    </ListItem>
                  ))}
                </List>
              </>
            )}
          </Box>
        </AccordionDetails>
      </Accordion>
    );
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static" sx={{ background: 'linear-gradient(135deg, #0078d4 0%, #004578 100%)' }}>
        <Toolbar>
          <CloudIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ☁️ Azure Reporting Tool
          </Typography>
          {loadingStatus ? (
            <Chip label="Connecting..." color="default" variant="filled" sx={{ bgcolor: 'rgba(255,255,255,0.9)', color: '#0078d4', fontWeight: 'bold' }} />
          ) : loginStatus?.logged_in ? (
            <Chip label={`✓ ${loginStatus.user}`} color="success" variant="filled" sx={{ bgcolor: '#4caf50', color: 'white', fontWeight: 'bold' }} />
          ) : (
            <Chip label="✗ Not Logged In" color="error" variant="filled" sx={{ bgcolor: '#f44336', color: 'white', fontWeight: 'bold' }} />
          )}
        </Toolbar>
      </AppBar>

      <Box sx={{ width: '100%', px: 4, mt: 4, mb: 4 }}>
        {/* Subscription Selection */}
        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <SecurityIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6">Azure Subscription</Typography>
          </Box>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 8 }}>
              <FormControl fullWidth>
                <InputLabel id="subscription-select-label">Subscription</InputLabel>
                <Select
                  labelId="subscription-select-label"
                  id="subscription-select"
                  value={subscriptionId}
                  label="Subscription"
                  onChange={(e) => setSubscriptionId(e.target.value)}
                  disabled={analyzeAllSubscriptions || subscriptions.length === 0}
                >
                  {subscriptions.length === 0 ? (
                    <MenuItem value={DEFAULT_SUBSCRIPTION_ID}>
                      No subscriptions available
                    </MenuItem>
                  ) : (
                    subscriptions.map((sub) => (
                      <MenuItem key={sub.id} value={sub.id}>
                        {sub.name} {sub.is_default ? '(Default)' : ''}
                      </MenuItem>
                    ))
                  )}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={analyzeAllSubscriptions}
                    onChange={(e) => setAnalyzeAllSubscriptions(e.target.checked)}
                    disabled={subscriptions.length === 0}
                  />
                }
                label="Analyze All Subscriptions"
                sx={{ mt: 1 }}
              />
            </Grid>
          </Grid>
          {analyzeAllSubscriptions && subscriptions.length > 0 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Analysis will be performed across all {subscriptions.length} subscriptions
            </Alert>
          )}
        </Paper>

        {/* Settings */}
        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <AnalyticsIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6">Analysis Settings</Typography>
          </Box>
          
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Report Filename"
                value={settings.reportFilename}
                onChange={(e) => setSettings({ ...settings, reportFilename: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                select
                label="Export Format"
                value={settings.exportFormat}
                onChange={(e) => setSettings({ ...settings, exportFormat: e.target.value })}
                SelectProps={{ native: true }}
              >
                <option value="pdf">PDF</option>
                <option value="pptx">PowerPoint</option>
              </TextField>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={settings.aiEnabled}
                    onChange={(e) => setSettings({ ...settings, aiEnabled: e.target.checked })}
                  />
                }
                label="🤖 Enable AI Analysis"
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={settings.tagAnalysis.enabled}
                    onChange={(e) => setSettings({
                      ...settings,
                      tagAnalysis: { ...settings.tagAnalysis, enabled: e.target.checked }
                    })}
                  />
                }
                label="🏷️ Enable Tag Compliance Analysis"
              />
            </Grid>
          </Grid>

          <Box sx={{ mt: 3 }}>
            <Button
              variant="contained"
              size="large"
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <AnalyticsIcon />}
              onClick={handleRunAnalysis}
              disabled={loading}
              sx={{ background: 'linear-gradient(45deg, #0078d4 30%, #50b0f0 90%)' }}
            >
              {loading ? 'Analyzing...' : '🔍 Run Analysis'}
            </Button>
          </Box>
        </Paper>

        {/* AI Configuration */}
        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <AiIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6">AI Configuration</Typography>
          </Box>
          
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 4 }}>
              <FormControl fullWidth>
                <InputLabel id="ai-provider-label">AI Provider</InputLabel>
                <Select
                  labelId="ai-provider-label"
                  value={settings.aiConfiguration.provider}
                  label="AI Provider"
                  onChange={(e) => setSettings({
                    ...settings,
                    aiConfiguration: {
                      ...settings.aiConfiguration,
                      provider: e.target.value as 'openai' | 'azure' | 'none'
                    }
                  })}
                >
                  <MenuItem value="none">None</MenuItem>
                  <MenuItem value="openai">OpenAI</MenuItem>
                  <MenuItem value="azure">Azure AI Foundry</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          {settings.aiConfiguration.provider === 'openai' && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                OpenAI Configuration
              </Typography>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 8 }}>
                  <TextField
                    fullWidth
                    label="API Key"
                    type="password"
                    value={settings.aiConfiguration.openAI.apiKey}
                    onChange={(e) => setSettings({
                      ...settings,
                      aiConfiguration: {
                        ...settings.aiConfiguration,
                        openAI: {
                          ...settings.aiConfiguration.openAI,
                          apiKey: e.target.value
                        }
                      }
                    })}
                    placeholder="sk-proj-xxxxxxxxxxxxx"
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 4 }}>
                  <TextField
                    fullWidth
                    label="Model"
                    value={settings.aiConfiguration.openAI.model}
                    onChange={(e) => setSettings({
                      ...settings,
                      aiConfiguration: {
                        ...settings.aiConfiguration,
                        openAI: {
                          ...settings.aiConfiguration.openAI,
                          model: e.target.value
                        }
                      }
                    })}
                    placeholder="gpt-4"
                  />
                </Grid>
              </Grid>
            </Box>
          )}

          {settings.aiConfiguration.provider === 'azure' && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                Azure AI Foundry Configuration
              </Typography>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <TextField
                    fullWidth
                    label="Endpoint"
                    value={settings.aiConfiguration.azureAI.endpoint}
                    onChange={(e) => setSettings({
                      ...settings,
                      aiConfiguration: {
                        ...settings.aiConfiguration,
                        azureAI: {
                          ...settings.aiConfiguration.azureAI,
                          endpoint: e.target.value
                        }
                      }
                    })}
                    placeholder="https://your-resource.openai.azure.com/"
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <TextField
                    fullWidth
                    label="API Key"
                    type="password"
                    value={settings.aiConfiguration.azureAI.apiKey}
                    onChange={(e) => setSettings({
                      ...settings,
                      aiConfiguration: {
                        ...settings.aiConfiguration,
                        azureAI: {
                          ...settings.aiConfiguration.azureAI,
                          apiKey: e.target.value
                        }
                      }
                    })}
                    placeholder="your-api-key"
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <TextField
                    fullWidth
                    label="Deployment Name"
                    value={settings.aiConfiguration.azureAI.deployment}
                    onChange={(e) => setSettings({
                      ...settings,
                      aiConfiguration: {
                        ...settings.aiConfiguration,
                        azureAI: {
                          ...settings.aiConfiguration.azureAI,
                          deployment: e.target.value
                        }
                      }
                    })}
                    placeholder="gpt-4-deployment"
                  />
                </Grid>
              </Grid>
            </Box>
          )}
        </Paper>

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Results */}
        {result && (
          <>
            {/* Statistics Cards */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Card elevation={3}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Total Resources
                    </Typography>
                    <Typography variant="h4" component="div" color="primary">
                      {result.statistics.TotalResources || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Card elevation={3}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Total Findings
                    </Typography>
                    <Typography variant="h4" component="div" color="info.main">
                      {result.statistics.TotalFindings || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Card elevation={3}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Critical Findings
                    </Typography>
                    <Typography variant="h4" component="div" color="error.main">
                      {result.statistics.CriticalFindings || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Card elevation={3}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      High Findings
                    </Typography>
                    <Typography variant="h4" component="div" color="warning.main">
                      {result.statistics.HighFindings || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Executive Summary */}
            {result.executiveSummary && !result.executiveSummaryPillars && (
              <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  📋 Executive Summary
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {result.executiveSummary}
                </Typography>
              </Paper>
            )}

            {/* CAF/WAF Pillar-Based Executive Summary */}
            {result.executiveSummaryPillars && (
              <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
                  📋 Executive Summary - Microsoft CAF/WAF Analysis
                </Typography>
                <Alert severity="info" sx={{ mb: 3 }}>
                  This analysis evaluates your Azure environment against Microsoft's Cloud Adoption Framework (CAF) 
                  and Well-Architected Framework (WAF) best practices across five core pillars.
                </Alert>
                
                {renderPillarSummary(result.executiveSummaryPillars.security)}
                {renderPillarSummary(result.executiveSummaryPillars.costOptimization)}
                {renderPillarSummary(result.executiveSummaryPillars.operationalExcellence)}
                {renderPillarSummary(result.executiveSummaryPillars.reliability)}
                {renderPillarSummary(result.executiveSummaryPillars.performanceEfficiency)}
              </Paper>
            )}

            {/* Findings Table */}
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                🔍 Findings
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Priority</TableCell>
                      <TableCell>Severity</TableCell>
                      <TableCell>Resource</TableCell>
                      <TableCell>Category</TableCell>
                      <TableCell>Issue</TableCell>
                      <TableCell>Recommendation</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {result.findings.map((finding) => (
                      <TableRow key={finding.id}>
                        <TableCell>{finding.priority}</TableCell>
                        <TableCell>
                          <Chip
                            label={finding.severity}
                            color={getSeverityColor(finding.severity)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{finding.resourceName}</TableCell>
                        <TableCell>{finding.category}</TableCell>
                        <TableCell>{finding.issue}</TableCell>
                        <TableCell>{finding.recommendation}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </>
        )}
      </Box>

      <Box component="footer" sx={{ py: 3, px: 2, mt: 'auto', backgroundColor: '#f5f5f5', textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Azure Reporting Tool | Powered by .NET 10 & React with TypeScript ⚡
        </Typography>
      </Box>
    </Box>
  );
}

export default App;

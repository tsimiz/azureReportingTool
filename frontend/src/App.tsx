import { useState } from 'react';
import {
  Container,
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
} from '@mui/material';
import {
  CloudQueue as CloudIcon,
  Analytics as AnalyticsIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import axios from 'axios';
import './App.css';

const API_BASE_URL = 'http://localhost:5000/api';

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

interface AnalysisResult {
  executiveSummary: string;
  findings: Finding[];
  statistics: Record<string, any>;
  tagCompliance?: any;
  costAnalysis?: any;
}

function App() {
  const [subscriptionId, setSubscriptionId] = useState('00000000-0000-0000-0000-000000000000');
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
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/Analysis/run`, {
        subscriptionId,
        settings,
      });
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'An error occurred during analysis');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
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

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static" sx={{ background: 'linear-gradient(135deg, #0078d4 0%, #004578 100%)' }}>
        <Toolbar>
          <CloudIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ☁️ Azure Reporting Tool
          </Typography>
          <Chip label="Powered by .NET & React" color="primary" variant="outlined" sx={{ bgcolor: 'rgba(255,255,255,0.2)' }} />
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        {/* Subscription Selection */}
        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <SecurityIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6">Azure Subscription</Typography>
          </Box>
          <TextField
            fullWidth
            label="Subscription ID"
            value={subscriptionId}
            onChange={(e) => setSubscriptionId(e.target.value)}
            variant="outlined"
          />
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
            {result.executiveSummary && (
              <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  📋 Executive Summary
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {result.executiveSummary}
                </Typography>
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
                            color={getSeverityColor(finding.severity) as any}
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
      </Container>

      <Box component="footer" sx={{ py: 3, px: 2, mt: 'auto', backgroundColor: '#f5f5f5', textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Azure Reporting Tool | Powered by .NET 10 & React with TypeScript ⚡
        </Typography>
      </Box>
    </Box>
  );
}

export default App;

import React, { useState, useEffect } from 'react';
import { Box, Snackbar, Alert, Fade } from '@mui/material';
import axios from 'axios';

import AppLayout from './layout/AppLayout';
import LeftSidebar from './layout/LeftSidebar';
import ChatPanel from './layout/ChatPanel';
import RightPanel from './layout/RightPanel';
import ConnectionModal from './modals/ConnectionModal';

// Setup axios to use the correct backend URL
axios.defaults.baseURL = 'http://localhost:8000';

function QueryInterface() {
  // State variables
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState([]);
  const [generatedCode, setGeneratedCode] = useState('');
  const [executionTime, setExecutionTime] = useState(0);
  const [apiExecutionTime, setApiExecutionTime] = useState(0);
  const [attempts, setAttempts] = useState(1);
  const [selectedConnection, setSelectedConnection] = useState('');
  const [connections, setConnections] = useState([]);
  const [usingMockData, setUsingMockData] = useState(false);
  const [showConnectionModal, setShowConnectionModal] = useState(false);
  const [initialConnectionValues, setInitialConnectionValues] = useState(null);
  const [messages, setMessages] = useState([]);
  const [processSteps, setProcessSteps] = useState([]);
  const [agentPhases, setAgentPhases] = useState([]);
  const [alert, setAlert] = useState({ show: false, message: '', severity: 'info' });
  const [compilationSessionId, setCompilationSessionId] = useState(null);
  const [wsConnection, setWsConnection] = useState(null);
  
  // Function to establish WebSocket connection for real-time phase updates
  const connectToPhaseWebSocket = (sessionId) => {
    if (!sessionId) return;
    
    // Close existing connection if any
    if (wsConnection) {
      wsConnection.close();
    }
    
    const wsUrl = `ws://localhost:8000/ws/phases/${sessionId}`;
    console.log(`Connecting to WebSocket: ${wsUrl}`);
    
    try {
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log(`WebSocket connection established for session: ${sessionId}`);
        setWsConnection(ws);
        
        // Send initial ping to request current phase status
        ws.send('ping');
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);
          
          if (data.phases && Array.isArray(data.phases)) {
            // Make sure each phase has id, name, status, and thinking fields
            const normalizedPhases = data.phases.map(phase => ({
              id: phase.id || 'unknown',
              name: phase.name || 'Unknown Phase',
              status: phase.status || 'pending',
              thinking: phase.thinking || '',
              order: phase.order || 0
            }));
            
            // Sort phases by their order to ensure correct display
            normalizedPhases.sort((a, b) => a.order - b.order);
            
            // Update agent phases with real-time data
            setAgentPhases(normalizedPhases);
            
            // If any phase is in progress, the system is still loading
            const stillProcessing = normalizedPhases.some(phase => phase.status === 'in_progress');
            if (!stillProcessing && loading) {
              // All phases are complete or failed, done loading
              setLoading(false);
            }
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setAlert({
          show: true,
          message: 'WebSocket connection error. Phase updates may not be real-time.',
          severity: 'warning'
        });
      };
      
      ws.onclose = (event) => {
        console.log(`WebSocket connection closed: ${event.code} ${event.reason}`);
        // Handle phases from response data if WebSocket fails
        setWsConnection(null);
        
        // If we're still loading, we should stop since the connection is closed
        if (loading) {
          setLoading(false);
        }
      };
      
      // Set up ping interval to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000); // every 30 seconds
      
      // Clean up on unmount
      return () => {
        clearInterval(pingInterval);
        if (ws) ws.close();
      };
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      // Fall back to using the phases from the API response
    }
  };
  
  // Clean up WebSocket on component unmount
  useEffect(() => {
    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, [wsConnection]);
  
  // Fetch connections on component mount
  useEffect(() => {
    async function fetchConnections() {
      try {
        const response = await axios.get('/connections');
        console.log('Connection response:', response.data);
        
        setConnections(Object.entries(response.data).map(([id, conn]) => ({
          id,
          name: conn.name,
          type: conn.type,
          host: conn.host,
          port: conn.port,
          database: conn.database,
          username: conn.username
        })));
        
        // If connections exist, select the first one
        if (Object.keys(response.data).length > 0) {
          setSelectedConnection(Object.keys(response.data)[0]);
        }
      } catch (error) {
        console.error('Error fetching connections:', error);
        
        // Show connection error alert
        setAlert({
          show: true,
          message: 'Failed to connect to backend server. Please check if the server is running.',
          severity: 'error'
        });
        
        // Create a default connection if none exists
        const defaultConnection = {
          id: 'default',
          name: 'Default Connection',
          type: 'spark',
          host: 'localhost',
          port: 8020,
          database: 'default',
          username: 'user'
        };
        
        setConnections([defaultConnection]);
        setSelectedConnection('default');
      }
    }
    
    fetchConnections();
  }, []);
  
  // Handle query submission
  const handleSubmitQuery = async (queryText) => {
    if (!queryText.trim()) {
      setError('Please enter a query');
      return;
    }
    
    if (!selectedConnection) {
      setError('Please select a database connection');
      return;
    }
    
    setLoading(true);
    setError(null);
    setResult([]);
    setGeneratedCode('');
    setAgentPhases([]);
    
    // Show longer processing steps
    await showDetailedProcessSteps(queryText);
    
    // Add user message to chat
    setMessages(prev => [...prev, { sender: 'user', content: queryText }]);
    
    try {
      console.log('Sending query to backend:', queryText);
      
      const response = await axios.post('/query', {
        query: queryText.trim(),
        connection_id: selectedConnection
      });
      
      console.log('Query response:', response.data);
      
      // Process response
      if (response.data) {
        setResult(response.data.results || []);
        setGeneratedCode(response.data.generated_code || '');
        setExecutionTime(response.data.executionTime || 0);
        setApiExecutionTime(response.data.apiExecutionTime || 0);
        setAttempts(response.data.attempts || 1);
        
        // Add system message about query execution
        const resultCount = response.data.results ? response.data.results.length : 0;
        
        // Use the actual query execution time for the message
        const queryExecTime = response.data.executionTime 
          ? response.data.executionTime.toFixed(3) 
          : '0.000';
          
        // Get total API execution time
        const apiExecTime = response.data.apiExecutionTime
          ? response.data.apiExecutionTime.toFixed(3)
          : queryExecTime;
          
        // Show both times if they're different
        let executionMessage = '';
        if (response.data.attempts && response.data.attempts > 1) {
          executionMessage = `Query executed successfully in ${queryExecTime}s after ${response.data.attempts} attempts (total time: ${apiExecTime}s). Found ${resultCount} records.`;
        } else {
          executionMessage = `Query executed successfully in ${queryExecTime}s. Found ${resultCount} records.`;
        }
        
        setMessages(prev => [...prev, { 
          sender: 'system', 
          content: executionMessage
        }]);
        
        // Store compilation session ID and connect to WebSocket for real-time updates
        if (response.data.compilationSessionId) {
          setCompilationSessionId(response.data.compilationSessionId);
          connectToPhaseWebSocket(response.data.compilationSessionId);
        }
        
        // Handle agent phases if provided
        if (response.data.agentPhases && response.data.agentPhases.length > 0) {
          setAgentPhases(response.data.agentPhases);
        }
        
        // If there's AI thinking/response included
        if (response.data.ai_thinking) {
          setMessages(prev => [...prev, { 
            sender: 'ai', 
            content: response.data.ai_thinking,
            isThinking: true
          }]);
        }
        
        if (response.data.ai_response) {
          setMessages(prev => [...prev, { 
            sender: 'ai', 
            content: response.data.ai_response
          }]);
        }
      }
    } catch (error) {
      console.error('Query execution failed:', error);
      
      let errorMessage = 'Query execution failed';
      if (error.response && error.response.data && error.response.data.detail) {
        errorMessage = error.response.data.detail;
      }
      
      setError(errorMessage);
      setAlert({
        show: true,
        message: errorMessage,
        severity: 'error'
      });
      
      // Add error message to chat
      setMessages(prev => [...prev, { 
        sender: 'system', 
        content: `Error: ${errorMessage}`
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Show detailed process steps with longer delays
  const showDetailedProcessSteps = async (queryText) => {
    return new Promise(resolve => {
      // Initialize processing
      setProcessSteps([
        { title: 'Initializing Agent', status: 'processing' }
      ]);
      
      // Schema Analysis
      setTimeout(() => {
        setProcessSteps([
          { title: 'Initializing Agent', status: 'completed' },
          { title: 'Schema Analysis', status: 'processing' }
        ]);
        
        // Schema Analysis completed
        setTimeout(() => {
          setProcessSteps([
            { title: 'Initializing Agent', status: 'completed' },
            { title: 'Schema Analysis', status: 'completed' },
            { title: 'Query Planning', status: 'processing' }
          ]);
          
          // Query Planning completed
          setTimeout(() => {
            setProcessSteps([
              { title: 'Initializing Agent', status: 'completed' },
              { title: 'Schema Analysis', status: 'completed' },
              { title: 'Query Planning', status: 'completed' },
              { title: 'Code Generation', status: 'processing' }
            ]);
            
            // Code Generation completed
            setTimeout(() => {
              setProcessSteps([
                { title: 'Initializing Agent', status: 'completed' },
                { title: 'Schema Analysis', status: 'completed' },
                { title: 'Query Planning', status: 'completed' },
                { title: 'Code Generation', status: 'completed' },
                { title: 'Executing Query', status: 'processing' }
              ]);
              
              // Query Execution
              setTimeout(() => {
                setProcessSteps([
                  { title: 'Initializing Agent', status: 'completed' },
                  { title: 'Schema Analysis', status: 'completed' },
                  { title: 'Query Planning', status: 'completed' },
                  { title: 'Code Generation', status: 'completed' },
                  { title: 'Executing Query', status: 'completed' }
                ]);
                
                // Wait before resolving to ensure steps are visible
                setTimeout(() => {
                  resolve();
                }, 1000);
              }, 2000);
            }, 3000);
          }, 3000);
        }, 2000);
      }, 1500);
    });
  };
  
  // Handle connection operations
  const handleOpenConnectionModal = (connection = null) => {
    setInitialConnectionValues(connection);
    setShowConnectionModal(true);
  };
  
  const handleSaveConnection = async (connectionData) => {
    try {
      if (connectionData.id && connectionData.id !== 'default') {
        // Update existing connection
        await axios.put(`/connections/${connectionData.id}`, connectionData);
        
        // Update local state
        const updatedConnections = connections.map(conn => 
          conn.id === connectionData.id ? { ...connectionData } : conn
        );
        setConnections(updatedConnections);
      } else {
        // Create new connection
        const response = await axios.post('/connections', connectionData);
        const newConnection = response.data;
        
        // Update local state
        setConnections([...connections, newConnection]);
        setSelectedConnection(newConnection.id);
      }
      
      setAlert({
        show: true,
        message: `Connection "${connectionData.name}" saved successfully`,
        severity: 'success'
      });
    } catch (error) {
      console.error('Error saving connection:', error);
      
      setAlert({
        show: true,
        message: `Failed to save connection: ${error.message}`,
        severity: 'error'
      });
    }
  };
  
  // Handle selecting a chat history item
  const handleHistorySelect = (historyItem) => {
    setQuery(historyItem.query);
    handleSubmitQuery(historyItem.query);
  };
  
  // Handle alert close
  const handleAlertClose = () => {
    setAlert({ ...alert, show: false });
  };

  // Handle database selection from the chat panel
  const handleConnectionSelectFromChat = (connectionId) => {
    if (connectionId !== selectedConnection) {
      setSelectedConnection(connectionId);
      // Add system message about context switch
      const newConnection = connections.find(conn => conn.id === connectionId);
      if (newConnection) {
        setMessages(prev => [...prev, { 
          sender: 'system', 
          content: `Switched database context to "${newConnection.database}"`,
          isContextSwitch: true
        }]);
      }
    }
  };
  
  // Handle starting a new chat session
  const handleNewSession = () => {
    // Reset all chat state but maintain connection
    setMessages([]);
    setQuery('');
    setResult([]);
    setGeneratedCode('');
    setProcessSteps([]);
    setAgentPhases([]);
    setExecutionTime(0);
    setApiExecutionTime(0);
    setAttempts(1);
    
    setAlert({
      show: true,
      message: 'Started a new chat session',
      severity: 'info'
    });
  };

  return (
    <>
      <AppLayout
        leftSidebar={
          <LeftSidebar 
            onHistorySelect={handleHistorySelect}
            onSchemaSelect={(table, column) => {
              setQuery(prev => prev + ` ${table}.${column}`);
            }}
            connections={connections}
            selectedConnection={selectedConnection}
            onConnectionSelect={handleConnectionSelectFromChat}
            onAddConnection={() => handleOpenConnectionModal()}
            onEditConnection={conn => handleOpenConnectionModal(conn)}
          />
        }
        center={
          <ChatPanel
            onSubmitQuery={handleSubmitQuery}
            messages={messages}
            loading={loading}
            processSteps={processSteps}
            query={query}
            setQuery={setQuery}
            agentPhases={agentPhases}
            activeConnection={connections.find(conn => conn.id === selectedConnection) || null}
            connections={connections}
            onConnectionSelect={handleConnectionSelectFromChat}
            onNewSession={handleNewSession}
          />
        }
        rightPanel={
          <RightPanel 
            data={result}
            loading={loading}
            executionTime={executionTime}
            apiExecutionTime={apiExecutionTime}
            attempts={attempts}
            generatedCode={generatedCode}
          />
        }
      />
        
      {/* Connection Modal */}
      <ConnectionModal
        open={showConnectionModal}
        onClose={() => setShowConnectionModal(false)}
        onSave={handleSaveConnection}
        initialValues={initialConnectionValues}
        testing={loading}
      />
      
      {/* Alert Snackbar */}
      <Snackbar
        open={alert.show}
        autoHideDuration={6000}
        onClose={handleAlertClose}
        TransitionComponent={Fade}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleAlertClose} 
          severity={alert.severity}
          sx={{ borderRadius: 2 }}
          variant="filled"
        >
          {alert.message}
        </Alert>
      </Snackbar>
    </>
  );
}

export default QueryInterface; 
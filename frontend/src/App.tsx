import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import JobList from './pages/JobList';
import { QueryClient, QueryClientProvider } from 'react-query';
// Ant Design 5.x不再需要导入CSS文件，它使用CSS-in-JS方案

// 创建一个QueryClient实例
const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router basename="/xiaoyuan-recruitment">
        <div style={{ padding: '20px' }}>
          <Routes>
            <Route path="/" element={<JobList />} />
            <Route path="*" element={<div style={{ padding: '20px' }}>页面未找到</div>} />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;

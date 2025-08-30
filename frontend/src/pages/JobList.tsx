import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { Table, Typography, Button, Card, Row, Col, Input, Tag, Select, Space, Divider, Badge, Cascader, Modal, message, Menu, Dropdown, Collapse, Spin } from 'antd';
import { Link } from 'react-router-dom';
import { SearchOutlined, FilterOutlined, ReloadOutlined, SaveOutlined, DownOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { locationOptions } from '../data/locations';
import dayjs from 'dayjs';

const { Title } = Typography;
const { Search } = Input;
const { Option } = Select;
const { confirm } = Modal;

// 职位数据类型定义（与后端API返回格式匹配）
interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  salary_min?: number;
  salary_max?: number;
  job_type?: string;
  experience?: string;
  education?: string;
  industry?: string;
  posted_at?: string;
  deadline?: string;
  description?: string;
  source?: string;
  url?: string;
  status?: string;
  target_group?: string;
}

// 定义表格列类型
interface TableColumnsType<T> {
  title: string;
  dataIndex?: keyof T | string;
  key: string;
  width?: number | string;
  render?: (text: any, record: T, index: number) => React.ReactNode;
  sorter?: boolean | ((a: T, b: T) => number);
  sortDirections?: ('ascend' | 'descend')[];
}

const JobList: React.FC = () => {
  // 定义筛选条件状态
  const [filters, setFilters] = useState({
    keyword: '',
    company_type: '',
    job_type: '',
    location: '',
    target_group: '',
    salary_range: '',
    education: '',
    experience: ''
  });

  // 添加排序状态
  const [sortConfig, setSortConfig] = useState<{
    field?: string;
    order?: 'ascend' | 'descend';
  }>({
    field: 'posted_at',
    order: 'descend'
  });

  // 添加选择状态
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  
  // 添加保存筛选条件功能
  const [savedFilters, setSavedFilters] = useState<{name: string, filters: typeof filters}[]>([]);
  
  // 添加筛选条件名称状态
  const [filterName, setFilterName] = useState('');

  // 添加加载状态
  const [isRefreshing, setIsRefreshing] = useState(false);

  // 使用React Query获取职位列表数据
  const { data, isLoading, error, refetch } = useQuery<{ jobs: Job[]; total: number }>(
    ['jobs', filters, sortConfig],
    async () => {
      try {
        // 构建查询参数
        const params = new URLSearchParams();
        if (filters.keyword) params.append('keyword', filters.keyword);
        if (filters.company_type) params.append('company_type', filters.company_type);
        if (filters.job_type) params.append('job_type', filters.job_type);
        if (filters.location) params.append('location', filters.location);
        if (filters.target_group) params.append('target_group', filters.target_group);
        if (filters.salary_range) params.append('salary_range', filters.salary_range);
        if (filters.education) params.append('education', filters.education);
        if (filters.experience) params.append('experience', filters.experience);
        
        // 添加排序参数
        if (sortConfig.field) {
          params.append('sort_field', sortConfig.field);
          params.append('sort_order', sortConfig.order || 'descend');
        }
        
        // 发送请求
        const baseUrl = '/api';
        const url = `${baseUrl}/jobs${params.toString() ? `?${params.toString()}` : ''}`;
        
        // 添加超时处理
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15秒超时
        
        try {
          const response = await fetch(url, {
            signal: controller.signal,
            headers: {
              'Content-Type': 'application/json',
            }
          });
          clearTimeout(timeoutId);
          
          if (!response.ok) {
            let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            try {
              const errorData = await response.json();
              errorMessage = errorData.message || errorMessage;
            } catch {
              // 忽略JSON解析错误，使用默认错误消息
            }
            throw new Error(errorMessage);
          }
          
          const result = await response.json();
          return result;
        } catch (err: any) {
          if (err.name === 'AbortError') {
            throw new Error('请求超时，请检查网络连接或后端服务是否正常运行');
          }
          console.error('API请求错误:', err);
          throw err;
        }
      } catch (err: any) {
        console.error('API请求错误:', err);
        throw err;
      }
    },
    {
      enabled: true,
      refetchOnWindowFocus: false,
      staleTime: 60000,
      retry: (failureCount, error: any) => {
        // 如果是网络错误或超时，重试2次
        if (error?.message?.includes('fetch') || error?.message?.includes('超时')) {
          return failureCount < 2;
        }
        // 其他错误不重试
        return false;
      },
      onError: (err: any) => {
        message.error(`数据加载失败: ${err.message}`);
      }
    }
  );

  // 处理搜索和筛选
  const handleSearch = (value: string) => {
    setFilters(prev => ({ ...prev, keyword: value }));
  };

  // 处理筛选条件变化
  const handleFilterChange = (type: string, value: string) => {
    setFilters(prev => ({ ...prev, [type]: value }));
  };
  
  // 处理地点级联选择变化
  const handleLocationChange = (value: string[]) => {
    if (!value || value.length === 0) {
      setFilters(prev => ({ ...prev, location: '' }));
    } else if (value[0] === 'all') {
      setFilters(prev => ({ ...prev, location: '' }));
    } else if (value.length === 1) {
      setFilters(prev => ({ ...prev, location: value[0] }));
    } else if (value.length === 2) {
      setFilters(prev => ({ ...prev, location: value[1] }));
    }
  };
  
  // 重置所有筛选条件
  const resetFilters = () => {
    setFilters({
      keyword: '',
      company_type: '',
      job_type: '',
      location: '',
      target_group: '',
      salary_range: '',
      education: '',
      experience: ''
    });
    setSortConfig({ field: 'posted_at', order: 'descend' });
  };

  // 刷新数据
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refetch();
      message.success('数据刷新成功');
    } catch (error) {
      message.error('数据刷新失败');
    } finally {
      setIsRefreshing(false);
    }
  };

  // 批量操作函数
  const batchApply = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择职位');
      return;
    }
    
    confirm({
      title: '批量申请确认',
      icon: <ExclamationCircleOutlined />,
      content: `确定要申请选中的 ${selectedRowKeys.length} 个职位吗？`,
      okText: '确认申请',
      cancelText: '取消',
      onOk: async () => {
        try {
          // 模拟API调用
          const response = await fetch('/api/jobs/batch-apply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jobIds: selectedRowKeys })
          });
          
          if (!response.ok) {
            throw new Error('申请失败');
          }
          
          message.success(`已成功申请 ${selectedRowKeys.length} 个职位`);
          setSelectedRowKeys([]);
        } catch (error) {
          console.error('批量申请错误:', error);
          message.error('申请失败，请稍后重试');
        }
      }
    });
  };
  
  const batchCollect = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择职位');
      return;
    }
    
    confirm({
      title: '批量收藏确认',
      icon: <ExclamationCircleOutlined />,
      content: `确定要收藏选中的 ${selectedRowKeys.length} 个职位吗？`,
      okText: '确认收藏',
      cancelText: '取消',
      onOk: async () => {
        try {
          // 模拟API调用
          const response = await fetch('/api/jobs/batch-collect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jobIds: selectedRowKeys })
          });
          
          if (!response.ok) {
            throw new Error('收藏失败');
          }
          
          message.success(`已成功收藏 ${selectedRowKeys.length} 个职位`);
          setSelectedRowKeys([]);
        } catch (error) {
          console.error('批量收藏错误:', error);
          message.error('收藏失败，请稍后重试');
        }
      }
    });
  };

  // 保存当前筛选条件
  const saveCurrentFilters = () => {
    let inputValue = '';
    
    confirm({
      title: '保存筛选条件',
      content: (
        <div>
          <p>请输入筛选条件名称：</p>
          <Input 
            placeholder="输入筛选条件名称" 
            onChange={e => inputValue = e.target.value}
            onPressEnter={() => {
              if (inputValue.trim()) {
                handleSaveFilters(inputValue.trim());
              }
            }}
          />
        </div>
      ),
      onOk: () => {
        if (!inputValue.trim()) {
          message.error('请输入筛选条件名称');
          return Promise.reject('请输入筛选条件名称');
        }
        return handleSaveFilters(inputValue.trim());
      }
    });
  };

  const handleSaveFilters = (name: string) => {
    try {
      const newSavedFilters = [...savedFilters, { name, filters: { ...filters } }];
      setSavedFilters(newSavedFilters);
      localStorage.setItem('savedJobFilters', JSON.stringify(newSavedFilters));
      message.success('筛选条件保存成功');
      return Promise.resolve();
    } catch (error) {
      console.error('保存筛选条件错误:', error);
      message.error('保存失败，请稍后重试');
      return Promise.reject('保存失败');
    }
  };

  // 加载保存的筛选条件
  const loadSavedFilters = () => {
    try {
      const saved = localStorage.getItem('savedJobFilters');
      if (saved) {
        setSavedFilters(JSON.parse(saved));
      }
    } catch (error) {
      console.error('加载保存的筛选条件错误:', error);
      message.error('加载保存的筛选条件失败');
    }
  };

  // 使用保存的筛选条件
  const useSavedFilter = (savedFilter: typeof filters) => {
    setFilters(savedFilter);
    message.success('筛选条件已应用');
  };

  // 在useEffect中加载保存的筛选条件
  useEffect(() => {
    loadSavedFilters();
  }, []);

  // 表格列定义
  const columns: TableColumnsType<Job>[] = [
    {
      title: '职位名称',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: Job) => (
        <Link to={`/jobs/${record.id}`} style={{ color: '#1890ff', textDecoration: 'none' }}>
          {text}
        </Link>
      ),
      width: 200
    },
    {
      title: '公司',
      dataIndex: 'company',
      key: 'company',
      width: 150
    },
    {
      title: '所属行业',
      dataIndex: 'industry',
      key: 'industry',
      render: (text: string) => text || '-',
      width: 120
    },
    {
      title: '招聘职位',
      dataIndex: 'job_type',
      key: 'job_type',
      render: (text: string) => text || '-',
      width: 120
    },
    {
      title: '地点',
      dataIndex: 'location',
      key: 'location',
      width: 100
    },
    {
      title: '薪资',
      key: 'salary',
      render: (_, record) => {
        if (record.salary_min && record.salary_max) {
          return (
            <span style={{ color: '#f5222d', fontWeight: 'bold' }}>
              {(record.salary_min / 1000).toFixed(0)}k-{(record.salary_max / 1000).toFixed(0)}k
            </span>
          );
        }
        return <span style={{ color: '#999' }}>面议</span>;
      },
      width: 100,
      sorter: (a, b) => {
        const aMin = a.salary_min || 0;
        const bMin = b.salary_min || 0;
        return aMin - bMin;
      }
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      render: (text: string) => (
        <Tag color="cyan">{text || '未知'}</Tag>
      ),
      width: 80
    },
    {
      title: '招聘网址',
      dataIndex: 'url',
      key: 'url',
      render: (text: string) => (
        text ? (
          <a href={text} target="_blank" rel="noopener noreferrer">
            查看原始职位
          </a>
        ) : '-'
      ),
      width: 120
    },
    {
      title: '目标人群',
      dataIndex: 'target_group',
      key: 'target_group',
      render: (text: string) => {
        let color = 'default';
        if (text === '2024') color = 'green';
        if (text === '2025') color = 'blue';
        if (text === '2026') color = 'purple';
        return text ? <Tag color={color}>{text}届</Tag> : '-';
      },
      width: 100
    },
    {
      title: '职位描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => (
        <Typography.Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 0 }}>
          {text || '暂无描述'}
        </Typography.Paragraph>
      ),
      width: 300
    },
    {
      title: '发布时间',
      dataIndex: 'posted_at',
      key: 'posted_at',
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD') : '-',
      sorter: (a, b) => {
        if (!a.posted_at) return -1;
        if (!b.posted_at) return 1;
        return dayjs(a.posted_at).unix() - dayjs(b.posted_at).unix();
      },
      sortDirections: ['ascend', 'descend'],
      width: 120
    },
    {
      title: '截止时间',
      dataIndex: 'deadline',
      key: 'deadline',
      render: (text) => {
        if (!text) return '-';
        const deadline = dayjs(text);
        const now = dayjs();
        const isExpired = deadline.isBefore(now);
        const isExpiringSoon = deadline.diff(now, 'day') <= 3;
        
        return (
          <span style={{ 
            color: isExpired ? '#ff4d4f' : isExpiringSoon ? '#faad14' : '#52c41a'
          }}>
            {deadline.format('YYYY-MM-DD')}
            {isExpired && ' (已过期)'}
            {!isExpired && isExpiringSoon && ' (即将截止)'}
          </span>
        );
      },
      sorter: (a, b) => {
        if (!a.deadline) return -1;
        if (!b.deadline) return 1;
        return dayjs(a.deadline).unix() - dayjs(b.deadline).unix();
      },
      width: 120
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (text: string) => {
        const status = text || '招聘中';
        return (
          <Badge 
            status={status === '招聘中' ? 'success' : status === '已结束' ? 'error' : 'default'} 
            text={status} 
          />
        );
      },
      width: 100
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Job) => (
        <Space>
          <Button 
            type="primary" 
            size="small"
            onClick={() => {
              // 查看职位详情
              window.open(`/jobs/${record.id}`, '_blank');
            }}
          >
            查看
          </Button>
          <Button 
            type="primary" 
            danger 
            size="small"
            onClick={() => {
              confirm({
                title: '申请职位',
                content: `确定要申请「${record.title}」职位吗？`,
                onOk: async () => {
                  try {
                    // 模拟申请API
                    message.success('申请成功');
                  } catch (error) {
                    message.error('申请失败');
                  }
                }
              });
            }}
          >
            申请
          </Button>
        </Space>
      ),
      width: 120
    },
  ];

  // 加载状态
  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Typography.Text>正在加载职位数据...</Typography.Text>
        </div>
      </div>
    );
  }
  
  // 错误状态
  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <div style={{ marginBottom: 16 }}>
          <Typography.Title level={4} type="danger">
            数据加载失败
          </Typography.Title>
          <Typography.Text type="danger">
            {(error as Error).message}
          </Typography.Text>
        </div>
        <Space>
          <Button type="primary" onClick={handleRefresh} loading={isRefreshing}>
            重新加载
          </Button>
          <Button onClick={() => window.location.reload()}>
            刷新页面
          </Button>
        </Space>
      </div>
    );
  }
  
  // 无数据状态
  if (!data || !data.jobs || data.jobs.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Typography.Title level={4} type="secondary">
          暂无职位数据
        </Typography.Title>
        <Typography.Text type="secondary">
          请尝试调整筛选条件或稍后再试
        </Typography.Text>
        <div style={{ marginTop: 16 }}>
          <Space>
            <Button type="primary" onClick={resetFilters}>
              重置筛选
            </Button>
            <Button onClick={handleRefresh} loading={isRefreshing}>
              重新加载
            </Button>
          </Space>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '0 20px' }}>
      {/* 页面标题和操作按钮 */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: 16, 
        flexWrap: 'wrap',
        gap: '8px'
      }}>
        <Title level={4} style={{ margin: '8px 0' }}>校园招聘职位列表</Title>
        <Space wrap style={{ marginTop: '8px' }}>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={handleRefresh}
            loading={isRefreshing}
          >
            刷新数据
          </Button>
          <Button icon={<SaveOutlined />} onClick={saveCurrentFilters}>
            保存筛选
          </Button>
          <Dropdown 
            overlay={
              <Menu>
                {savedFilters.map((item, index) => (
                  <Menu.Item key={index} onClick={() => useSavedFilter(item.filters)}>
                    {item.name}
                  </Menu.Item>
                ))}
                {savedFilters.length === 0 && (
                  <Menu.Item disabled>暂无保存的筛选条件</Menu.Item>
                )}
              </Menu>
            }
            disabled={savedFilters.length === 0}
          >
            <Button icon={<DownOutlined />}>加载筛选</Button>
          </Dropdown>
        </Space>
      </div>

      {/* 筛选条件面板 */}
      <Card style={{ marginBottom: 16 }}>
        <Collapse defaultActiveKey={['1']} ghost>
          <Collapse.Panel header="筛选条件" key="1">
            <div style={{ marginBottom: 16 }}>
              <Row gutter={[16, 16]} align="middle">
                {/* 第一行筛选 */}
                <Col xs={24} sm={24} md={8} lg={6}>
                  <Input.Search 
                    placeholder="搜索职位名称、公司或描述" 
                    allowClear 
                    enterButton={<><SearchOutlined /> 搜索</>}
                    value={filters.keyword}
                    onChange={e => handleFilterChange('keyword', e.target.value)}
                    onSearch={handleSearch}
                  />
                </Col>
                <Col xs={24} sm={12} md={5} lg={4}>
                  <Select 
                    placeholder="公司类型" 
                    allowClear 
                    style={{ width: '100%' }}
                    value={filters.company_type || undefined}
                    onChange={value => handleFilterChange('company_type', value || '')}
                  >
                    <Option value="央国企">央国企</Option>
                    <Option value="外企">外企</Option>
                    <Option value="民企">民企</Option>
                    <Option value="事业单位">事业单位</Option>
                    <Option value="银行">银行</Option>
                  </Select>
                </Col>
                <Col xs={24} sm={12} md={5} lg={4}>
                  <Select 
                    placeholder="招聘类型" 
                    allowClear 
                    style={{ width: '100%' }}
                    value={filters.job_type || undefined}
                    onChange={value => handleFilterChange('job_type', value || '')}
                  >
                    <Option value="春招">春招</Option>
                    <Option value="秋招">秋招</Option>
                    <Option value="补录">补录</Option>
                    <Option value="秋招提前批">秋招提前批</Option>
                  </Select>
                </Col>
                <Col xs={24} sm={12} md={5} lg={4}>
                  <Button 
                    icon={<FilterOutlined />} 
                    onClick={resetFilters}
                    style={{ width: '100%' }}
                  >
                    重置筛选
                  </Button>
                </Col>
                
                {/* 第二行筛选 */}
                <Col xs={24} sm={12} md={5} lg={4}>
                  <Cascader 
                    options={locationOptions}
                    placeholder="工作地点" 
                    allowClear 
                    style={{ width: '100%' }}
                    onChange={handleLocationChange}
                    changeOnSelect
                    expandTrigger="hover"
                  />
                </Col>
                <Col xs={24} sm={12} md={5} lg={4}>
                  <Select 
                    placeholder="目标人群" 
                    allowClear 
                    style={{ width: '100%' }}
                    value={filters.target_group || undefined}
                    onChange={value => handleFilterChange('target_group', value || '')}
                  >
                    <Option value="2024">2024届</Option>
                    <Option value="2025">2025届</Option>
                    <Option value="2026">2026届</Option>
                  </Select>
                </Col>
                <Col xs={24} sm={12} md={5} lg={4}>
                  <Select 
                    placeholder="薪资范围" 
                    allowClear 
                    style={{ width: '100%' }}
                    value={filters.salary_range || undefined}
                    onChange={value => handleFilterChange('salary_range', value || '')}
                  >
                    <Option value="0-10000">10K以下</Option>
                    <Option value="10000-20000">10K-20K</Option>
                    <Option value="20000-30000">20K-30K</Option>
                    <Option value="30000-50000">30K-50K</Option>
                    <Option value="50000-999999">50K以上</Option>
                  </Select>
                </Col>
                <Col xs={24} sm={12} md={5} lg={4}>
                  <Select 
                    placeholder="学历要求" 
                    allowClear 
                    style={{ width: '100%' }}
                    value={filters.education || undefined}
                    onChange={value => handleFilterChange('education', value || '')}
                  >
                    <Option value="大专">大专</Option>
                    <Option value="本科">本科</Option>
                    <Option value="硕士">硕士</Option>
                    <Option value="博士">博士</Option>
                  </Select>
                </Col>
                <Col xs={24} sm={12} md={5} lg={4}>
                  <Select 
                    placeholder="经验要求" 
                    allowClear 
                    style={{ width: '100%' }}
                    value={filters.experience || undefined}
                    onChange={value => handleFilterChange('experience', value || '')}
                  >
                    <Option value="应届生">应届生</Option>
                    <Option value="1年以下">1年以下</Option>
                    <Option value="1-3年">1-3年</Option>
                    <Option value="3-5年">3-5年</Option>
                    <Option value="5年以上">5年以上</Option>
                  </Select>
                </Col>
              </Row>
            </div>
          </Collapse.Panel>
        </Collapse>
      </Card>
        
      <Divider style={{ margin: '12px 0' }} />
      
      {/* 批量操作按钮 */}
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button 
            type="primary" 
            disabled={selectedRowKeys.length === 0}
            onClick={batchApply}
          >
            批量申请 ({selectedRowKeys.length})
          </Button>
          <Button 
            disabled={selectedRowKeys.length === 0}
            onClick={batchCollect}
          >
            批量收藏 ({selectedRowKeys.length})
          </Button>
          <Typography.Text type="secondary">
            共找到 {data?.total || 0} 个职位
          </Typography.Text>
        </Space>
      </div>
      
      {/* 职位列表表格 */}
      <Table 
        rowSelection={{
          selectedRowKeys,
          onChange: setSelectedRowKeys,
          selections: [
            Table.SELECTION_ALL,
            Table.SELECTION_INVERT,
            Table.SELECTION_NONE
          ]
        }}
        columns={columns} 
        dataSource={data?.jobs || []} 
        rowKey="id"
        pagination={{
          total: data?.total || 0,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
          pageSizeOptions: ['10', '20', '50', '100'],
          defaultPageSize: 20
        }}
        loading={isLoading}
        onChange={(pagination, tableFilters, sorter) => {
          // 处理排序变化
          if (sorter && !Array.isArray(sorter) && sorter.field) {
            setSortConfig({
              field: sorter.field as string,
              order: sorter.order
            });
          }
        }}
        scroll={{ x: 1500 }}
        size="middle"
      />
    </div>
  );
};

export default JobList;

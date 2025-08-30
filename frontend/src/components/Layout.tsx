import React from 'react';
import { Layout as AntLayout, Menu, Typography } from 'antd';
import {
  HomeOutlined,
  FileTextOutlined,
  UserOutlined,
  BellOutlined,
  LogoutOutlined
} from '@ant-design/icons';
import { Outlet, Link } from 'react-router-dom';

const { Header, Content, Sider } = AntLayout;
const { Title } = Typography;

const Layout: React.FC = () => {
  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header className="header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Title level={3} style={{ color: 'white', margin: 0 }}>招聘管理系统</Title>
        <div style={{ color: 'white' }}>欢迎使用</div>
      </Header>
      <AntLayout>
        <Sider width={200} className="site-layout-background">
          <Menu
            mode="inline"
            defaultSelectedKeys={['1']}
            style={{ height: '100%', borderRight: 0 }}
          >
            <Menu.Item key="1" icon={<HomeOutlined />}>
              <Link to="/">职位列表</Link>
            </Menu.Item>
            <Menu.Item key="2" icon={<BellOutlined />}>
              <Link to="/announcements">通知公告</Link>
            </Menu.Item>
            <Menu.Item key="3" icon={<FileTextOutlined />}>
              <Link to="/resume">简历中心</Link>
            </Menu.Item>
            <Menu.Item key="4" icon={<UserOutlined />}>
              <Link to="/user">用户中心</Link>
            </Menu.Item>
            <Menu.Item key="5" icon={<LogoutOutlined />}>
              <Link to="/login">退出登录</Link>
            </Menu.Item>
          </Menu>
        </Sider>
        <AntLayout style={{ padding: '0 24px 24px' }}>
          <Content
            className="site-layout-background"
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
            }}
          >
            <Outlet />
          </Content>
        </AntLayout>
      </AntLayout>
    </AntLayout>
  );
};

export default Layout;
import React from 'react';
import { Card, Typography } from 'antd';
import { useParams } from 'react-router-dom';

const { Title } = Typography;

const JobDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <Card>
      <Title level={4}>职位详情</Title>
      <p>职位ID: {id}</p>
      <p>职位信息将在此显示</p>
    </Card>
  );
};

export default JobDetail;
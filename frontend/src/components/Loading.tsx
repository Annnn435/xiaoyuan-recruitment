import React from 'react';
import { Spin, Card, Row, Col } from 'antd';

const Loading: React.FC = () => {
  return (
    <Card style={{ marginTop: 16 }}>
      <Row gutter={16} justify="center" align="middle" style={{ height: 300 }}>
        <Col>
          <Spin size="large" tip="加载中..." />
        </Col>
      </Row>
    </Card>
  );
};

export default Loading;
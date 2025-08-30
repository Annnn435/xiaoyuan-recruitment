from simple_app import app, db

with app.app_context():
    # 删除所有表
    db.drop_all()
    print('✅ 数据库表已删除')
    
    # 重新创建表
    db.create_all()
    print('✅ 数据库表已创建')
    
    # 初始化数据库
    from simple_app import init_database
    init_database()
    print('✅ 数据库初始化完成')
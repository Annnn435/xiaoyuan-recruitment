# Netlify 部署指南

## 快速部署步骤

### 1. 准备工作
确保你的代码已经推送到 GitHub 仓库。

### 2. 连接 Netlify
1. 访问 [Netlify](https://www.netlify.com/)
2. 点击 "Sign up" 或 "Log in"
3. 选择 "GitHub" 登录
4. 授权 Netlify 访问你的 GitHub 账户

### 3. 部署项目
1. 在 Netlify 控制台，点击 "New site from Git"
2. 选择 "GitHub"
3. 找到并选择你的 `xiaoyuan` 仓库
4. 配置构建设置：
   - **Branch to deploy**: `main`
   - **Build command**: `cd frontend && npm run build`
   - **Publish directory**: `frontend/dist`
5. 点击 "Deploy site"

### 4. 自动配置
项目根目录的 `netlify.toml` 文件会自动配置以下设置：
- 构建命令和发布目录
- React Router 支持（SPA 重定向）
- 静态资源缓存优化
- Node.js 版本设置

### 5. 部署完成
- Netlify 会自动构建和部署你的应用
- 每次推送到 `main` 分支都会触发自动部署
- 你会获得一个免费的 `.netlify.app` 域名

## 优势

✅ **零配置部署** - 只需连接 GitHub 仓库
✅ **自动部署** - 代码推送后自动构建和部署
✅ **免费 HTTPS** - 自动提供 SSL 证书
✅ **全球 CDN** - 快速的内容分发网络
✅ **预览部署** - Pull Request 自动生成预览链接
✅ **自定义域名** - 支持绑定自己的域名

## 故障排除

如果部署失败，请检查：
1. `frontend/package.json` 中的构建脚本是否正确
2. 依赖是否完整安装
3. 构建过程中是否有错误

查看详细的构建日志可以在 Netlify 控制台的 "Deploys" 页面找到。

## 下一步

部署成功后，你可以：
- 设置自定义域名
- 配置环境变量
- 设置表单处理
- 添加 Netlify Functions（无服务器函数）
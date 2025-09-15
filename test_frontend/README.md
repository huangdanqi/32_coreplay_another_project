# CorePlay Agent Test Frontend

A comprehensive Vue3 frontend for testing the CorePlay Agent system. This frontend allows you to test all agents, modify prompts, configure LLM providers, and verify everything works in the actual environment.

## 🚀 Features

- **Multi-Agent Testing**: Test Diary, Sensor Event, BaZi/WuXing, and Event agents
- **LLM Configuration**: Manage multiple LLM providers with failover settings
- **Prompt Editor**: Edit and test prompts for all agents with live preview
- **Real-time Testing**: Test configurations directly against the backend API
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Live Status Monitoring**: Real-time connection and system status

## 📋 Prerequisites

- Node.js 16+ and npm/yarn
- CorePlay Agent backend running on port 5000
- Modern web browser with JavaScript enabled

## 🛠️ Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd test_frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. **Open your browser:**
   Navigate to `http://localhost:3000`

## 🏗️ Project Structure

```
test_frontend/
├── src/
│   ├── components/          # Reusable Vue components
│   ├── views/               # Main page components
│   │   ├── Dashboard.vue    # System overview dashboard
│   │   ├── AgentTester.vue  # Agent testing interface
│   │   ├── LLMConfig.vue    # LLM provider configuration
│   │   └── PromptEditor.vue  # Prompt editing interface
│   ├── stores/              # Pinia state management
│   │   └── appStore.js      # Global application state
│   ├── services/            # API communication
│   │   └── apiService.js    # Backend API service
│   ├── router/              # Vue Router configuration
│   │   └── index.js         # Route definitions
│   ├── App.vue              # Main application component
│   ├── main.js              # Application entry point
│   └── style.css            # Global styles
├── package.json             # Dependencies and scripts
├── vite.config.js           # Vite configuration
└── index.html               # HTML template
```

## 🎯 Usage Guide

### 1. Dashboard
- **System Overview**: Check connection status, available providers, and recent tests
- **Quick Actions**: Access all major features with one click
- **Status Monitoring**: Real-time system health indicators

### 2. Agent Tester
- **Select Agent**: Choose from Diary, Sensor, BaZi/WuXing, or Event agents
- **Configure Input**: Set up test data using JSON format
- **LLM Settings**: Select provider and configure options
- **Run Tests**: Execute tests and view results in real-time

### 3. LLM Configuration
- **Provider Management**: Add, edit, and remove LLM providers
- **Connection Testing**: Test provider connectivity
- **Global Settings**: Configure failover and performance options
- **Priority Management**: Set provider priority and capabilities

### 4. Prompt Editor
- **Template Management**: Load and save prompt templates
- **Live Editing**: Edit system and user prompts with syntax highlighting
- **Validation Rules**: Configure output format and validation
- **Test Prompts**: Test prompts with sample data

## 🔧 Configuration

### Backend API Configuration
The frontend connects to the backend API via proxy configuration in `vite.config.js`:

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true,
      secure: false
    }
  }
}
```

### Environment Variables
Create a `.env` file for environment-specific settings:

```env
VITE_API_BASE_URL=http://localhost:5000
VITE_APP_TITLE=CorePlay Agent Test Frontend
VITE_DEFAULT_PROVIDER=zhipu
```

## 📡 API Endpoints

The frontend communicates with these backend endpoints:

### Health & Configuration
- `GET /api/health` - System health check
- `GET /api/llm-config` - Get LLM configuration
- `POST /api/llm-config` - Update LLM configuration

### Agent Testing
- `POST /api/diary/generate` - Test diary agent
- `POST /api/sensor/translate` - Test sensor agent
- `POST /api/bazi_wuxing/calc` - Test BaZi agent
- `POST /api/event/extract` - Test event extraction
- `POST /api/event/update` - Test event update
- `POST /api/event/pipeline` - Test event pipeline

### Prompt Management
- `GET /api/prompts/templates` - Get prompt templates
- `POST /api/prompts/update` - Update prompt template

### Custom Testing
- `POST /api/test/custom` - Run custom test with prompt configuration

## 🎨 Customization

### Styling
- Modify `src/style.css` for global styles
- Use Element Plus theme customization
- Add custom CSS classes for specific components

### Components
- Extend existing components in `src/views/`
- Add new components in `src/components/`
- Modify API service in `src/services/apiService.js`

### State Management
- Update global state in `src/stores/appStore.js`
- Add new stores for specific features
- Use Pinia for reactive state management

## 🚀 Deployment

### Development Build
```bash
npm run build
```

### Production Deployment
1. Build the project: `npm run build`
2. Deploy the `dist/` folder to your web server
3. Configure reverse proxy for API calls
4. Set up HTTPS for production use

### Docker Deployment
```dockerfile
FROM node:16-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🧪 Testing

### Unit Tests
```bash
npm run test
```

### E2E Tests
```bash
npm run test:e2e
```

### Manual Testing Checklist
- [ ] All agents can be tested successfully
- [ ] LLM providers can be configured and tested
- [ ] Prompts can be edited and tested
- [ ] Error handling works correctly
- [ ] Responsive design works on all devices
- [ ] Real-time status updates function properly

## 🐛 Troubleshooting

### Common Issues

1. **Connection Failed**
   - Ensure backend is running on port 5000
   - Check proxy configuration in `vite.config.js`
   - Verify API endpoints are accessible

2. **LLM Provider Errors**
   - Check API keys in LLM configuration
   - Verify provider endpoints are correct
   - Test individual providers using the test button

3. **Prompt Testing Fails**
   - Validate JSON format in prompt configuration
   - Check validation rules are properly formatted
   - Ensure test data matches expected format

4. **Build Issues**
   - Clear node_modules and reinstall dependencies
   - Check Node.js version compatibility
   - Verify all required dependencies are installed

### Debug Mode
Enable debug mode by adding to your browser console:
```javascript
localStorage.setItem('debug', 'true')
```

## 📚 Additional Resources

- [Vue 3 Documentation](https://vuejs.org/)
- [Element Plus Components](https://element-plus.org/)
- [Pinia State Management](https://pinia.vuejs.org/)
- [Vite Build Tool](https://vitejs.dev/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the troubleshooting section
- Review the API documentation
- Create an issue in the repository
- Contact the development team

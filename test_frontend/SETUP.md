# CorePlay Agent Test Frontend Setup Script

This script helps you set up and run the CorePlay Agent Test Frontend.

## Quick Start

```bash
# 1. Navigate to the frontend directory
cd test_frontend

# 2. Install dependencies
npm install

# 3. Start the development server
npm run dev

# 4. Open your browser to http://localhost:3000
```

## Prerequisites

- Node.js 16+ installed
- CorePlay Agent backend running on port 5000
- npm or yarn package manager

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run serve` - Serve production build

## Configuration

The frontend is configured to connect to the backend API at `http://localhost:5000`. 
If your backend runs on a different port, update the proxy configuration in `vite.config.js`.

## Features

✅ **Multi-Agent Testing** - Test all CorePlay agents
✅ **LLM Configuration** - Manage LLM providers and settings  
✅ **Prompt Editor** - Edit and test prompts live
✅ **Real-time Testing** - Test configurations against actual backend
✅ **Responsive Design** - Works on all devices
✅ **Status Monitoring** - Live system health indicators

## Troubleshooting

If you encounter issues:

1. **Port conflicts**: Ensure ports 3000 and 5000 are available
2. **API connection**: Verify backend is running and accessible
3. **Dependencies**: Try deleting `node_modules` and running `npm install` again
4. **Browser cache**: Clear browser cache and reload

## Support

For issues and questions, check the main README.md file or create an issue in the repository.

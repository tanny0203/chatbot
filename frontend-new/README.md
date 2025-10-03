# ChatBot Frontend# React + TypeScript + Vite



A clean, modern React TypeScript frontend for the ChatBot application with a ChatGPT-like UI design.This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.



## FeaturesCurrently, two official plugins are available:



- 🔐 **Authentication**: Login and Register pages with clean design- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh

- 💬 **Chat Interface**: ChatGPT-like messaging interface- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

- 📱 **Responsive Design**: Works on desktop and mobile devices

- 🎨 **Clean UI**: Minimal, professional design without funky colors## React Compiler

- 📂 **File Upload**: Support for file uploads in chats

- 🔄 **Real-time Chat**: Seamless messaging experienceThe React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).



## Tech Stack## Expanding the ESLint configuration



- **React 18** with TypeScriptIf you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

- **Vite** for fast development and building

- **React Router** for navigation```js

- **Axios** for API communicationexport default defineConfig([

- **Lucide React** for clean, consistent icons  globalIgnores(['dist']),

  {

## API Integration    files: ['**/*.{ts,tsx}'],

    extends: [

The frontend is designed to work with your Go backend and includes:      // Other configs...



### Authentication Endpoints      // Remove tseslint.configs.recommended and replace with this

- `POST /auth/register` - User registration      tseslint.configs.recommendedTypeChecked,

- `POST /auth/login` - User login      // Alternatively, use this for stricter rules

- `GET /auth/me` - Get current user info      tseslint.configs.strictTypeChecked,

      // Optionally, add this for stylistic rules

### Chat Endpoints      tseslint.configs.stylisticTypeChecked,

- `GET /chats` - Get user's chats

- `POST /chats` - Create new chat      // Other configs...

- `GET /chats/:id` - Get messages for a chat    ],

- `POST /chats/:id/messages` - Send message    languageOptions: {

- `GET /chats/:id/files` - Get files for a chat      parserOptions: {

- `POST /chats/:id/files` - Upload file to chat        project: ['./tsconfig.node.json', './tsconfig.app.json'],

        tsconfigRootDir: import.meta.dirname,

## Getting Started      },

      // other options...

### Prerequisites    },

  },

- Node.js 20.19+ or 22.12+ (you need to upgrade from 20.18.1)])

- npm or yarn```

- Go backend running on `http://localhost:8080`

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

### Installation

```js

1. Install dependencies:// eslint.config.js

   ```bashimport reactX from 'eslint-plugin-react-x'

   npm installimport reactDom from 'eslint-plugin-react-dom'

   ```

export default defineConfig([

2. Start the development server:  globalIgnores(['dist']),

   ```bash  {

   npm run dev    files: ['**/*.{ts,tsx}'],

   ```    extends: [

      // Other configs...

3. Open [http://localhost:5173](http://localhost:5173) in your browser      // Enable lint rules for React

      reactX.configs['recommended-typescript'],

### Building for Production      // Enable lint rules for React DOM

      reactDom.configs.recommended,

```bash    ],

npm run build    languageOptions: {

```      parserOptions: {

        project: ['./tsconfig.node.json', './tsconfig.app.json'],

The built files will be in the `dist` directory.        tsconfigRootDir: import.meta.dirname,

      },

## Project Structure      // other options...

    },

```  },

src/])

├── components/          # React components```

│   ├── Auth.css        # Authentication styles
│   ├── ChatSidebar.tsx # Chat list sidebar
│   ├── ChatWindow.tsx  # Main chat interface
│   ├── Dashboard.tsx   # Main dashboard layout
│   ├── Login.tsx       # Login page
│   ├── Register.tsx    # Registration page
│   └── ProtectedRoute.tsx # Route protection
├── contexts/
│   └── AuthContext.tsx # Authentication context
├── services/
│   └── api.ts          # API service layer
├── types/
│   └── api.ts          # TypeScript type definitions
├── App.tsx             # Main app component
├── App.css             # Main styles
└── main.tsx            # App entry point
```

## Features Overview

### Authentication
- Clean login/register forms with validation
- JWT token handling with HTTP-only cookies
- Automatic redirect based on auth state

### Chat Interface
- Sidebar with chat list and user info
- Real-time messaging interface
- Message history with timestamps
- Typing indicators
- File upload support (UI ready)

### Responsive Design
- Mobile-first approach
- Collapsible sidebar on mobile
- Touch-friendly interactions
- Optimized for various screen sizes

## Configuration

The frontend is configured to connect to:
- Backend API: `http://localhost:8080`
- Frontend dev server: `http://localhost:5173`

To change the API URL, update the `API_BASE_URL` constant in `src/services/api.ts`.

## Notes

1. **Node.js Version**: You need to upgrade to Node.js 20.19+ or 22.12+ to run this project
2. **Backend Integration**: Ensure your Go backend is running and configured with CORS for localhost:5173
3. **Styling**: The UI uses a clean, professional design similar to ChatGPT
4. **Type Safety**: Full TypeScript support with proper type definitions for your Go backend DTOs
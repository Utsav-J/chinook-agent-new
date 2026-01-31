# Chinook Data Speech Agent

<video controls src="AgentDemo.mp4" title="Title"></video>

## Table of Contents
1. [Project Overview](#project-overview)
2. [What This Project Achieves](#what-this-project-achieves)
3. [System Architecture](#system-architecture)
4. [How It Works](#how-it-works)
5. [Backend Implementation](#backend-implementation)
6. [Frontend Capabilities](#frontend-capabilities)
7. [API Documentation](#api-documentation)
8. [Technical Stack](#technical-stack)
9. [Installation and Setup](#installation-and-setup)
10. [Usage Guide](#usage-guide)
11. [Features and Capabilities](#features-and-capabilities)
12. [Security and Safety](#security-and-safety)
13. [Database Schema](#database-schema)
14. [Project Structure](#project-structure)
15. [Future Enhancements](#future-enhancements)

---

## Project Overview

The **Chinook Data Speech Agent** is an intelligent, conversational AI system that enables users to interact with the Chinook SQLite database using natural language queries through both text and voice interfaces. The system combines advanced Large Language Model (LLM) capabilities with SQL query generation, user authentication, and multi-modal interaction (text, speech input, and text-to-speech output) to provide a seamless, personalized data exploration experience.

### Key Innovation

This project demonstrates the integration of:
- **Natural Language Processing (NLP)** for understanding user queries
- **SQL Query Generation** for database interaction
- **User Identity Validation** against database records
- **Conversational Context Management** for multi-turn dialogues
- **Speech Recognition** for voice input
- **Text-to-Speech (TTS)** for audio responses
- **RESTful API Architecture** for frontend-backend separation

---

## What This Project Achieves

### Primary Objectives

1. **Natural Language Database Querying**: Users can ask questions about the Chinook database in plain English (or via voice), and the system automatically generates and executes appropriate SQL queries.

2. **Personalized Data Access**: The system validates user identity against the database and provides personalized responses based on the user's customer record, addressing them by name and tailoring results to their specific data.

3. **Multi-Modal Interaction**: The system supports multiple interaction modes:
   - **Text Input**: Traditional keyboard-based input
   - **Speech Input**: Voice commands using Web Speech API
   - **Text Output**: Displayed responses in the chat interface
   - **Audio Output**: Text-to-speech synthesis for hands-free interaction

4. **Conversational Intelligence**: The agent maintains context across multiple turns of conversation, allowing for follow-up questions and natural dialogue flow.

5. **Safe Database Operations**: The system enforces read-only access to the database, preventing any data modification or schema changes.

6. **Session Management**: Users can create multiple conversation threads, each maintaining its own context and history.

### Real-World Applications

- **Customer Service Portals**: Customers can query their purchase history, invoices, and account information using natural language.
- **Business Intelligence Dashboards**: Non-technical users can explore sales data, artist catalogs, and inventory without writing SQL.
- **Accessibility Solutions**: Voice input and TTS output make the system accessible to users with visual or motor impairments.
- **Educational Tools**: Demonstrates how AI can bridge the gap between natural language and database queries.

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Text Input  │  │ Speech Input │  │  TTS Output  │     │
│  │   (Keyboard) │  │ (Web Speech) │  │ (Speech API) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         React/JavaScript Frontend Application         │  │
│  │  - Chat Interface                                     │  │
│  │  - Thread Management                                  │  │
│  │  - Message History                                    │  │
│  │  - Speech Recognition Integration                     │  │
│  │  - Text-to-Speech Integration                         │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP/REST API
                        │ (JSON)
┌───────────────────────┴─────────────────────────────────────┐
│                    Backend Layer (FastAPI)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              FastAPI REST API Server                  │  │
│  │  - /chat (POST) - Send messages                      │  │
│  │  - /threads (GET/POST/DELETE) - Thread management    │  │
│  │  - /threads/{id}/messages (GET) - Message history    │  │
│  │  - /health (GET) - Health check                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Thread Registry & Session Management        │  │
│  │  - Thread creation and tracking                       │  │
│  │  - Message history storage                            │  │
│  │  - Thread metadata management                         │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                  Agent Layer (LangGraph)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              LangGraph Agent Runtime                   │  │
│  │  - Conversation state management                      │  │
│  │  - Tool orchestration                                 │  │
│  │  - Context preservation                               │  │
│  │  - Checkpointing (InMemorySaver)                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Middleware Stack                          │  │
│  │  1. require_valid_name - Name validation gate         │  │
│  │  2. dynamic_system_prompt - Context-aware prompts     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  LLM Layer (Gemini)                    │  │
│  │  - Google Gemini 2.5 Flash                            │  │
│  │  - Natural language understanding                     │  │
│  │  - SQL query generation                               │  │
│  │  - Response generation                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Tool Layer                          │  │
│  │  - execute_sql: Read-only SQL execution               │  │
│  │  - update_user_name: User context update              │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                    Data Layer                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Chinook SQLite Database                   │  │
│  │  - Customer records                                   │  │
│  │  - Invoice data                                       │  │
│  │  - Artist/Album/Track information                     │  │
│  │  - Sales and purchase history                         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Interactions

1. **Frontend → Backend**: The frontend sends HTTP POST requests to `/chat` endpoint with user messages (text or transcribed speech).

2. **Backend → Agent**: The FastAPI backend invokes the LangGraph agent with the user message, thread ID, and runtime context.

3. **Agent → LLM**: The agent uses middleware to prepare the request and sends it to Google Gemini for processing.

4. **LLM → Tools**: Based on the user's query, the LLM decides which tools to call (e.g., `execute_sql` or `update_user_name`).

5. **Tools → Database**: The `execute_sql` tool executes read-only SQL queries against the Chinook database.

6. **Agent → Backend**: The agent returns the response message, which the backend serializes and sends to the frontend.

7. **Backend → Frontend**: The frontend receives the response, displays it in the chat interface, and optionally uses TTS to speak the response.

---

## How It Works

### Complete User Interaction Flow

#### 1. Initial Setup and Authentication

```
User: "I'm Frank Harris"
     ↓
Frontend: Transcribes speech (if voice input) or sends text
     ↓
Backend: Receives message, creates/updates thread
     ↓
Agent: Middleware checks if name is validated
     ↓
Agent: Since has_valid_name = False, restricts tools to update_user_name only
     ↓
LLM: Calls update_user_name("Frank", "Harris")
     ↓
Tool: Validates name exists in Customer table
     ↓
Tool: Updates RuntimeContext with user name
     ↓
LLM: Generates personalized greeting
     ↓
Backend: Returns response to frontend
     ↓
Frontend: Displays "Hello Frank! How can I help you today?"
     ↓
Frontend: Optionally uses TTS to speak the response
```

#### 2. Data Query Flow

```
User: "What was my most expensive purchase?"
     ↓
Frontend: Sends message with thread_id (maintains context)
     ↓
Backend: Retrieves thread context, sends to agent
     ↓
Agent: Middleware allows SQL queries (has_valid_name = True)
     ↓
LLM: Analyzes query, determines SQL needed
     ↓
LLM: Calls execute_sql("SELECT i.InvoiceId, i.Total FROM Invoice i 
                        JOIN Customer c ON i.CustomerId = c.CustomerId 
                        WHERE c.FirstName = 'Frank' AND c.LastName = 'Harris' 
                        ORDER BY i.Total DESC LIMIT 1;")
     ↓
Tool: Executes query on Chinook database
     ↓
Database: Returns [(145, 13.86)]
     ↓
LLM: Receives results, generates natural language response
     ↓
LLM: "Frank, your most expensive purchase was Invoice ID 145, totaling $13.86."
     ↓
Backend: Returns response with thread_id and timestamp
     ↓
Frontend: Displays response, stores in message history
     ↓
Frontend: Optionally uses TTS to speak the response
```

### Key Mechanisms

#### A. Name Validation Gate

The `require_valid_name` middleware acts as a security gate that:
- Checks if `has_valid_name` is `True` in the runtime context
- If `False`, restricts available tools to only `update_user_name`
- Forces the LLM to collect and validate the user's name before allowing any SQL queries
- Prevents unauthorized data access by ensuring users are validated customers

#### B. Dynamic System Prompt

The `dynamic_system_prompt` middleware:
- Injects current user information (first name, last name) into the system prompt
- Includes available database tables in the prompt
- Personalizes the agent's behavior based on the user context
- Updates the prompt dynamically as the conversation progresses

#### C. Thread-Based Context Management

- Each conversation thread has a unique `thread_id` (UUID)
- The LangGraph agent uses `InMemorySaver` to checkpoint conversation state
- Thread registry tracks metadata (title, creation time, last activity, message count)
- Messages are stored in chronological order for history retrieval

#### D. Speech Recognition Integration

The frontend uses the Web Speech API (`webkitSpeechRecognition` or `SpeechRecognition`):
- Captures audio from the user's microphone
- Converts speech to text in real-time
- Handles recognition events (start, result, end, error)
- Sends transcribed text to the backend API
- Provides visual feedback during recognition (listening indicator)

#### E. Text-to-Speech Integration

The frontend uses the Web Speech API (`speechSynthesis`):
- Converts agent responses to speech
- Supports multiple voice options and languages
- Provides controls for play/pause/stop
- Handles speech synthesis events (start, end, error)
- Allows users to toggle TTS on/off

---

## Backend Implementation

### FastAPI Server (`fastapi_backend.py`)

The backend is built using FastAPI, providing a RESTful API for the frontend to interact with the agent.

#### Key Components

1. **Application Setup**
   - FastAPI app with CORS middleware for cross-origin requests
   - Lifespan management for startup/shutdown
   - Health check endpoints

2. **Thread Registry**
   - In-memory dictionary storing thread metadata
   - Tracks: `created_at`, `last_activity`, `title`, `messages`
   - Provides thread listing, retrieval, and deletion

3. **API Endpoints**

   - **`POST /chat`**: Main endpoint for sending messages
     - Accepts `ChatRequest` with `message` and optional `thread_id`
     - Creates new thread if `thread_id` not provided
     - Invokes LangGraph agent with timeout (30 seconds)
     - Returns `ChatResponse` with agent response and thread metadata

   - **`POST /threads`**: Create a new conversation thread
     - Generates UUID for thread_id if not provided
     - Initializes thread registry entry
     - Returns thread metadata

   - **`GET /threads`**: List all threads with pagination
     - Supports `limit` and `offset` query parameters
     - Sorted by last activity (most recent first)

   - **`GET /threads/{thread_id}`**: Get thread metadata
     - Returns thread information including message count

   - **`GET /threads/{thread_id}/messages`**: Get message history
     - Returns paginated list of messages for a thread
     - Messages in chronological order

   - **`DELETE /threads/{thread_id}`**: Delete a thread
     - Removes thread from registry

   - **`GET /health`**: Health check endpoint
     - Returns service status and agent name

4. **Error Handling**
   - HTTP exception handling with appropriate status codes
   - Timeout handling (504 Gateway Timeout)
   - Validation error handling (400 Bad Request)
   - Generic error handling (500 Internal Server Error)

5. **Message Serialization**
   - Converts LangChain message objects to Pydantic models
   - Handles various message content formats (string, list, dict)
   - Extracts message roles (user, assistant, tool)
   - Adds timestamps to messages

### LangGraph Agent (`agent.py`)

The agent is built using LangGraph, which provides a stateful, graph-based execution model for LLM applications.

#### Key Components

1. **Runtime Context**
   ```python
   @dataclass
   class RuntimeContext:
       db: SQLDatabase
       user_first_name: str
       user_last_name: str
       has_valid_name: bool
   ```
   - Stores database connection and user information
   - Tracks name validation status

2. **Tools**

   - **`execute_sql(query: str)`**
     - Executes read-only SQL SELECT queries
     - Returns query results as structured data
     - Handles SQL errors gracefully
     - Accesses database from runtime context

   - **`update_user_name(new_first_name: str, new_last_name: str)`**
     - Validates name exists in Customer table
     - Updates runtime context with user name
     - Returns `Command` object to update agent state
     - Emits `ToolMessage` for agent acknowledgment

3. **Middleware**

   - **`require_valid_name`**
     - Wraps model calls to enforce name validation
     - Restricts tools when `has_valid_name = False`
     - Provides clear instructions to LLM for name collection

   - **`dynamic_system_prompt`**
     - Generates context-aware system prompts
     - Includes available tables and user information
     - Updates prompt based on runtime context

4. **Agent Configuration**
   - Model: Google Gemini 2.5 Flash
   - Checkpointer: InMemorySaver (for conversation state)
   - Tools: `execute_sql`, `update_user_name`
   - Middleware: `require_valid_name`, `dynamic_system_prompt`

### Database Utilities (`utils/sql_utils.py`)

1. **Database Connection**
   - Uses `langchain_community.utilities.SQLDatabase`
   - Connects to SQLite database at `Chinook.db`
   - Provides database handle to agent

2. **Helper Functions**
   - `get_db()`: Returns database connection
   - `get_usable_tables()`: Lists available tables
   - `customer_exists(first_name, last_name)`: Validates customer name

### Prompt Engineering (`utils/prompts.py`)

The system uses carefully crafted prompts to guide the LLM's behavior:

1. **System Prompt Template**
   - Defines agent role and capabilities
   - Lists available tools and their usage
   - Provides database context (available tables)
   - Includes user context (name personalization)
   - Specifies behavior guidelines and restrictions
   - Includes example interactions

2. **Tool Descriptions**
   - Detailed descriptions for each tool
   - Parameter specifications
   - Return value formats
   - Usage examples

---

## Frontend Capabilities

### Speech Input (Speech Recognition)

The frontend implements speech recognition using the **Web Speech API**, specifically the `SpeechRecognition` interface (or `webkitSpeechRecognition` for Chrome).

#### Implementation Details

1. **Initialization**
   ```javascript
   const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
   recognition.continuous = false;  // Single utterance mode
   recognition.interimResults = false;  // Only final results
   recognition.lang = 'en-US';  // Language setting
   ```

2. **Event Handlers**
   - **`onstart`**: Indicates recognition has started (show listening indicator)
   - **`onresult`**: Receives recognition results (transcribed text)
   - **`onerror`**: Handles recognition errors (no speech, network error, etc.)
   - **`onend`**: Indicates recognition has ended (hide listening indicator)

3. **User Interaction**
   - Microphone button to start/stop recognition
   - Visual feedback during recognition (animated microphone icon)
   - Display of transcribed text before sending
   - Error handling for microphone permissions

4. **Browser Compatibility**
   - Chrome/Edge: Full support via `webkitSpeechRecognition`
   - Firefox: Limited support (may require polyfill)
   - Safari: Limited support
   - Mobile browsers: Varies by platform

5. **Features**
   - Real-time speech-to-text conversion
   - Automatic punctuation and capitalization
   - Language selection
   - Continuous vs. single utterance modes
   - Confidence scores for recognition results

### Text-to-Speech (TTS) Output

The frontend implements text-to-speech using the **Web Speech API**, specifically the `speechSynthesis` interface.

#### Implementation Details

1. **Initialization**
   ```javascript
   const utterance = new SpeechSynthesisUtterance(text);
   utterance.rate = 1.0;  // Speech rate (0.1 to 10)
   utterance.pitch = 1.0;  // Pitch (0 to 2)
   utterance.volume = 1.0;  // Volume (0 to 1)
   utterance.lang = 'en-US';  // Language
   ```

2. **Voice Selection**
   - Lists available voices from `speechSynthesis.getVoices()`
   - Allows user to select preferred voice
   - Supports multiple languages and accents
   - Defaults to system default voice

3. **Controls**
   - Play/Pause button for TTS
   - Stop button to cancel speech
   - Volume control
   - Rate control (speed adjustment)
   - Voice selection dropdown

4. **Event Handlers**
   - **`onstart`**: Speech synthesis started
   - **`onend`**: Speech synthesis completed
   - **`onerror`**: Error during synthesis
   - **`onpause`**: Speech paused
   - **`onresume`**: Speech resumed

5. **Integration with Chat**
   - Automatically speaks agent responses (if enabled)
   - Respects user preferences (TTS on/off toggle)
   - Handles long responses (may need chunking)
   - Pauses TTS when new message arrives (optional)

6. **Browser Compatibility**
   - Chrome/Edge: Full support
   - Firefox: Full support
   - Safari: Full support
   - Mobile browsers: Generally supported

### User Interface Features

1. **Chat Interface**
   - Message bubbles for user and agent
   - Timestamp display
   - Message history scrolling
   - Loading indicators during agent processing

2. **Thread Management**
   - Sidebar with thread list
   - Create new thread button
   - Thread title display
   - Message count per thread
   - Delete thread functionality

3. **Input Methods**
   - Text input field with send button
   - Microphone button for speech input
   - Keyboard shortcut support (Enter to send)
   - Clear input after sending

4. **Settings/Preferences**
   - TTS enable/disable toggle
   - Voice selection
   - Speech rate adjustment
   - Language selection

---

## API Documentation

### Base URL
```
Development: http://localhost:8080
Production: [Your production URL]
```

### Authentication
Currently, the API does not require authentication. All endpoints are publicly accessible.

### Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` or `/health` | Health check |
| POST | `/chat` | Send message to agent |
| POST | `/threads` | Create new thread |
| GET | `/threads` | List all threads |
| GET | `/threads/{thread_id}` | Get thread metadata |
| GET | `/threads/{thread_id}/messages` | Get message history |
| DELETE | `/threads/{thread_id}` | Delete thread |

### Request/Response Examples

#### Send Chat Message
```http
POST /chat
Content-Type: application/json

{
  "message": "I'm Frank Harris",
  "thread_id": "optional-thread-id"
}
```

**Response:**
```json
{
  "response": "Hello Frank! How can I help you today?",
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "msg-124",
  "timestamp": "2024-01-15T10:30:05.000Z"
}
```

#### Create Thread
```http
POST /threads
Content-Type: application/json

{
  "title": "My Conversation"
}
```

**Response:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-15T10:30:00.000Z",
  "last_activity": "2024-01-15T10:30:00.000Z",
  "title": "My Conversation",
  "message_count": 0
}
```

For complete API documentation, see `API_USAGE.md`.

---

## Technical Stack

### Backend Technologies

- **Python 3.11+**: Core programming language
- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **LangChain**: Framework for building LLM applications
- **LangGraph**: Stateful, graph-based agent orchestration
- **Google Gemini 2.5 Flash**: Large Language Model for NLP
- **SQLAlchemy**: SQL toolkit and ORM (via LangChain)
- **SQLite**: Lightweight database (Chinook.db)
- **Pydantic**: Data validation using Python type annotations
- **python-dotenv**: Environment variable management

### Frontend Technologies

- **HTML5**: Markup language
- **CSS3**: Styling
- **JavaScript (ES6+)**: Client-side programming
- **Web Speech API**: Speech recognition and synthesis
- **Fetch API**: HTTP requests to backend
- **React** (optional): If using React frontend framework

### Development Tools

- **uv**: Python package manager (alternative to pip)
- **pyproject.toml**: Project configuration and dependencies
- **.env**: Environment variables (API keys, configuration)

### Dependencies

```toml
[project]
dependencies = [
    "langchain>=1.0.3",
    "langchain-community>=0.4.1",
    "langchain-google-genai>=3.0.0",
    "pyprojroot>=0.3.0",
    "fastapi[standard]>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "python-dotenv>=1.0.0",
]
```

---

## Installation and Setup

### Prerequisites

1. **Python 3.11 or higher**
   ```bash
   python --version
   ```

2. **uv package manager** (or pip)
   ```bash
   # Install uv
   pip install uv
   ```

3. **Chinook.db database file**
   - Place `Chinook.db` in the project root directory
   - Download from: https://github.com/lerocha/chinook-database

4. **Google Generative AI API Key**
   - Obtain from: https://makersuite.google.com/app/apikey
   - Create a `.env` file in the project root

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chinook-data-speech-agent
   ```

2. **Create virtual environment** (if using uv)
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   uv pip install -e .
   # Or using pip:
   pip install -e .
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_api_key_here
   ```

5. **Verify database file**
   Ensure `Chinook.db` is in the project root directory.

### Running the Backend

1. **Start the FastAPI server**
   ```bash
   python fastapi_backend.py
   # Or using uvicorn directly:
   uvicorn fastapi_backend:app --host 0.0.0.0 --port 8080 --reload
   ```

2. **Verify server is running**
   ```bash
   curl http://localhost:8080/health
   # Should return: {"status":"healthy","agent_name":"sql_agent"}
   ```

3. **Access API documentation**
   - Swagger UI: http://localhost:8080/docs
   - ReDoc: http://localhost:8080/redoc

### Running the Frontend

1. **Serve the frontend files**
   - If using a simple HTML/JS frontend, serve using a local web server:
     ```bash
     # Using Python's HTTP server
     python -m http.server 3000
     
     # Or using Node.js http-server
     npx http-server -p 3000
     ```

2. **Open in browser**
   - Navigate to: http://localhost:3000
   - Ensure microphone permissions are granted for speech recognition

### Testing the CLI Agent (Optional)

Run the agent directly from the command line:
```bash
python agent.py
```

Type your questions and press Enter. Type `exit` to quit.

---

## Usage Guide

### Basic Usage

1. **Start a conversation**
   - Open the frontend application
   - Click "New Conversation" or start typing/speaking

2. **Provide your name**
   - Type or say: "I'm Frank Harris" (or any valid customer name)
   - The agent will validate your name and greet you

3. **Ask questions**
   - Text input: Type your question and press Enter
   - Voice input: Click the microphone button and speak your question
   - Examples:
     - "What was my most expensive purchase?"
     - "Show me all albums by AC/DC"
     - "What's my total spending?"

4. **Listen to responses** (if TTS enabled)
   - Agent responses are automatically spoken
   - Use controls to pause, stop, or adjust volume

### Advanced Usage

1. **Thread Management**
   - Create multiple conversation threads
   - Switch between threads to maintain separate contexts
   - Delete threads when no longer needed

2. **Message History**
   - View past messages in a thread
   - Scroll through conversation history
   - Reference previous queries and responses

3. **Speech Settings**
   - Adjust TTS voice, rate, and volume
   - Enable/disable automatic TTS
   - Select preferred language

### Example Conversations

#### Conversation 1: Customer Purchase History
```
User: I'm Frank Harris
Agent: Hello Frank! How can I help you today?

User: What was my cheapest purchase?
Agent: Frank, your most inexpensive purchase was Invoice ID 13, totaling $0.99.

User: What about the most expensive?
Agent: Frank, your most expensive purchase was Invoice ID 145, totaling $13.86.

User: Show me all my invoices
Agent: [Executes SQL query and returns list of invoices]
```

#### Conversation 2: Music Catalog Query
```
User: I'm Steve Murray
Agent: Hello Steve! How can I help you today?

User: List all albums by AC/DC
Agent: AC/DC has 2 albums in the database: Let There Be Rock and For Those About To Rock We Salute You.

User: What tracks are on Let There Be Rock?
Agent: [Lists all tracks on the album]
```

---

## Features and Capabilities

### Core Features

1. **Natural Language Understanding**
   - Interprets user queries in plain English
   - Handles ambiguous questions with clarifying prompts
   - Understands context from previous messages

2. **SQL Query Generation**
   - Automatically generates SQL queries from natural language
   - Optimizes queries for performance
   - Handles complex joins and aggregations

3. **User Authentication**
   - Validates user identity against database
   - Personalizes responses based on user data
   - Maintains user context throughout conversation

4. **Conversation Management**
   - Maintains context across multiple turns
   - Supports follow-up questions
   - Thread-based session management

5. **Error Handling**
   - Graceful handling of SQL errors
   - User-friendly error messages
   - Timeout protection (30 seconds)

6. **Security**
   - Read-only database access
   - Input validation
   - SQL injection prevention (via parameterized queries in LangChain)

### Speech Features

1. **Speech Recognition**
   - Real-time speech-to-text conversion
   - Multiple language support
   - Error handling for recognition failures
   - Visual feedback during recognition

2. **Text-to-Speech**
   - Natural-sounding voice synthesis
   - Multiple voice options
   - Adjustable rate, pitch, and volume
   - Automatic speech for agent responses

### User Experience Features

1. **Responsive Design**
   - Works on desktop and mobile devices
   - Adaptive layout for different screen sizes

2. **Accessibility**
   - Voice input for users with motor impairments
   - TTS output for users with visual impairments
   - Keyboard navigation support

3. **Performance**
   - Fast response times
   - Efficient database queries
   - Optimized API calls

---

## Security and Safety

### Database Security

1. **Read-Only Access**
   - Only SELECT statements are allowed
   - No INSERT, UPDATE, DELETE, or DROP operations
   - Enforced at the tool level

2. **SQL Injection Prevention**
   - LangChain's SQLDatabase uses parameterized queries
   - Input validation and sanitization
   - No direct string concatenation in SQL

3. **User Validation**
   - Names must exist in the Customer table
   - Prevents unauthorized data access
   - Enforced by middleware gate

### API Security

1. **Input Validation**
   - Pydantic models validate all inputs
   - Type checking and constraint validation
   - Error messages for invalid inputs

2. **Timeout Protection**
   - 30-second timeout on agent requests
   - Prevents resource exhaustion
   - Returns 504 Gateway Timeout on timeout

3. **Error Handling**
   - Generic error messages to prevent information leakage
   - Detailed logging for debugging (server-side only)
   - Graceful degradation on errors

### Frontend Security

1. **CORS Configuration**
   - Configurable CORS settings
   - Restrict origins in production
   - Secure credential handling

2. **Microphone Permissions**
   - Browser-level permission requests
   - User consent required for speech recognition
   - Graceful fallback if permissions denied

---

## Database Schema

The Chinook database is a sample database representing a digital media store. Key tables include:

### Core Tables

- **Customer**: Customer information (FirstName, LastName, Email, etc.)
- **Invoice**: Purchase invoices (InvoiceId, CustomerId, Total, InvoiceDate, etc.)
- **InvoiceLine**: Line items for invoices (InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity)
- **Track**: Music tracks (TrackId, Name, AlbumId, MediaTypeId, etc.)
- **Album**: Music albums (AlbumId, Title, ArtistId)
- **Artist**: Music artists (ArtistId, Name)
- **Genre**: Music genres (GenreId, Name)
- **MediaType**: Media types (MediaTypeId, Name)
- **Playlist**: User playlists (PlaylistId, Name)
- **PlaylistTrack**: Playlist-track associations

### Relationships

- Customer → Invoice (one-to-many)
- Invoice → InvoiceLine (one-to-many)
- InvoiceLine → Track (many-to-one)
- Track → Album (many-to-one)
- Album → Artist (many-to-one)
- Track → Genre (many-to-one)
- Track → MediaType (many-to-one)
- Playlist → PlaylistTrack (one-to-many)
- PlaylistTrack → Track (many-to-one)

### Sample Queries Supported

- Customer purchase history
- Sales by country/artist/genre
- Album and track listings
- Playlist information
- Revenue analytics
- Customer demographics

---

## Project Structure

```
chinook-data-speech-agent/
│
├── agent.py                 # LangGraph agent implementation
├── fastapi_backend.py       # FastAPI REST API server
├── Chinook.db              # SQLite database file
├── pyproject.toml          # Project dependencies and configuration
├── README.md               # This file
├── API_USAGE.md            # Detailed API documentation
├── .env                    # Environment variables (not in repo)
│
├── utils/
│   ├── __init__.py
│   ├── prompts.py          # System prompts and tool descriptions
│   └── sql_utils.py        # Database utilities and helpers
│
├── frontend/               # Frontend application (if separate)
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── ...
│
└── __pycache__/           # Python cache files (gitignored)
```

### File Descriptions

- **`agent.py`**: Core agent logic, tools, middleware, and LangGraph configuration
- **`fastapi_backend.py`**: FastAPI application with REST endpoints and thread management
- **`utils/prompts.py`**: System prompts and tool descriptions for the LLM
- **`utils/sql_utils.py`**: Database connection and utility functions
- **`pyproject.toml`**: Project metadata and dependencies
- **`API_USAGE.md`**: Complete API reference documentation

---

## Future Enhancements

### Potential Improvements

1. **Enhanced Speech Recognition**
   - Support for multiple languages
   - Offline speech recognition
   - Improved accuracy with custom models
   - Noise cancellation

2. **Advanced TTS**
   - More natural voice synthesis
   - Emotion and tone variation
   - Multiple voice options
   - SSML support for advanced formatting

3. **Database Features**
   - Support for multiple databases
   - Database schema exploration UI
   - Query optimization suggestions
   - Query history and favorites

4. **User Features**
   - User accounts and authentication
   - Saved queries and bookmarks
   - Export results to CSV/JSON
   - Visualization of query results

5. **Agent Improvements**
   - Multi-step reasoning
   - Query explanation and learning
   - Suggestion of related queries
   - Conversation summarization

6. **Performance**
   - Response caching
   - Query result caching
   - Streaming responses
   - WebSocket support for real-time updates

7. **Security**
   - User authentication and authorization
   - Rate limiting
   - API key management
   - Audit logging

8. **Deployment**
   - Docker containerization
   - Cloud deployment (AWS, GCP, Azure)
   - CI/CD pipeline
   - Monitoring and logging

---

## Conclusion

The Chinook Data Speech Agent demonstrates a complete integration of modern AI technologies (LLMs, speech recognition, TTS) with traditional database systems, creating an intuitive and accessible interface for data exploration. The system's architecture is scalable, maintainable, and extensible, making it suitable for both educational purposes and real-world applications.

### Key Achievements

- ✅ Natural language to SQL conversion
- ✅ User authentication and personalization
- ✅ Multi-modal interaction (text, speech input, TTS output)
- ✅ Conversational context management
- ✅ Secure, read-only database access
- ✅ RESTful API architecture
- ✅ Comprehensive error handling
- ✅ Thread-based session management

### Learning Outcomes

This project showcases:
- Integration of LLMs with databases
- Agent orchestration using LangGraph
- RESTful API design with FastAPI
- Web Speech API integration
- Prompt engineering techniques
- Security best practices
- User experience design for accessibility

---

## License

[Specify your license here]

## Author

[Your name/team name]

## Acknowledgments

- Chinook Database: Sample database for SQLite
- LangChain: LLM application framework
- Google Gemini: Large Language Model
- FastAPI: Modern web framework
- Web Speech API: Browser speech recognition and synthesis

---

**Last Updated**: 2024-01-15  
**Version**: 1.0.0

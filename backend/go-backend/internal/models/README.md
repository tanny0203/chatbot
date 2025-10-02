# Database Models

This directory contains the PostgreSQL database models for the NL2SQL Data Chatbot application.

## Models Overview

### 1. User Model (`user.go`)
Represents application users with authentication information.

```go
type User struct {
    ID           uuid.UUID `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
    Email        string    `gorm:"uniqueIndex;not null;size:255"`
    PasswordHash string    `gorm:"column:password_hash;not null"`
    Name         *string   `gorm:"size:255"`
    CreatedAt    time.Time `gorm:"autoCreateTime"`
    
    // Relationships
    Chats    []Chat    `gorm:"foreignKey:UserID"`
    Files    []File    `gorm:"foreignKey:UserID"`
    Messages []Message `gorm:"foreignKey:UserID"`
}
```

### 2. Chat Model (`chat.go`)
Represents independent chat sessions for each user.

```go
type Chat struct {
    ID        uuid.UUID `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
    UserID    uuid.UUID `gorm:"type:uuid;not null;index"`
    Title     *string   `gorm:"size:255"`
    CreatedAt time.Time `gorm:"autoCreateTime"`
    UpdatedAt time.Time `gorm:"autoUpdateTime"`
    
    // Relationships
    User     User      `gorm:"foreignKey:UserID;references:ID;constraint:OnDelete:CASCADE"`
    Files    []File    `gorm:"foreignKey:ChatID;constraint:OnDelete:CASCADE"`
    Messages []Message `gorm:"foreignKey:ChatID;constraint:OnDelete:CASCADE"`
}
```

### 3. File Model (`file.go`)
Represents uploaded CSV/XLSX datasets associated with chats.

```go
type File struct {
    ID          uuid.UUID `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
    ChatID      uuid.UUID `gorm:"type:uuid;not null;index"`
    UserID      uuid.UUID `gorm:"type:uuid;not null;index"`
    Filename    string    `gorm:"not null;size:255"`
    StoragePath string    `gorm:"column:storage_path;not null"`
    TableName   string    `gorm:"column:table_name;not null;size:255"`
    CreatedAt   time.Time `gorm:"autoCreateTime"`
    
    // Relationships
    User User `gorm:"foreignKey:UserID;references:ID;constraint:OnDelete:CASCADE"`
    Chat Chat `gorm:"foreignKey:ChatID;references:ID;constraint:OnDelete:CASCADE"`
}
```

### 4. Message Model (`message.go`)
Represents conversation messages between users and the AI assistant.

```go
type Message struct {
    ID        uuid.UUID      `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
    ChatID    uuid.UUID      `gorm:"type:uuid;not null;index"`
    UserID    uuid.UUID      `gorm:"type:uuid;not null;index"`
    Role      MessageRole    `gorm:"type:text;check:role IN ('user','assistant');not null"`
    Content   MessageContent `gorm:"type:jsonb;not null"`
    CreatedAt time.Time      `gorm:"autoCreateTime"`
    
    // Relationships
    User User `gorm:"foreignKey:UserID;references:ID;constraint:OnDelete:CASCADE"`
    Chat Chat `gorm:"foreignKey:ChatID;references:ID;constraint:OnDelete:CASCADE"`
}
```

The `MessageContent` is a flexible JSONB structure that supports different content types:
- `text`: Plain text messages
- `table`: Tabular data results
- `chart`: Chart/visualization data
- `file`: File references

## Database Schema

The models create the following PostgreSQL tables:

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Chats table
CREATE TABLE chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Files table
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    table_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT CHECK (role IN ('user','assistant')),
    content JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);
```

## Usage

### Import the models
```go
import "go-backend/internal/models"
```

### Using with GORM
```go
// Initialize PostgreSQL with GORM
db.InitPostgreSQL()

// Create a new user
user := models.User{
    Email:        "user@example.com",
    PasswordHash: "hashed_password",
    Name:         &name,
}
result := db.GormDB.Create(&user)

// Create a new chat
chat := models.Chat{
    UserID: user.ID,
    Title:  &title,
}
db.GormDB.Create(&chat)

// Query with relationships
var userWithChats models.User
db.GormDB.Preload("Chats").First(&userWithChats, user.ID)
```

### Running Migrations
```go
import "go-backend/internal/migrate"

// Auto-migrate all models
err := migrate.AutoMigrate(db.GormDB)
```

## Environment Variables

When using PostgreSQL, set these environment variables:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=chatbot
DB_SSLMODE=disable
```

## Features

- **UUID Primary Keys**: All models use UUID for better scalability
- **Cascade Deletes**: Proper foreign key constraints with cascade deletes
- **JSONB Support**: Flexible message content storage
- **Timestamps**: Automatic creation and update timestamps
- **Relationships**: Proper GORM relationships between models
- **Validation**: Database-level constraints and checks
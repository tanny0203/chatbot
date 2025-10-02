package chat

import (
	"time"

	"go-backend/internal/file"
	"go-backend/internal/message"

	"github.com/google/uuid"
)

type chatResponseDTO struct {
	ID        uuid.UUID                    `json:"id"`
	Title     string                       `json:"title"`
	CreatedAt time.Time                    `json:"created_at"`
	UpdatedAt time.Time                    `json:"updated_at"`
	Messages  []message.MessageResponseDTO `json:"messages"`
	Files     []file.FileResponseDTO       `json:"files"`
}

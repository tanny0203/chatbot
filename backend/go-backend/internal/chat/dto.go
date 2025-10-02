package chat

import (
	"time"

	"github.com/google/uuid"
	"go-backend/internal/message"
)


type chatDTO struct {
	ID        uuid.UUID    `json:"id"`
	Title     string       `json:"title"`
	CreatedAt time.Time          `json:"created_at"`
	UpdatedAt time.Time          `json:"updated_at"`
	Messages  []message.MessageDTO `json:"messages"`
}
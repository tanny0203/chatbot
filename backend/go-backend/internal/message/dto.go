package message

import (
	"time"

	"github.com/google/uuid"
)

type MessageResponseDTO struct {
	ID        uuid.UUID `json:"id"`
	Role      string    `json:"role"`
	Content   string    `json:"content"`
	CreatedAt time.Time `json:"created_at"`
}

package models

import (
	"time"

	"github.com/google/uuid"
)

// MessageRole defines the role of the message sender (user or assistant)
type MessageRole string

const (
	MessageRoleUser      MessageRole = "user"
	MessageRoleAssistant MessageRole = "assistant"
)

type Message struct {
	ID        uuid.UUID   `gorm:"type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	ChatID    uuid.UUID   `gorm:"type:uuid;not null;index" json:"chat_id"`
	UserID    uuid.UUID   `gorm:"type:uuid;not null;index" json:"user_id"`
	Role      MessageRole `gorm:"type:text;check:role IN ('user','assistant');not null" json:"role"`
	Content   string      `gorm:"type:text;not null" json:"content"`
	CreatedAt time.Time   `gorm:"autoCreateTime" json:"created_at"`

	// Relationships
	User User `gorm:"foreignKey:UserID;references:ID;constraint:OnDelete:CASCADE" json:"user,omitempty"`
	Chat Chat `gorm:"foreignKey:ChatID;references:ID;constraint:OnDelete:CASCADE" json:"chat,omitempty"`
}

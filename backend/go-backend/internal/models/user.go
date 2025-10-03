package models

import (
	"time"

	"github.com/google/uuid"
)

type User struct {
	ID           uuid.UUID `gorm:"type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	Email        string    `gorm:"uniqueIndex;not null;size:255" json:"email"`
	PasswordHash string    `gorm:"column:password_hash;not null" json:"-"`
	Name         string   `gorm:"size:255" json:"name,omitempty"`
	CreatedAt    time.Time `gorm:"autoCreateTime" json:"created_at"`

	// Relationships
	Chats    []Chat    `gorm:"foreignKey:UserID" json:"chats,omitempty"`
	Files    []File    `gorm:"foreignKey:UserID" json:"files,omitempty"`
	Messages []Message `gorm:"foreignKey:UserID" json:"messages,omitempty"`
}

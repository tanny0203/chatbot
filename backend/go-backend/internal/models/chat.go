package models

import (
	"time"

	"github.com/google/uuid"
)

type Chat struct {
	ID        uuid.UUID `gorm:"type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	UserID    uuid.UUID `gorm:"type:uuid;not null;index" json:"user_id"`
	Title     string   `gorm:"size:255" json:"title,omitempty"`
	CreatedAt time.Time `gorm:"autoCreateTime" json:"created_at"`
	UpdatedAt time.Time `gorm:"autoUpdateTime" json:"updated_at"`

	// Relationships
	User     User      `gorm:"foreignKey:UserID;references:ID;constraint:OnDelete:CASCADE" json:"user,omitempty"`
	Files    []File    `gorm:"foreignKey:ChatID;constraint:OnDelete:CASCADE" json:"files,omitempty"`
	Messages []Message `gorm:"foreignKey:ChatID;constraint:OnDelete:CASCADE" json:"messages,omitempty"`
}

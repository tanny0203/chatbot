package models

import (
	"time"

	"github.com/google/uuid"
)

type File struct {
	ID          uuid.UUID `gorm:"type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	ChatID      uuid.UUID `gorm:"type:uuid;not null;index" json:"chat_id"`
	UserID      uuid.UUID `gorm:"type:uuid;not null;index" json:"user_id"`
	Filename    string    `gorm:"not null;size:255" json:"filename"`
	TableName   string    `gorm:"column:table_name;not null;size:255" json:"table_name"`
	CreatedAt   time.Time `gorm:"autoCreateTime" json:"created_at"`

	// Relationships
	User User `gorm:"foreignKey:UserID;references:ID;constraint:OnDelete:CASCADE" json:"user,omitempty"`
	Chat Chat `gorm:"foreignKey:ChatID;references:ID;constraint:OnDelete:CASCADE" json:"chat,omitempty"`
}

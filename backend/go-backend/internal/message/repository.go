package message

import (
	"go-backend/internal/models"
	"gorm.io/gorm"
)

type Repository struct {
	DB *gorm.DB
}


func NewRepo(db *gorm.DB) *Repository {
	return &Repository{DB: db}
}

func (r *Repository) CreateMessage(message *models.Message) error {
	return r.DB.Create(message).Error
}
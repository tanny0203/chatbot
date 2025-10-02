package chat

import (
	"go-backend/internal/models"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

type Repository struct {
	DB *gorm.DB
}


func NewRepo(db *gorm.DB) *Repository {
	return &Repository{DB: db}
}

func (r *Repository) CreateChat(chat *models.Chat) error {
	return r.DB.Create(chat).Error
}

func (r *Repository) ListAllByUserID(userID uuid.UUID) ([]models.Chat, error) {
	var chats []models.Chat
	if err := r.DB.Where("user_id = ?", userID).Find(&chats).Error; err != nil {
		return nil, err
	}
	return chats, nil
}

func (r *Repository) GetByID(id uuid.UUID) (*models.Chat, error) {
	var chat models.Chat
	if err := r.DB.Preload("Messages").Preload("Files").First(&chat, "id = ?", id).Error; err != nil {
		return nil, err
	}
	return &chat, nil
}

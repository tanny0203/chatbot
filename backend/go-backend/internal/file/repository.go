package file

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

func (r *Repository) CreateFile(file *models.File) error {
	if err := r.DB.Create(file).Error; err != nil {
		return err
	}
	return nil
}

func (r *Repository) ListAllByChatID(chatID uuid.UUID) ([]models.File, error) {
	var files []models.File
	if err := r.DB.Where("chat_id = ?", chatID).Find(&files).Error; err != nil {
		return nil, err
	}
	return files, nil
}


func (r *Repository) GetMetadata(fileID uuid.UUID) (*models.ColumnMetadata, error) {
	var metadata models.ColumnMetadata
	if err := r.DB.Where("file_id = ?", fileID).First(&metadata).Error; err != nil {
		return nil, err
	}
	return &metadata, nil
}
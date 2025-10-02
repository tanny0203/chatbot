package file

import (
	"go-backend/internal/models"

	"github.com/google/uuid"
)

type Service struct {
	repo *Repository
}

func NewService(r *Repository) *Service {
	return &Service{repo: r}
}

func (s *Service) CreateFile(file *models.File) error {
	if err := s.repo.CreateFile(file); err != nil {
		return err
	}
	return nil
}

func (s *Service) CreateTableForFileUpload(chatID, userID uuid.UUID, fileName, tableName string, headers []string, data [][]string) (*models.File, error) {
	finalTableName := chatID.String() + "_" + tableName
	file := &models.File{
		ID:        uuid.New(),
		ChatID:    chatID,
		UserID:    userID,
		Filename:  fileName,
		TableName: finalTableName,
	}
	if err := s.repo.CreateTableForFileUpload(finalTableName, headers, data, file); err != nil {
		return nil, err
	}

	return file, nil
}

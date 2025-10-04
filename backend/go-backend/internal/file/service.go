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



func (s *Service) GetFilesByChat(chatID uuid.UUID) ([]models.File, error) {
	return s.repo.ListAllByChatID(chatID)
}

func (s *Service) GetMetadataByFileID(fileID uuid.UUID) (*models.ColumnMetadata, error) {
	return s.repo.GetMetadata(fileID)
}
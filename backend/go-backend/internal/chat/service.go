package chat

import (
	"fmt"
	"go-backend/internal/file"
	"go-backend/internal/models"
	"go-backend/internal/utils"
	"io"
	"path/filepath"
	"strings"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

type Service struct {
	repo *Repository
}

func NewService(r *Repository) *Service {
	return &Service{repo: r}
}

func (s *Service) CreateChat(userID uuid.UUID, title string) (*models.Chat, error) {
	chat := &models.Chat{
		ID:     uuid.New(),
		UserID: userID,
		Title:  title,
	}
	return chat, s.repo.CreateChat(chat)
}

func (s *Service) GetChatsByUser(userID uuid.UUID) ([]models.Chat, error) {
	return s.repo.ListAllByUserID(userID)
}

// Note: Message sending is handled by the Python NL2SQL service.
// The Go backend no longer creates assistant messages.

func (s *Service) GetChatByID(chatID uuid.UUID) (*models.Chat, error) {
	return s.repo.GetByID(chatID)
}

func (s *Service) HandleFileUpload(chatID uuid.UUID, userID uuid.UUID, fileName string, fileReader io.Reader, tableDB *gorm.DB) (*models.File, error) {
	var data [][]string
	var headers []string
	var err error

	if strings.HasSuffix(strings.ToLower(fileName), ".csv") {
		data, headers, err = utils.ReadCSV(fileReader)
	} else if strings.HasSuffix(strings.ToLower(fileName), ".xlsx") {
		data, headers, err = utils.ReadXLSX(fileReader)
	} else {
		return nil, fmt.Errorf("unsupported file type")
	}

	if err != nil {
		return nil, err
	}

	tableName := strings.TrimSuffix(fileName, filepath.Ext(fileName))

	// Create table in database
	fileStorageService := file.NewService(file.NewRepo(tableDB))
	fileResponse, err := fileStorageService.CreateTableForFileUpload(chatID, userID, fileName, tableName, headers, data)

	if err != nil {
		return nil, err
	}

	service := file.NewService(file.NewRepo(s.repo.DB))

	if err := service.CreateFile(fileResponse); err != nil {
		return nil, err
	}

	return fileResponse, nil

}

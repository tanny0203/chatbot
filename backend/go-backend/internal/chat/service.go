package chat

import (
	"go-backend/internal/message"
	"go-backend/internal/models"

	"github.com/google/uuid"
)

type Service struct {
	repo *Repository
}


func NewService(r *Repository) *Service {
	return &Service{repo: r}
}

func (s *Service) CreateChat(userID uuid.UUID, title string) (*models.Chat, error) {
	chat := &models.Chat{
		ID:        uuid.New(),
		UserID:    userID,
		Title:     title,
	}
	return chat, s.repo.CreateChat(chat)
}

// func (s *Service) GetChatsByUser(userID string) ([]Chat, error) {
// 	return s.repo.GetChatsByUser(userID)
// }

func (s *Service) SendMessage(chatID uuid.UUID, userID uuid.UUID, content string) (*models.Message, error) {
	messageService := message.NewService((*message.Repository)(s.repo))
	return messageService.SendMessage(chatID, userID, content)
}

func (s *Service) GetChatByID(chatID uuid.UUID) (*models.Chat, error) {
	return s.repo.GetByID(chatID)
}

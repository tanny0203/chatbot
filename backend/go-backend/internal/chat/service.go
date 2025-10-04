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
		ID:     uuid.New(),
		UserID: userID,
		Title:  title,
	}
	return chat, s.repo.CreateChat(chat)
}

func (s *Service) GetChatsByUser(userID uuid.UUID) ([]models.Chat, error) {
	return s.repo.ListAllByUserID(userID)
}

func (s *Service) AddMessageToChat(chatID ,userID uuid.UUID, role models.MessageRole, content string, messageService *message.Service) (*models.Message, error) {
	message := &models.Message{
		ID:      uuid.New(),
		ChatID:  chatID,
		UserID: userID,
		Role:    role,
		Content: content,
	}
	return message, messageService.CreateUserMessage(message)
	
}


func (s *Service) GetChatByID(chatID uuid.UUID) (*models.Chat, error) {
	return s.repo.GetByID(chatID)
}

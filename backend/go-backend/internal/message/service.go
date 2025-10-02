package message

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

func (s *Service) SendMessage(chatID, userID uuid.UUID, content string) (*models.Message, error) {
	message := &models.Message{
		ChatID:  chatID,
		UserID:  userID,
		Role:    models.MessageRoleUser,
		Content: content,
	}
	err := s.repo.CreateMessage(message)
	if err != nil {
		return &models.Message{}, err
	}
	aiContent := CallExternalAIAPI(message.Content)
	aiMessage := &models.Message{
		ID: uuid.New(),
		ChatID:  message.ChatID,
		UserID:  message.UserID,
		Role:    models.MessageRoleAssistant,
		Content: aiContent,
	}
	_ = s.repo.CreateMessage(aiMessage)
	return aiMessage, nil
}

func CallExternalAIAPI(message string) string {
	return "This is a placeholder response from the AI."
}

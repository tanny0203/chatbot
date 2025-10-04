package message

import (
	"go-backend/internal/models"
)

type Service struct {
	repo *Repository
}

func NewService(r *Repository) *Service {
	return &Service{repo: r}
}

// Deprecated: Message creation with assistant responses has been removed.
// The Python FastAPI NL2SQL service is responsible for processing and responding
// to messages. The Go backend retains only storage utilities if needed later.
// Consider implementing explicit "store message" endpoints if persistence in Go
// is required without AI generation.

// CreateUserMessage stores a user-authored message without generating an assistant reply.
func (s *Service) CreateUserMessage(msg *models.Message) error {
	return s.repo.CreateMessage(msg)
}

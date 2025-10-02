package users

import (
	"fmt"
	"go-backend/internal/models"
	"go-backend/internal/utils"

	"github.com/google/uuid"
)

type Service struct {
	repo *Repository
}

func NewService(r *Repository) *Service {
	return &Service{repo: r}
}

func (s *Service) GetUserByID(userID uuid.UUID) (models.User, error) {
	return s.repo.GetByID(userID)
}

func (s *Service) CreateUser(dto *UserRegisterDTO) error {

	password, err := utils.HashPassword(dto.Password)
	if err != nil {
		return err
	}

	user := &models.User{
		Email:        dto.Email,
		PasswordHash: password,
		Name:         &dto.Name,
	}

	return s.repo.Create(user)
}

func (s *Service) AuthenticateUser(dto *UserLoginDTO) (*models.User, error) {
	user, err := s.repo.GetByEmail(dto.Email)
	if err != nil {
		return nil, err
	}

	if err := utils.CheckPasswordHash(dto.Password, user.PasswordHash); err != nil {
		return nil, fmt.Errorf("authentication failed: %w", err)
	}

	return user, nil
}

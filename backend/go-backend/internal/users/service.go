package users

import (
	"errors"
	"fmt"
	"go-backend/internal/models"
	"go-backend/internal/utils"

	"github.com/google/uuid"
)

var (
	ErrUserExists     = errors.New("user already exists")
	ErrUserNotFound   = errors.New("user not found")
	ErrInvalidCredentials = errors.New("invalid credentials")
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

func (s *Service) CreateUser(dto *UserRegisterDTO) (*models.User, error) {

	password, err := utils.HashPassword(dto.Password)
	if err != nil {
		return nil, err
	}

	user := &models.User{
		ID: 	   uuid.New(),
		Email:        dto.Email,
		PasswordHash: password,
		Name:         dto.Name,
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

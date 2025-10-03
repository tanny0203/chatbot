package users

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

func (r *Repository) Create(user *models.User) (*models.User, error) {

	existingUser, err := r.GetByEmail(user.Email)
	if err == nil && existingUser != nil {
		return nil, gorm.ErrDuplicatedKey
	}

	if err != nil && err != gorm.ErrRecordNotFound {
		return nil, err
	}
	return user, r.DB.Create(user).Error
}

func (r *Repository) GetByEmail(email string) (*models.User, error) {
	var user models.User
	if err := r.DB.Where("email = ?", email).First(&user).Error; err != nil {
		return nil, err
	}
	return &user, nil
}
func (r *Repository) GetByID(userID uuid.UUID) (models.User, error) {
	var user models.User
	if err := r.DB.First(&user, userID).Error; err != nil {
		return models.User{}, err
	}
	return user, nil
}

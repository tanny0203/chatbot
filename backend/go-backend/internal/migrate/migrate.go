package main

import (
	"go-backend/config"
	"go-backend/internal/db"
	"go-backend/internal/models"

	"gorm.io/gorm"
)

// AutoMigrate runs the database migrations for all models
func AutoMigrate(db *gorm.DB) error {
	return db.AutoMigrate(
		&models.User{},
		&models.Chat{},
		&models.File{},
		&models.Message{},
	)
}

// DropTables drops all tables (use with caution - only for development)
func DropTables(db *gorm.DB) error {
	return db.Migrator().DropTable(
		&models.Message{},
		&models.File{},
		&models.Chat{},
		&models.User{},
	)
}

// AllModels returns a slice of all model structs for batch operations
func AllModels() []interface{} {
	return []interface{}{
		&models.User{},
		&models.Chat{},
		&models.File{},
		&models.Message{},
	}
}


func main() {
	config.LoadEnvVariables()
	db.ConnectToDB()
	AutoMigrate(db.DB)
}
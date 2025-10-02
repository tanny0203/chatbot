package db

import (
	"log"
	"os"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

var DB *gorm.DB
var FileStorageDB *gorm.DB

func ConnectToDB() {
	var err error
	DB_URL := os.Getenv("DB_URL")
	DB, err = gorm.Open(postgres.Open(DB_URL), &gorm.Config{})

	if (err != nil) {
		log.Fatal("failed to connect to database")
	}

	fileStorageDB_URL := os.Getenv("FILESTORAGEDB_URL")
	FileStorageDB, err = gorm.Open(postgres.Open(fileStorageDB_URL), &gorm.Config{})

	if (err != nil) {
		log.Fatal("failed to connect to database for file storage")
	}
}
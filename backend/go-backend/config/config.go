package config

import (
	"log"

	"github.com/joho/godotenv"
)

type Config struct {
	DBUrl         string
	ServerAddress string
}

func LoadEnvVariables() {
	err := godotenv.Load()

	if err != nil {
		log.Fatal("Error loading the .env files", err)

	}
}
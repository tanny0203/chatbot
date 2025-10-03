package main

import (
	// "go-backend/internal/api"
	"go-backend/config"
	"go-backend/internal/chat"
	"go-backend/internal/db"
	"go-backend/internal/users"

	"github.com/gin-gonic/gin"
)

func main() {
	config.LoadEnvVariables()
	db.ConnectToDB()

	r := gin.Default()

	// r.POST("/upload", func(c *gin.Context) {
	// 	file, err := c.FormFile("file")
	// 	if err != nil {
	// 		c.String(400, "Bad request: %s", err.Error())
	// 		return
	// 	}

	// 	fileContent, err := file.Open()

	// 	if err != nil {
	// 		c.String(500, "Failed to open file: %s", err.Error())
	// 		return
	// 	}
	// 	defer fileContent.Close()

	// 	// data, err := api.HandleFileUpload(file.Filename, fileContent, db.DB)
	// 	// if err != nil {
	// 	// 	c.String(500, "Failed to process file: %s", err.Error())
	// 	// 	return
	// 	// }
	// 	// c.JSON(200, data)
	// })

	users.RegisterRoutes(r, db.DB)
	chat.RegisterRoutes(r, db.DB, db.FileStorageDB)

	r.Run(":8080")
}
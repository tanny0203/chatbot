package main

import (
	"go-backend/internal/api"
	"go-backend/internal/db"

	"github.com/gin-gonic/gin"
)

func main() {
	db.InitDB()
	defer db.Db.Close()

	r := gin.Default()

	r.POST("/upload", func(c *gin.Context) {
		file, err := c.FormFile("file")
		if err != nil {
			c.String(400, "Bad request: %s", err.Error())
			return
		}

		fileContent, err := file.Open()

		if err != nil {
			c.String(500, "Failed to open file: %s", err.Error())
			return
		}
		defer fileContent.Close()

		data, err := api.HandleFileUpload(file.Filename, fileContent, db.Db)
		if err != nil {
			c.String(500, "Failed to process file: %s", err.Error())
			return
		}
		c.JSON(200, data)
	})

	r.Run(":8080")
}
package chat

import (
	"errors"
	"fmt"
	"go-backend/internal/file"
	"go-backend/internal/message"
	middleware "go-backend/internal/middlewares"
	"go-backend/internal/models"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

func RegisterRoutes(r *gin.Engine, db *gorm.DB, fileStorageDB *gorm.DB) {
	repo := NewRepo(db)
	service := NewService(repo)

	chats := r.Group("/chats")
	{
		chats.Use(middleware.RequireAuth())

		chats.POST("", func(c *gin.Context) {
			var dto struct {
				Title string `json:"title"`
			}
			if err := c.ShouldBindJSON(&dto); err != nil {
				c.JSON(400, gin.H{"error": err.Error()})
				return
			}
			user := c.MustGet("user").(models.User)
			chat, err := service.CreateChat(user.ID, dto.Title)
			if err != nil {
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}
			c.JSON(201, gin.H{
				"id":         chat.ID,
				"title":      chat.Title,
				"created_at": chat.CreatedAt,
			})
		})

		chats.GET("", func(c *gin.Context) {
			user := c.MustGet("user").(models.User)
			chats, err := service.GetChatsByUser(user.ID)
			if err != nil {
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}

			type DTO struct {
				ID        uuid.UUID `json:"id"`
				Title     string    `json:"title"`
				CreatedAt time.Time `json:"created_at"`
				}

			chatResponse := make([]DTO, 0, len(chats))

			for _, chat := range chats {	
				chatResponse = append(chatResponse, DTO{
					ID: chat.ID,
					Title: chat.Title,
					CreatedAt: chat.CreatedAt,
				})
			}
			c.JSON(200, chatResponse)

		})

		chats.GET("/:chat_id", func(c *gin.Context) {
			chatID := c.Param("chat_id")
			chatIDUUID, err := uuid.Parse(chatID)
			if err != nil {
				c.JSON(400, gin.H{"error": "invalid chat ID"})
				return
			}
			
			user := c.MustGet("user").(models.User)
			
			if err := AuthorizeChatAccess(user.ID, chatIDUUID, service); err != nil {
				if err.Error() == "forbidden" {
					c.JSON(403, gin.H{"error": "forbidden"})
					return
				}
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}
		
			chat, err := service.GetChatByID(chatIDUUID)
			if err != nil {
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}
		
			messages := make([]message.MessageResponseDTO, 0, len(chat.Messages))
			for _, m := range chat.Messages {
				messages = append(messages, message.MessageResponseDTO{
					ID:        m.ID,
					Role:      string(m.Role),
					Content:   m.Content,
					CreatedAt: m.CreatedAt,
				})
			}

			files := make([]file.FileResponseDTO, 0, len(chat.Files))
			for _, f := range chat.Files {
				files = append(files, file.FileResponseDTO{
					ID:        f.ID,
					Filename:  f.Filename,
					TableName: f.TableName,
				})
			}

			resp := chatResponseDTO{
				ID:        chat.ID,
				Title:     chat.Title,
				CreatedAt: chat.CreatedAt,
				UpdatedAt: chat.UpdatedAt,
				Messages:  messages,
				Files: files,
			}
			c.JSON(200, resp)
		})

		chats.GET("/:chat_id/messages", func(c *gin.Context) {

			user := c.MustGet("user").(models.User)
			chatID := c.Param("chat_id")
			chatIDUUID, err := uuid.Parse(chatID)
			if err != nil {
				c.JSON(400, gin.H{"error": "invalid chat ID"})
				return
			}
			if err := AuthorizeChatAccess(user.ID, chatIDUUID, service); err != nil {
				if err.Error() == "forbidden" {
					c.JSON(403, gin.H{"error": "forbidden"})
					return
				}
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}

			chat, err := service.GetChatByID(chatIDUUID)
			if err != nil {
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}
			
			messages := make([]message.MessageResponseDTO, 0, len(chat.Messages))
			for _, m := range chat.Messages {
				messages = append(messages, message.MessageResponseDTO{
					ID:        m.ID,
					Role:      string(m.Role),
					Content:   m.Content,
					CreatedAt: m.CreatedAt,
				})
			}
			c.JSON(200, messages)

		})

		chats.POST("/:chat_id/messages", func(c *gin.Context) {
			var dto struct {
				Content string `json:"content"`
			}
			if err := c.ShouldBindJSON(&dto); err != nil {
				c.JSON(400, gin.H{"error": err.Error()})
				return
			}
			user := c.MustGet("user").(models.User)
			chatID := c.Param("chat_id")
			chatIDUUID, err := uuid.Parse(chatID)
			if err != nil {
				c.JSON(400, gin.H{"error": "invalid chat ID"})
				return
			}
			if err := AuthorizeChatAccess(user.ID, chatIDUUID, service); err != nil {
				if err.Error() == "forbidden" {
					c.JSON(403, gin.H{"error": "forbidden"})
					return
				}
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}

			response, err := service.SendMessage(chatIDUUID, user.ID, dto.Content)
			if err != nil {
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}
			c.JSON(201, gin.H{
				"id":         response.ID,
				"role":       response.Role,
				"content":    response.Content,
				"created_at": response.CreatedAt,
			})
		})


		chats.GET("/:chat_id/files", func(c *gin.Context) {
			chatID := c.Param("chat_id")
			chatIDUUID, err := uuid.Parse(chatID)
			if err != nil {
				c.JSON(400, gin.H{"error": "invalid chat ID"})
				return
			}

			user := c.MustGet("user").(models.User)

		if err := AuthorizeChatAccess(user.ID, chatIDUUID, service); err != nil {
			if err.Error() == "forbidden" {
				c.JSON(403, gin.H{"error": "forbidden"})
				return
			}
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}

			

			chat, err := service.GetChatByID(chatIDUUID)
			if err != nil {
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}

			if chat.UserID != user.ID {
				c.JSON(403, gin.H{"error": "forbidden"})
				return
			}

			files := make([]file.FileResponseDTO, 0, len(chat.Files))
			for _, f := range chat.Files {
				files = append(files, file.FileResponseDTO{
					ID:        f.ID,
					Filename:  f.Filename,
					TableName: f.TableName,
				})
			}

			c.JSON(http.StatusOK, files)
		})

		chats.POST("/:chat_id/files", func(c *gin.Context) {
			chatID := c.Param("chat_id")
			chatIDUUID, err := uuid.Parse(chatID)
			if err != nil {
				c.JSON(400, gin.H{"error": "invalid chat ID"})
				return
			}

			user := c.MustGet("user").(models.User)

		if err := AuthorizeChatAccess(user.ID, chatIDUUID, service); err != nil {
			if err.Error() == "forbidden" {
				c.JSON(403, gin.H{"error": "forbidden"})
				return
			}
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}


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

			fileResponse, err := service.HandleFileUpload(chatIDUUID, user.ID, file.Filename, fileContent, fileStorageDB)

			if err != nil {
				c.String(http.StatusInternalServerError, err.Error())
			}

			c.JSON(http.StatusOK, fileResponse)
		})


	}
}


func AuthorizeChatAccess(userID, chatID uuid.UUID, service *Service) error {
    chat, err := service.GetChatByID(chatID)
    if err != nil {
        if errors.Is(err, gorm.ErrRecordNotFound) {
            return fmt.Errorf("forbidden") 
        }
        return err
    }
    if chat.UserID != userID {
        return fmt.Errorf("forbidden")
    }
    return nil
}

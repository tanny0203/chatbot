package chat

import (
	"go-backend/internal/message"
	middleware "go-backend/internal/middlewares"
	"go-backend/internal/models"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

func RegisterRoutes(r *gin.Engine, db *gorm.DB) {
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

		chats.GET("/:chat_id", func(ctx *gin.Context) {
			chatID := ctx.Param("chat_id")
			chatIDUUID, err := uuid.Parse(chatID)
			if err != nil {
				ctx.JSON(400, gin.H{"error": "invalid chat ID"})
				return
			}
			chat, err := service.GetChatByID(chatIDUUID)
			if err != nil {
				ctx.JSON(500, gin.H{"error": err.Error()})
				return
			}

			user := ctx.MustGet("user").(models.User)
			if chat.UserID != user.ID {
				ctx.JSON(403, gin.H{"error": "forbidden"})
				return
			
			}

			messages := make([]message.MessageDTO, 0, len(chat.Messages))
			for _, m := range chat.Messages {
				messages = append(messages, message.MessageDTO{
					ID:        m.ID,
					Role:      string(m.Role),
					Content:   m.Content,
					CreatedAt: m.CreatedAt,
				})
			}

			resp := chatDTO{
				ID:        chat.ID,
				Title:     chat.Title,
				CreatedAt: chat.CreatedAt,
				UpdatedAt: chat.UpdatedAt,
				Messages:  messages,
			}
			ctx.JSON(200, resp)
		})

		chats.POST("/:chat_id/message", func(ctx *gin.Context) {
			var dto struct {
				Content string `json:"content"`
			}
			if err := ctx.ShouldBindJSON(&dto); err != nil {
				ctx.JSON(400, gin.H{"error": err.Error()})
				return
			}
			user := ctx.MustGet("user").(models.User)
			chatID := ctx.Param("chat_id")
			chatIDUUID, err := uuid.Parse(chatID)
			if err != nil {
				ctx.JSON(400, gin.H{"error": "invalid chat ID"})
				return
			}
			response, err := service.SendMessage(chatIDUUID, user.ID, dto.Content)
			if err != nil {
				ctx.JSON(500, gin.H{"error": err.Error()})
				return
			}
			ctx.JSON(201, gin.H{
				"id":         response.ID,
				"role":       response.Role,
				"content":    response.Content,
				"created_at": response.CreatedAt,
			})
		})

		// chats.GET("/", func(c *gin.Context) {
		// 	user := c.MustGet("user").(models.User)
		// 	chats, err := service.GetChatsByUser(user.ID)
		// 	if err != nil {
		// 		c.JSON(500, gin.H{"error": err.Error()})
		// 		return
		// 	}
		// 	c.JSON(200, chats)
		// })
	}
}

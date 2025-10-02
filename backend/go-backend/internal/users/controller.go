package users

import (
	middleware "go-backend/internal/middlewares"
	"go-backend/internal/models"
	"go-backend/internal/utils"
	"net/http"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

func RegisterRoutes(r *gin.Engine, db *gorm.DB) {
	repo := NewRepo(db)
	service := NewService(repo)

	users := r.Group("/auth")
	{
		users.POST("/register", func(c *gin.Context) {
			var dto UserRegisterDTO
			if err := c.ShouldBindJSON(&dto); err != nil {
				c.JSON(400, gin.H{"error": err.Error()})
				return
			}
			if err := service.CreateUser(&dto); err != nil {
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}
			c.JSON(201, gin.H{"status": "user created"})
		})


		users.POST("/login", func(c *gin.Context) {
			var dto UserLoginDTO
			if err := c.ShouldBindJSON(&dto); err != nil {
				c.JSON(400, gin.H{"error": err.Error()})
				return
			}
			user, err := service.AuthenticateUser(&dto)
			if err != nil {
				c.JSON(401, gin.H{"error": "invalid credentials"})
				return
			}

			token, err := utils.GenerateAccessToken(user.ID)
			if err != nil {
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}

			c.SetSameSite(http.SameSiteLaxMode)
			c.SetCookie("Authorization", token, 7*24*60*60, "/", "localhost", false, true)
			c.JSON(http.StatusOK, gin.H{"status": "login successful"})
		})

		users.GET("/me",middleware.RequireAuth(), func(c *gin.Context) {
			user := c.MustGet("user").(models.User)

			c.JSON(200, gin.H{
				"id":    user.ID,
				"email": user.Email,
				"name":  user.Name,
			})
		})


		users.POST("/logout", func(c *gin.Context) {
			c.SetCookie("Authorization", "", -1, "/", "localhost", false, true)
			c.JSON(200, gin.H{"status": "logged out"})
		})

	}
}	
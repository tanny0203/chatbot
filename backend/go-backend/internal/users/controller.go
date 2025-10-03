package users

import (
	"errors"
	middleware "go-backend/internal/middlewares"
	"go-backend/internal/models"
	"go-backend/internal/utils"
	"net/http"
	"os"

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
				c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
				return
			}

			user, err := service.CreateUser(&dto)
			if err != nil {
				if errors.Is(err, gorm.ErrDuplicatedKey) {
					c.JSON(http.StatusConflict, gin.H{"error": "user already exists"})
					return
				}
				c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
				return
			}


			token, err := utils.GenerateAccessToken(user.ID)
			if err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
				return
			}
			domain := os.Getenv("COOKIE_DOMAIN")
			c.SetSameSite(http.SameSiteLaxMode)
			c.SetCookie("Authorization", token, 7*24*60*60, "/", domain, true, true)

			c.JSON(http.StatusCreated, gin.H{
				"status": "user created",
				"user": gin.H{
					"id":    user.ID,
					"name":  user.Name,
					"email": user.Email,
				},
				"token": token, 
			})
		})



		users.POST("/login", func(c *gin.Context) {
			var dto UserLoginDTO
			if err := c.ShouldBindJSON(&dto); err != nil {
				c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
				return
			}

			user, err := service.AuthenticateUser(&dto)
			if err != nil {
				c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid credentials"})
				return
			}

			token, err := utils.GenerateAccessToken(user.ID)
			if err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
				return
			}

	
			domain := os.Getenv("COOKIE_DOMAIN") 
			c.SetSameSite(http.SameSiteLaxMode)  
			c.SetCookie("Authorization", token, 7*24*60*60, "/", domain, true, true) 


	
			c.JSON(http.StatusOK, gin.H{
				"status": "login successful",
				"token":  token,
			})
		})


		users.GET("/me", middleware.RequireAuth(), func(c *gin.Context) {
			user, exists := c.Get("user")
			if !exists {
				c.AbortWithStatus(http.StatusUnauthorized)
				return
			}

			u := user.(models.User)

			c.JSON(http.StatusOK, gin.H{
				"id":    u.ID,
				"name":  u.Name,
				"email": u.Email,
			})
		})



		users.POST("/logout", func(c *gin.Context) {
			domain := os.Getenv("COOKIE_DOMAIN")
			c.SetSameSite(http.SameSiteLaxMode) // or NoneMode for cross-site
			c.SetCookie("Authorization", "", -1, "/", domain, true, true)
			
			c.JSON(http.StatusOK, gin.H{"status": "logged out"})
		})


	}
}	
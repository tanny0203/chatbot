package utils


import (
	"os"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)


func GenerateAccessToken(userID uuid.UUID) (string, error){

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
	"sub": userID,
	"exp": time.Now().Add(15 * time.Minute).Unix(),
	})

	return token.SignedString([]byte(os.Getenv("SECRET_KEY")))
}

func ParseToken(tokenString string) (uuid.UUID, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		return []byte(os.Getenv("SECRET_KEY")), nil
	}, jwt.WithValidMethods([]string{jwt.SigningMethodHS256.Alg()}))

	if err != nil {
		return uuid.Nil, err
	}

	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		// Check expiration
		if exp, ok := claims["exp"].(float64); ok {
			if float64(time.Now().Unix()) > exp {
				return uuid.Nil, jwt.ErrTokenExpired
			}
		} else {
			return uuid.Nil, jwt.ErrTokenInvalidClaims
		}

		// Extract user ID
		if subVal, ok := claims["sub"]; ok {
			switch v := subVal.(type) {
			case string:
				subUUID, err := uuid.Parse(v)
				if err != nil {
					return uuid.Nil, err
				}
				return subUUID, nil
			case uuid.UUID:
				return v, nil
			}
		}
	}

	return uuid.Nil, jwt.ErrTokenInvalidClaims
}

func GenerateUUID() (string, error) {
	uuid, err := uuid.NewRandom()
	if err != nil {
		return "", err
	}
	return uuid.String(), nil
}
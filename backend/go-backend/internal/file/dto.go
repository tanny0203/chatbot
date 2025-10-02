package file

import "github.com/google/uuid"

type FileResponseDTO struct {
	ID        uuid.UUID `json:"id"`
	Filename  string `json:"filename"`
	TableName string `json:"table_name"`
}
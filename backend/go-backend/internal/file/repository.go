package file

import (
	"fmt"
	"go-backend/internal/models"
	"regexp"
	"strconv"
	"strings"
	"time"

	"gorm.io/gorm"
)

type Repository struct {
	DB *gorm.DB
}

func NewRepo(db *gorm.DB) *Repository {
	return &Repository{DB: db}
}

func (r *Repository) CreateFile(file *models.File) error {
		if err := r.DB.Create(file).Error; err != nil {
		return  err
	}
	return nil
}

func (r *Repository) CreateTableForFileUpload(tableName string, headers []string, data [][]string, file *models.File) error {
	// Drop table if exists
	dropSQL := fmt.Sprintf(`DROP TABLE IF EXISTS "%s"`, tableName)
	if dbResult := r.DB.Exec(dropSQL); dbResult.Error != nil {
		return dbResult.Error
	}

	// Infer column types
	columnDefs := make([]string, len(headers))
	for i, header := range headers {
		colType := inferColumnType(data, i)
		columnDefs[i] = fmt.Sprintf(`"%s" %s`, header, colType)
	}

	// Create table
	createSQL := fmt.Sprintf(`CREATE TABLE "%s" (%s)`, tableName, strings.Join(columnDefs, ", "))

	if err := r.DB.Exec(createSQL).Error; err != nil {
		return err
	}

	// Insert data with batch optimization
	if len(data) > 0 {
		const batchSize = 1000 // Process 1000 rows per batch

		placeholders := make([]string, len(headers))
		for i := range placeholders {
			placeholders[i] = "?"
		}
		insertSQL := fmt.Sprintf(`INSERT INTO "%s" VALUES (%s)`, tableName, strings.Join(placeholders, ", "))

		// Process data in batches
		for batchStart := 0; batchStart < len(data); batchStart += batchSize {
			batchEnd := batchStart + batchSize
			if batchEnd > len(data) {
				batchEnd = len(data)
			}

			// Begin transaction for this batch using GORM's transaction API
			tx := r.DB.Begin()
			if tx.Error != nil {
				return tx.Error
			}

			// Use tx.Exec for each row in the batch
			for i := batchStart; i < batchEnd; i++ {
				row := data[i]
				values := make([]interface{}, len(headers))

				for j, val := range row {
					if j < len(values) {
						if val == "" {
							values[j] = nil
						} else {
							values[j] = val
						}
					}
				}

				// Pad with nil if row is shorter than headers
				for j := len(row); j < len(values); j++ {
					values[j] = nil
				}

				if err := tx.Exec(insertSQL, values...).Error; err != nil {
					tx.Rollback()
					return err
				}
			}

			// Commit the batch
			if err := tx.Commit().Error; err != nil {
				return err
			}
		}
	}

	return nil
}

func inferColumnType(data [][]string, columnIndex int) string {
	return inferColumnTypeAdvanced(data, columnIndex)
}

func inferColumnTypeAdvanced(data [][]string, columnIndex int) string {

	sqlType := "VARCHAR"

	if len(data) == 0 {
		return sqlType
	}

	var values []string
	const maxSampleSize = 1000

	// Sample data for type inference
	stepSize := 1
	if len(data) > maxSampleSize {
		stepSize = len(data) / maxSampleSize
	}

	for i := 0; i < len(data); i += stepSize {
		if len(values) >= maxSampleSize {
			break
		}

		if columnIndex >= len(data[i]) {
			continue
		}

		val := strings.TrimSpace(data[i][columnIndex])
		if val == "" {
			continue
		}

		values = append(values, val)
	}

	if len(values) == 0 {
		return sqlType
	}

	// Type inference
	allIntegers := true
	allFloats := true
	allDates := true
	allBooleans := true

	// Date patterns for validation
	datePatterns := []*regexp.Regexp{
		regexp.MustCompile(`^\d{4}-\d{2}-\d{2}$`),                   // YYYY-MM-DD
		regexp.MustCompile(`^\d{2}/\d{2}/\d{4}$`),                   // MM/DD/YYYY
		regexp.MustCompile(`^\d{2}-\d{2}-\d{4}$`),                   // MM-DD-YYYY
		regexp.MustCompile(`^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$`), // YYYY-MM-DD HH:MM:SS
		regexp.MustCompile(`^\d{2}/\d{2}/\d{2}$`),                   // MM/DD/YY
		regexp.MustCompile(`^\d{1,2}-\w{3}-\d{4}$`),                 // DD-MMM-YYYY
	}

	for _, val := range values {
		// Integer check
		if _, err := strconv.Atoi(val); err != nil {
			allIntegers = false
		}

		// Float check (only if not all integers)
		if !allIntegers {
			if _, err := strconv.ParseFloat(val, 64); err != nil {
				allFloats = false
			}
		}

		// Boolean check
		lower := strings.ToLower(strings.TrimSpace(val))
		booleanValues := map[string]bool{
			"true": true, "false": true, "1": true, "0": true,
			"yes": true, "no": true, "y": true, "n": true,
			"t": true, "f": true, "on": true, "off": true,
		}
		if !booleanValues[lower] {
			allBooleans = false
		}

		// Date check
		isDate := false
		for _, pattern := range datePatterns {
			if pattern.MatchString(val) {
				layouts := []string{"2006-01-02", "01/02/2006", "01-02-2006", "2006-01-02 15:04:05", "01/02/06", "2-Jan-2006"}
				for _, layout := range layouts {
					if _, err := time.Parse(layout, val); err == nil {
						isDate = true
						break
					}
				}
				if isDate {
					break
				}
			}
		}
		if !isDate {
			allDates = false
		}
	}

	// Determine SQL type
	if allBooleans {
		sqlType = "BOOLEAN"
	} else if allIntegers {
		sqlType = "INTEGER"
	} else if allFloats {
		sqlType = "DOUBLE"
	} else if allDates {
		sqlType = "DATE"
	}

	return sqlType
}

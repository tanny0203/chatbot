package main

import (
	"database/sql"
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"net/http"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	_ "github.com/marcboeker/go-duckdb"
	"github.com/tealeg/xlsx/v3"
)

type QueryRequest struct {
	SQL string `json:"sql" binding:"required"`
}

type UploadResponse struct {
	Message    string                   `json:"message"`
	Table      string                   `json:"table"`
	Metadata   string                   `json:"metadata"`
	SampleRows []map[string]interface{} `json:"sample_rows"`
}

type QueryResponse struct {
	Query  string                   `json:"query"`
	Result []map[string]interface{} `json:"result,omitempty"`
	Error  string                   `json:"error,omitempty"`
}

var db *sql.DB

func initDB() {
	var err error
	db, err = sql.Open("duckdb", "")
	if err != nil {
		log.Fatal("Failed to connect to DuckDB:", err)
	}

	if err = db.Ping(); err != nil {
		log.Fatal("Failed to ping DuckDB:", err)
	}

	log.Println("Connected to DuckDB successfully")
}

func main() {

	initDB()
	defer db.Close()

	r := gin.Default()

	r.POST("/upload", uploadFile)
	r.POST("/query", runQuery)

	r.Run(":8000")
}

func uploadFile(c *gin.Context) {
	log.Printf("Upload request started")

	file, header, err := c.Request.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "No file uploaded"})
		return
	}
	defer file.Close()

	filename := header.Filename
	ext := strings.ToLower(filepath.Ext(filename))
	log.Printf("Processing file: %s", filename)

	var data [][]string
	var headers []string

	switch ext {
	case ".csv":
		log.Printf("Reading CSV file")
		data, headers, err = readCSV(file)
	case ".xlsx":
		log.Printf("Reading XLSX file")
		data, headers, err = readXLSX(file)
	default:
		c.JSON(http.StatusBadRequest, gin.H{"error": "Unsupported file type"})
		return
	}

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to read file: %v", err)})
		return
	}

	log.Printf("File read successfully: %d rows, %d columns", len(data), len(headers))
	tableName := strings.TrimSuffix(filename, ext)

	err = createTable(tableName, headers, data)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to create table: %v", err)})
		return
	}

	log.Printf("Table %s created successfully with %d rows", tableName, len(data))

	metadata := generateMetadata(tableName, headers, data)
	sampleRows := generateSampleRows(headers, data)

	log.Printf("Generated metadata and sample rows for table %s", tableName)

	response := UploadResponse{
		Message:    fmt.Sprintf("Uploaded %s successfully", filename),
		Table:      tableName,
		Metadata:   metadata,
		SampleRows: sampleRows,
	}

	c.JSON(http.StatusOK, response)
}

func runQuery(c *gin.Context) {
	var req QueryRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	rows, err := db.Query(req.SQL)
	if err != nil {
		c.JSON(http.StatusOK, QueryResponse{
			Query: req.SQL,
			Error: err.Error(),
		})
		return
	}
	defer rows.Close()

	columns, err := rows.Columns()
	if err != nil {
		c.JSON(http.StatusOK, QueryResponse{
			Query: req.SQL,
			Error: err.Error(),
		})
		return
	}

	var result []map[string]interface{}
	for rows.Next() {
		values := make([]interface{}, len(columns))
		valuePtrs := make([]interface{}, len(columns))
		for i := range columns {
			valuePtrs[i] = &values[i]
		}

		if err := rows.Scan(valuePtrs...); err != nil {
			c.JSON(http.StatusOK, QueryResponse{
				Query: req.SQL,
				Error: err.Error(),
			})
			return
		}

		row := make(map[string]interface{})
		for i, col := range columns {
			val := values[i]
			if val != nil {
				// Handle different types properly
				switch v := val.(type) {
				case []byte:
					row[col] = string(v)
				default:
					row[col] = v
				}
			} else {
				row[col] = nil
			}
		}
		result = append(result, row)
	}

	c.JSON(http.StatusOK, QueryResponse{
		Query:  req.SQL,
		Result: result,
	})
}

func readCSV(file io.Reader) ([][]string, []string, error) {
	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil {
		return nil, nil, err
	}

	if len(records) == 0 {
		return nil, nil, fmt.Errorf("empty CSV file")
	}

	headers := records[0]
	data := records[1:]

	return data, headers, nil
}

func readXLSX(file io.Reader) ([][]string, []string, error) {
	// Read the entire file into memory
	content, err := io.ReadAll(file)
	if err != nil {
		return nil, nil, err
	}

	wb, err := xlsx.OpenBinary(content)
	if err != nil {
		return nil, nil, err
	}

	if len(wb.Sheets) == 0 {
		return nil, nil, fmt.Errorf("no sheets found in Excel file")
	}

	sheet := wb.Sheets[0]
	var data [][]string
	var headers []string

	rowIndex := 0
	err = sheet.ForEachRow(func(row *xlsx.Row) error {
		var rowData []string
		row.ForEachCell(func(cell *xlsx.Cell) error {
			text := cell.String()
			rowData = append(rowData, text)
			return nil
		})

		if rowIndex == 0 {
			headers = rowData
		} else {
			data = append(data, rowData)
		}
		rowIndex++
		return nil
	})

	if err != nil {
		return nil, nil, err
	}

	return data, headers, nil
}

func createTable(tableName string, headers []string, data [][]string) error {
	// Drop table if exists
	dropSQL := fmt.Sprintf(`DROP TABLE IF EXISTS "%s"`, tableName)
	_, err := db.Exec(dropSQL)
	if err != nil {
		return err
	}

	// Infer column types
	columnDefs := make([]string, len(headers))
	for i, header := range headers {
		colType := inferColumnType(data, i)
		columnDefs[i] = fmt.Sprintf(`"%s" %s`, header, colType)
	}

	// Create table
	createSQL := fmt.Sprintf(`CREATE TABLE "%s" (%s)`, tableName, strings.Join(columnDefs, ", "))
	_, err = db.Exec(createSQL)
	if err != nil {
		return err
	}

	// Insert data
	if len(data) > 0 {
		placeholders := make([]string, len(headers))
		for i := range placeholders {
			placeholders[i] = "?"
		}

		insertSQL := fmt.Sprintf(`INSERT INTO "%s" VALUES (%s)`, tableName, strings.Join(placeholders, ", "))
		stmt, err := db.Prepare(insertSQL)
		if err != nil {
			return err
		}
		defer stmt.Close()

		for _, row := range data {
			values := make([]interface{}, len(headers))
			for i, val := range row {
				if i < len(values) {
					if val == "" {
						values[i] = nil
					} else {
						values[i] = val
					}
				}
			}
			// Pad with nil if row is shorter than headers
			for i := len(row); i < len(values); i++ {
				values[i] = nil
			}

			_, err = stmt.Exec(values...)
			if err != nil {
				return err
			}
		}
	}

	return nil
}

func inferColumnType(data [][]string, columnIndex int) string {
	if len(data) == 0 {
		return "TEXT"
	}

	// Sample a few rows to infer type
	sampleSize := 10
	if len(data) < sampleSize {
		sampleSize = len(data)
	}

	hasNumbers := false
	hasDecimals := false

	for i := 0; i < sampleSize; i++ {
		if columnIndex >= len(data[i]) {
			continue
		}

		val := strings.TrimSpace(data[i][columnIndex])
		if val == "" {
			continue
		}

		// Try to parse as number
		if _, err := strconv.Atoi(val); err == nil {
			hasNumbers = true
		} else if _, err := strconv.ParseFloat(val, 64); err == nil {
			hasNumbers = true
			hasDecimals = true
		}
	}

	if hasNumbers {
		if hasDecimals {
			return "DOUBLE"
		}
		return "INTEGER"
	}

	return "TEXT"
}

func generateMetadata(tableName string, headers []string, data [][]string) string {
	metadata := fmt.Sprintf("Table %s\n", tableName)
	metadata += "Columns:\n"

	for i, header := range headers {
		colType := inferColumnType(data, i)
		metadata += fmt.Sprintf(" - %s: %s\n", header, colType)
	}

	metadata += fmt.Sprintf("Row count: %d\n", len(data))
	return metadata
}

func generateSampleRows(headers []string, data [][]string) []map[string]interface{} {
	var sampleRows []map[string]interface{}

	sampleSize := 5
	if len(data) < sampleSize {
		sampleSize = len(data)
	}

	// Pre-allocate slice capacity
	sampleRows = make([]map[string]interface{}, 0, sampleSize)

	for i := 0; i < sampleSize; i++ {
		row := make(map[string]interface{}, len(headers))
		rowData := data[i]

		for j, header := range headers {
			if j < len(rowData) && rowData[j] != "" {
				row[header] = rowData[j]
			} else {
				row[header] = nil
			}
		}
		sampleRows = append(sampleRows, row)
	}

	return sampleRows
}

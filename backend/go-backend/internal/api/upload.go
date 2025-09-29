package api

import (
	"database/sql"
	"encoding/csv"
	"fmt"
	"io"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"

	_ "github.com/marcboeker/go-duckdb"
	"github.com/tealeg/xlsx/v3"
)

func HandleFileUpload(filename string, file io.Reader, db *sql.DB) (map[string]interface{}, error) {
	var data [][]string
	var headers []string
	var err error

	if strings.HasSuffix(strings.ToLower(filename), ".csv") {
		data, headers, err = readCSV(file)
	} else if strings.HasSuffix(strings.ToLower(filename), ".xlsx") {
		data, headers, err = readXLSX(file)
	} else {
		return nil, fmt.Errorf("unsupported file type")
	}

	if err != nil {
		return nil, err
	}

	tableName := strings.TrimSuffix(filename, filepath.Ext(filename))

	// Create table in database
	if err := createTable(tableName, headers, data, db); err != nil {
		return nil, err
	}

	// Generate detailed metadata for NL2SQL
	metadata := generateTableMetadata(tableName, headers, data)

	return metadata, nil
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

// ValueCount represents frequency of values for categorical analysis
type ValueCount struct {
	Value string `json:"value"`
	Count int    `json:"count"`
}

// ColumnMetadata holds comprehensive information about a column for NL2SQL
type ColumnMetadata struct {
	Name            string            `json:"name"`
	DataType        string            `json:"data_type"` // "INTEGER","FLOAT","TEXT","BOOLEAN","DATE"
	SqlType         string            `json:"sql_type"`  // "INTEGER","DOUBLE","VARCHAR","BOOLEAN","DATE"
	Nullable        bool              `json:"nullable"`
	IsCategory      bool              `json:"is_category"`
	IsBoolean       bool              `json:"is_boolean"`
	IsDate          bool              `json:"is_date"`
	UniqueCount     int               `json:"unique_count"`
	NullCount       int               `json:"null_count"`
	SampleValues    []string          `json:"sample_values"`    // up to 5 examples
	TopValues       []ValueCount      `json:"top_values"`       // top 10 frequent values
	EnumValues      []string          `json:"enum_values"`      // all categorical values
	Min             *float64          `json:"min,omitempty"`    // for numeric columns
	Max             *float64          `json:"max,omitempty"`    // for numeric columns
	Mean            *float64          `json:"mean,omitempty"`   // for numeric columns
	Median          *float64          `json:"median,omitempty"` // for numeric columns
	Std             *float64          `json:"std,omitempty"`    // for numeric columns
	Description     string            `json:"description"`
	ValueMappings   map[string]string `json:"value_mappings,omitempty"`   // code -> human readable
	SynonymMappings map[string]string `json:"synonym_mappings,omitempty"` // query synonyms
	ExampleQueries  []string          `json:"example_queries,omitempty"`  // dataset-specific examples
}

// Enhanced type inference for NL2SQL with production-ready features
func inferColumnTypeAdvanced(data [][]string, columnIndex int, columnName string) ColumnMetadata {
	metadata := ColumnMetadata{
		Name:            columnName,
		DataType:        "TEXT",
		SqlType:         "VARCHAR",
		SampleValues:    make([]string, 0),
		ValueMappings:   make(map[string]string),
		SynonymMappings: make(map[string]string),
		ExampleQueries:  make([]string, 0),
	}

	if len(data) == 0 {
		return metadata
	}

	// Full scan for accurate statistics (critical for production)
	var values []string
	var numericValues []float64
	valueCounts := make(map[string]int)
	nullCount := 0
	totalRows := len(data)

	// Date patterns - extended for better coverage
	datePatterns := []*regexp.Regexp{
		regexp.MustCompile(`^\d{4}-\d{2}-\d{2}$`),                   // YYYY-MM-DD
		regexp.MustCompile(`^\d{2}/\d{2}/\d{4}$`),                   // MM/DD/YYYY
		regexp.MustCompile(`^\d{2}-\d{2}-\d{4}$`),                   // MM-DD-YYYY
		regexp.MustCompile(`^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$`), // YYYY-MM-DD HH:MM:SS
		regexp.MustCompile(`^\d{2}/\d{2}/\d{2}$`),                   // MM/DD/YY
		regexp.MustCompile(`^\d{1,2}-\w{3}-\d{4}$`),                 // DD-MMM-YYYY
	}


	const maxSampleSize = 1000 


	stepSize := 1
	if totalRows > maxSampleSize {
		stepSize = totalRows / maxSampleSize
	}

	for i := 0; i < totalRows; i += stepSize {
		if len(values) >= maxSampleSize {
			break
		}

		if columnIndex >= len(data[i]) {
			nullCount++
			continue
		}

		val := strings.TrimSpace(data[i][columnIndex])
		if val == "" {
			nullCount++
			continue
		}

		values = append(values, val)
		valueCounts[val]++

		// Keep first 5 for samples
		if len(metadata.SampleValues) < 5 {
			metadata.SampleValues = append(metadata.SampleValues, val)
		}
	}

	// Count nulls in remaining data (fast scan)
	if totalRows > maxSampleSize {
		for i := 0; i < totalRows; i++ {
			if columnIndex >= len(data[i]) || strings.TrimSpace(data[i][columnIndex]) == "" {
				nullCount++
			}
		}
	}

	metadata.UniqueCount = len(valueCounts)
	metadata.NullCount = nullCount
	metadata.Nullable = nullCount > 0

	if len(values) == 0 {
		return metadata
	}

	// Type inference with enhanced logic
	allIntegers := true
	allFloats := true
	allDates := true
	allBooleans := true

	for _, val := range values {
		// Integer check
		if intVal, err := strconv.Atoi(val); err != nil {
			allIntegers = false
		} else {
			numericValues = append(numericValues, float64(intVal))
		}

		// Float check
		if floatVal, err := strconv.ParseFloat(val, 64); err != nil {
			allFloats = false
		} else if !allIntegers {
			numericValues = append(numericValues, floatVal)
		}

		// Enhanced boolean detection
		lower := strings.ToLower(strings.TrimSpace(val))
		booleanValues := map[string]bool{
			"true": true, "false": true, "1": true, "0": true,
			"yes": true, "no": true, "y": true, "n": true,
			"t": true, "f": true, "on": true, "off": true,
		}
		if !booleanValues[lower] {
			allBooleans = false
		}

		// Date check with multiple formats
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

	// Calculate statistics for numeric columns
	if len(numericValues) > 0 {
		metadata.Min = &numericValues[0]
		metadata.Max = &numericValues[0]
		sum := 0.0

		for _, val := range numericValues {
			if val < *metadata.Min {
				*metadata.Min = val
			}
			if val > *metadata.Max {
				*metadata.Max = val
			}
			sum += val
		}

		mean := sum / float64(len(numericValues))
		metadata.Mean = &mean

		// Calculate standard deviation
		variance := 0.0
		for _, val := range numericValues {
			variance += (val - mean) * (val - mean)
		}
		std := variance / float64(len(numericValues))
		metadata.Std = &std
	}

	// Generate TopValues (sorted by frequency)
	type kv struct {
		Key   string
		Value int
	}
	var sortedValues []kv
	for k, v := range valueCounts {
		sortedValues = append(sortedValues, kv{k, v})
	}
	// Sort by count descending
	for i := 0; i < len(sortedValues)-1; i++ {
		for j := i + 1; j < len(sortedValues); j++ {
			if sortedValues[i].Value < sortedValues[j].Value {
				sortedValues[i], sortedValues[j] = sortedValues[j], sortedValues[i]
			}
		}
	}

	// Take top 10 values
	maxTop := 10
	if len(sortedValues) < maxTop {
		maxTop = len(sortedValues)
	}
	metadata.TopValues = make([]ValueCount, maxTop)
	for i := 0; i < maxTop; i++ {
		metadata.TopValues[i] = ValueCount{
			Value: sortedValues[i].Key,
			Count: sortedValues[i].Value,
		}
	}

	// Enhanced type determination with value mappings
	uniqueRatio := float64(metadata.UniqueCount) / float64(len(values))

	if allBooleans && metadata.UniqueCount <= 10 {
		metadata.DataType = "BOOLEAN"
		metadata.SqlType = "BOOLEAN"
		metadata.IsBoolean = true
		metadata.Description = "Boolean values"

		// Create boolean mappings
		for _, val := range values {
			lower := strings.ToLower(strings.TrimSpace(val))
			switch lower {
			case "yes", "y", "true", "1", "t", "on":
				metadata.ValueMappings[val] = "TRUE"
			case "no", "n", "false", "0", "f", "off":
				metadata.ValueMappings[val] = "FALSE"
			}
		}

		// Add generic synonyms for NL queries
		metadata.SynonymMappings["true"] = fmt.Sprintf("%s = TRUE", columnName)
		metadata.SynonymMappings["false"] = fmt.Sprintf("%s = FALSE", columnName)
		metadata.SynonymMappings["yes"] = fmt.Sprintf("%s = TRUE", columnName)
		metadata.SynonymMappings["no"] = fmt.Sprintf("%s = FALSE", columnName)

	} else if allIntegers {
		metadata.DataType = "INTEGER"
		metadata.SqlType = "INTEGER"
		metadata.Description = "Whole numbers"

	} else if allFloats {
		metadata.DataType = "FLOAT"
		metadata.SqlType = "DOUBLE"
		metadata.Description = "Decimal numbers"

	} else if allDates {
		metadata.DataType = "DATE"
		metadata.SqlType = "DATE"
		metadata.IsDate = true
		metadata.Description = "Date values"

	} else if (uniqueRatio < 0.2 && metadata.UniqueCount <= 50) || metadata.UniqueCount <= 20 {
		// Categorical detection with enhanced mapping
		metadata.IsCategory = true
		metadata.DataType = "TEXT"
		metadata.SqlType = "VARCHAR"
		metadata.Description = fmt.Sprintf("Categorical data with %d categories", metadata.UniqueCount)

		// Create enum values
		metadata.EnumValues = make([]string, len(sortedValues))
		for i, kv := range sortedValues {
			metadata.EnumValues[i] = kv.Key
		}

		// Generic pattern detection for common abbreviations
		for _, val := range metadata.EnumValues {
			val = strings.TrimSpace(val)
			// Only add generic mappings that are commonly understood
			if len(val) <= 3 { // Very short codes might need explanation
				switch strings.ToUpper(val) {
				case "M":
					metadata.ValueMappings[val] = "M (possibly male, medium, or other)"
				case "F":
					metadata.ValueMappings[val] = "F (possibly female, false, or other)"
				case "Y":
					metadata.ValueMappings[val] = "Y (possibly yes or year)"
				case "N":
					metadata.ValueMappings[val] = "N (possibly no or number)"
				}
			}
		}

	} else {
		metadata.Description = "Text data"
	}

	// Generate example queries for this column
	metadata.ExampleQueries = generateColumnExamples(columnName, metadata)

	return metadata
}

// Generate dataset-specific example queries for better NL2SQL accuracy
func generateColumnExamples(columnName string, metadata ColumnMetadata) []string {
	examples := make([]string, 0)

	if metadata.IsBoolean {
		examples = append(examples,
			fmt.Sprintf("How many records have %s as true?", columnName),
			fmt.Sprintf("Show me all data where %s is false", columnName))
	} else if metadata.IsCategory && len(metadata.TopValues) > 0 {
		topValue := metadata.TopValues[0].Value
		examples = append(examples,
			fmt.Sprintf("How many records have %s equal to '%s'?", columnName, topValue),
			fmt.Sprintf("Show distribution of %s", columnName))
	} else if metadata.DataType == "INTEGER" || metadata.DataType == "FLOAT" {
		if metadata.Min != nil && metadata.Max != nil {
			examples = append(examples,
				fmt.Sprintf("What is the average %s?", columnName),
				fmt.Sprintf("Show records where %s is greater than %.1f", columnName, (*metadata.Min+*metadata.Max)/2))
		}
	} else if metadata.IsDate {
		examples = append(examples,
			fmt.Sprintf("Show records from the latest %s", columnName),
			fmt.Sprintf("Group by %s and count", columnName))
	}

	return examples
}

// Simple inference for table creation (backward compatibility)
func inferColumnType(data [][]string, columnIndex int) string {
	metadata := inferColumnTypeAdvanced(data, columnIndex, "")
	return metadata.SqlType
}

func createTable(tableName string, headers []string, data [][]string, db *sql.DB) error {
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

			// Begin transaction for this batch
			tx, err := db.Begin()
			if err != nil {
				return err
			}

			stmt, err := tx.Prepare(insertSQL)
			if err != nil {
				tx.Rollback()
				return err
			}

			// Insert batch of rows
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

				_, err = stmt.Exec(values...)
				if err != nil {
					stmt.Close()
					tx.Rollback()
					return err
				}
			}

			stmt.Close()

			// Commit the batch
			if err = tx.Commit(); err != nil {
				return err
			}
		}
	}

	return nil
}

// Generate comprehensive metadata for NL2SQL model
func generateTableMetadata(tableName string, headers []string, data [][]string) map[string]interface{} {
	columns := make([]ColumnMetadata, len(headers))

	// Concurrent type inference for better performance
	var wg sync.WaitGroup
	for i, header := range headers {
		wg.Add(1)
		go func(idx int, colName string) {
			defer wg.Done()
			columns[idx] = inferColumnTypeAdvanced(data, idx, colName)
		}(i, header)
	}
	wg.Wait()

	// Generate table-level example queries
	tableExamples := generateTableExamples(tableName, columns, data)

	metadata := map[string]interface{}{
		"table_name":       tableName,
		"total_rows":       len(data),
		"total_columns":    len(headers),
		"columns":          columns,
		"schema_summary":   generateSchemaSummary(columns),
		"example_queries":  tableExamples,
		"generated_at":     time.Now().Unix(),
		"metadata_version": "2.0", // For schema versioning
		"query_hints":      generateQueryHints(columns),
	}

	return metadata
}

// Generate table-level example queries for the NL2SQL model
func generateTableExamples(tableName string, columns []ColumnMetadata, data [][]string) []string {
	examples := make([]string, 0)

	// Basic count
	examples = append(examples, fmt.Sprintf("SELECT COUNT(*) FROM %s", tableName))

	// Find categorical columns for filtering examples
	var categoricalCols []ColumnMetadata
	var numericCols []ColumnMetadata
	var booleanCols []ColumnMetadata

	for _, col := range columns {
		if col.IsCategory {
			categoricalCols = append(categoricalCols, col)
		} else if col.DataType == "INTEGER" || col.DataType == "FLOAT" {
			numericCols = append(numericCols, col)
		} else if col.IsBoolean {
			booleanCols = append(booleanCols, col)
		}
	}

	// Categorical filtering examples
	if len(categoricalCols) > 0 && len(categoricalCols[0].TopValues) > 0 {
		col := categoricalCols[0]
		topValue := col.TopValues[0].Value
		examples = append(examples,
			fmt.Sprintf("SELECT * FROM %s WHERE %s = '%s'", tableName, col.Name, topValue),
			fmt.Sprintf("SELECT %s, COUNT(*) FROM %s GROUP BY %s", col.Name, tableName, col.Name))
	}

	// Numeric aggregation examples
	if len(numericCols) > 0 {
		col := numericCols[0]
		examples = append(examples,
			fmt.Sprintf("SELECT AVG(%s) FROM %s", col.Name, tableName),
			fmt.Sprintf("SELECT MAX(%s), MIN(%s) FROM %s", col.Name, col.Name, tableName))

		if col.Min != nil && col.Max != nil {
			midpoint := (*col.Min + *col.Max) / 2
			examples = append(examples,
				fmt.Sprintf("SELECT * FROM %s WHERE %s > %.1f", tableName, col.Name, midpoint))
		}
	}

	// Boolean filtering examples
	if len(booleanCols) > 0 {
		col := booleanCols[0]
		examples = append(examples,
			fmt.Sprintf("SELECT COUNT(*) FROM %s WHERE %s = TRUE", tableName, col.Name),
			fmt.Sprintf("SELECT COUNT(*) FROM %s WHERE %s = FALSE", tableName, col.Name))
	}

	// Multi-column examples
	if len(categoricalCols) > 0 && len(numericCols) > 0 {
		catCol := categoricalCols[0]
		numCol := numericCols[0]
		if len(catCol.TopValues) > 0 {
			topValue := catCol.TopValues[0].Value
			examples = append(examples,
				fmt.Sprintf("SELECT AVG(%s) FROM %s WHERE %s = '%s'", numCol.Name, tableName, catCol.Name, topValue))
		}
	}

	return examples
}

// Generate query hints for the NL2SQL model
func generateQueryHints(columns []ColumnMetadata) map[string]string {
	hints := make(map[string]string)

	for _, col := range columns {
		if col.IsBoolean {
			hints[col.Name] = "Use TRUE/FALSE for boolean queries"
		} else if col.IsCategory && len(col.ValueMappings) > 0 {
			hints[col.Name] = "Has value mappings - check value_mappings field"
		} else if col.DataType == "INTEGER" || col.DataType == "FLOAT" {
			if col.Min != nil && col.Max != nil {
				hints[col.Name] = fmt.Sprintf("Numeric range: %.1f to %.1f", *col.Min, *col.Max)
			}
		}
	}

	return hints
}

func generateSchemaSummary(columns []ColumnMetadata) string {
	var summary strings.Builder
	summary.WriteString(fmt.Sprintf("Table has %d columns:\n", len(columns)))

	for _, col := range columns {
		summary.WriteString(fmt.Sprintf("- %s (%s): %s", col.Name, col.DataType, col.Description))
		if col.IsCategory {
			summary.WriteString(fmt.Sprintf(" [Categories: %v]", col.SampleValues))
		}
		summary.WriteString("\n")
	}

	return summary.String()
}

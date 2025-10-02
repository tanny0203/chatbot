package utils

import (
	"encoding/csv"
	"fmt"
	"io"
)


func ReadCSV(file io.Reader) ([][]string, []string, error) {
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
package utils

import (
	"fmt"
	"io"

	"github.com/tealeg/xlsx/v3"
)

func ReadXLSX(file io.Reader) ([][]string, []string, error) {
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
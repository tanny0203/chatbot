package models


type ValueCount struct {
	Value string `json:"value"`
	Count int    `json:"count"`
}


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
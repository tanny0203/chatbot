package db

import (
	"database/sql"
	"log"

	_ "github.com/marcboeker/go-duckdb"
)

var Db *sql.DB

func InitDB() {
	var err error
	Db, err = sql.Open("duckdb", "")
	if err != nil {
		log.Fatal("Failed to connect to DuckDB:", err)
	}

	if err = Db.Ping(); err != nil {
		log.Fatal("Failed to ping DuckDB:", err)
	}

	log.Println("Connected to DuckDB successfully")
}

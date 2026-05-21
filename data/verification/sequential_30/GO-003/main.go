package main

import (
    "fmt"
    "net/http"
)

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("GET /posts/{id}", func(w http.ResponseWriter, r *http.Request) {})
    req, _ := http.NewRequest("GET", "/posts/123", nil)
    match, pattern := mux.Handler(req)
    fmt.Printf("pattern=%q handler=%T\n", pattern, match)
}

package main

import (
    "encoding/json"
    "fmt"
)

type Payload struct {
    Count int `json:"count,omitzero"`
}

func main() {
    b, err := json.Marshal(Payload{})
    if err != nil { panic(err) }
    fmt.Println(string(b))
}

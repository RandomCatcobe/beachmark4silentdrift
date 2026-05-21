package main

import (
	"encoding/json"
	"fmt"
	"time"
)

func main() {
	timer := time.NewTimer(time.Hour)
	defer timer.Stop()

	result := map[string]int{
		"cap": cap(timer.C),
		"len": len(timer.C),
	}
	encoded, err := json.Marshal(result)
	if err != nil {
		panic(err)
	}
	fmt.Println(string(encoded))
}
